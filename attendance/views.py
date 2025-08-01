# attendance/views.py

from datetime import timedelta, date, datetime
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .pdf_report import build_roster_pdf, build_weekly_roster_pdf, build_daily_plan_grouped_pdf
from django_filters.rest_framework import DjangoFilterBackend
from collections import defaultdict
from .models import ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftLocation, DailyPlan, DailyPlanEntry
from .serializers import (ClockLogSerializer, RosterPeriodSerializer, StaffRosterSerializer,
    ShiftLocationSerializer, DailyPlanEntrySerializer, DailyPlanSerializer,
    CopyShiftSerializer,
    CopyDaySerializer,
    CopyDayAllSerializer,
    CopyWeekSerializer,)
from hotel.models import Hotel

# attendance/filters.py
import django_filters
from .filters import StaffRosterFilter

# ---------------------- helpers ----------------------
def euclidean(a, b):
    """Compute Euclidean distance between two equal‑length lists of floats."""
    import math
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------- Clock / Face ----------------------
class ClockLogViewSet(viewsets.ModelViewSet):
    queryset = ClockLog.objects.select_related('staff', 'hotel').all()
    serializer_class = ClockLogSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path=r'register-face/(?P<hotel_slug>[^/.]+)')
    def register_face(self, request, hotel_slug=None):
        descriptor = request.data.get("descriptor")
        if not isinstance(descriptor, list) or len(descriptor) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff = getattr(request.user, "staff_profile", None)
        if not staff:
            return Response({"error": "User has no linked staff profile."},
                            status=status.HTTP_400_BAD_REQUEST)

        StaffFace.objects.filter(staff=staff).delete()
        StaffFace.objects.create(hotel=hotel, staff=staff, encoding=descriptor)
        staff.has_registered_face = True
        staff.save(update_fields=["has_registered_face"])

        return Response({"message": "Face descriptor registered."})

    @action(detail=False, methods=['post'], url_path=r'face-clock-in/(?P<hotel_slug>[^/.]+)')
    def face_clock_in(self, request, hotel_slug=None):
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff_faces = StaffFace.objects.select_related('staff') \
                                       .filter(hotel=hotel, staff__is_active=True)

        best_id, best_dist = None, float('inf')
        for face_entry in staff_faces:
            dist = euclidean(probe, face_entry.encoding)
            if dist < best_dist:
                best_dist, best_id = dist, face_entry.staff.id

        if best_dist <= 0.6:
            staff = get_object_or_404(staff_faces.model.staff.field.related_model, id=best_id)
            today = now().date()
            existing_log = ClockLog.objects.filter(
                hotel=hotel, staff=staff,
                time_in__date=today, time_out__isnull=True
            ).first()

            if existing_log:
                existing_log.time_out = now()
                existing_log.save()
                action_message = "Clock‑out"
                log = existing_log
                staff.is_on_duty = False
            else:
                log = ClockLog.objects.create(
                    hotel=hotel,
                    staff=staff,
                    verified_by_face=True
                )
                action_message = "Clock‑in"
                staff.is_on_duty = True

            staff.save(update_fields=["is_on_duty"])

            return Response({
                "message": f"{action_message} successful for {staff.first_name}",
                "log": ClockLogSerializer(log).data
            })

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["get"], url_path="status")
    def current_status(self, request):
        staff = getattr(request.user, "staff_profile", None)
        hotel_slug = request.query_params.get("hotel_slug")
        if not staff or not hotel_slug:
            return Response({"error": "Missing staff or hotel."}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        latest_log = ClockLog.objects.filter(hotel=hotel, staff=staff) \
                                     .order_by("-time_in").first()

        if not latest_log:
            return Response({"status": "not_clocked_in"})
        if latest_log.time_out:
            return Response({"status": "clocked_out", "last_log": latest_log.time_out})
        return Response({"status": "clocked_in", "since": latest_log.time_in})

    @action(detail=False, methods=['post'], url_path=r'detect/(?P<hotel_slug>[^/.]+)')
    def detect_face_only(self, request, hotel_slug=None):
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response({"error": "A 128‑length descriptor array is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff_faces = StaffFace.objects.select_related('staff') \
                                       .filter(hotel=hotel, staff__is_active=True)

        best_id, best_dist = None, float('inf')
        for face_entry in staff_faces:
            dist = euclidean(probe, face_entry.encoding)
            if dist < best_dist:
                best_dist, best_id = dist, face_entry.staff.id

        if best_dist <= 0.6:
            staff = get_object_or_404(staff_faces.model.staff.field.related_model, id=best_id)
            is_clocked_in = ClockLog.objects.filter(
                hotel=hotel, staff=staff,
                time_in__date=now().date(), time_out__isnull=True
            ).exists()
            return Response({
                "staff_id": staff.id,
                "staff_name": f"{staff.first_name} {staff.last_name}",
                "clocked_in": is_clocked_in
            })

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)


# ---------------------- Roster Period ----------------------
class RosterPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = RosterPeriodSerializer
    permission_classes = [IsAuthenticated]
   
    
    def get_hotel(self):
        return get_object_or_404(Hotel, slug=self.kwargs.get("hotel_slug"))

    def get_queryset(self):
        hotel = self.get_hotel()
        return RosterPeriod.objects.select_related('hotel', 'created_by').filter(hotel=hotel)

    def perform_create(self, serializer):
        hotel = self.get_hotel()
        staff = getattr(self.request.user, "staff_profile", None)
        serializer.save(hotel=hotel, created_by=staff)

    @action(detail=True, methods=['post'], url_path='add-shift')
    def add_shift(self, request, pk=None):
        period = self.get_object()
        serializer = StaffRosterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(period=period, hotel=period.hotel)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='create-department-roster')
    def create_department_roster(self, request, pk=None):
        period = self.get_object()
        hotel = period.hotel
        department = request.data.get("department")
        shifts = request.data.get("shifts", [])
        created, errors = [], []

        for entry in shifts:
            entry.update({
                "department": department,
                "hotel": hotel.id,
                "period": period.id,
            })
            serializer = StaffRosterSerializer(data=entry, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append({"data": entry, "errors": serializer.errors})

        return Response({"created": created, "errors": errors},
                        status=201 if not errors else 207)

    @action(detail=False, methods=['post'], url_path='create-for-week')
    def create_for_week(self, request, *args, **kwargs):
        """
        POST /attendance/<hotel_slug>/periods/create-for-week/
        {
          "date": "2025-07-21"
        }
        """
        input_date = request.data.get("date")
        if not input_date:
            return Response({"error": "Field 'date' is required."}, status=400)

        parsed_date = parse_date(input_date)
        if not parsed_date:
            return Response({"error": "Invalid date format."}, status=400)

        # Monday start (0 = Monday)
        start_date = parsed_date - timedelta(days=parsed_date.weekday())
        end_date = start_date + timedelta(days=6)

        hotel = self.get_hotel()

        period, created = RosterPeriod.objects.get_or_create(
            hotel=hotel,
            start_date=start_date,
            defaults={
                "end_date": end_date,
                "title": f"Week of {start_date.strftime('%b %d')}",
                "created_by": getattr(self.request.user, "staff_profile", None),
            }
        )

        serializer = self.get_serializer(period)
        return Response(serializer.data, status=201 if created else 200)
    # add this to your class (or edit your existing one)
    
    @action(detail=True, methods=["get"], url_path="export-pdf")
    def export_pdf(self, request, pk=None, **kwargs):
        """
        GET /attendance/<hotel_slug>/periods/<pk>/export-pdf/?department=...
        """
        period = self.get_object()
        hotel = self.get_hotel()
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        qs = StaffRoster.objects.select_related("staff", "location") \
                                .filter(period=period, hotel=hotel)
        if department:
            qs = qs.filter(department__slug=department)

        if location_id:
            qs = qs.filter(location_id=location_id)

        title = f"Weekly Roster – {period.title or period.start_date}"
        meta = [
            f"Hotel: {hotel.name}",
            f"Period: {period.start_date} – {period.end_date}",
            f"Department: {department or 'All'}",
        ]

        # NEW: Use the weekly board-style PDF
        pdf_bytes = build_weekly_roster_pdf(
            title,
            meta,
            qs,
            period.start_date,
            period.end_date
        )

        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = (
            f'attachment; filename="roster_{hotel.slug}_{period.start_date}.pdf"'
        )
        return resp

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        for period in queryset:
            hotel_name = period.hotel.name
            title = period.title
            start_date = period.start_date.strftime("%B %d, %Y")
            end_date = period.end_date.strftime("%B %d, %Y")
            published = period.published
            created_by = f"{period.created_by.first_name} {period.created_by.last_name}" if period.created_by else "N/A"

            # Get departments related to this period through roster requirements
            departments = set(req.department.name for req in period.requirements.all())

            print(
                f"RosterPeriod: {title} | Hotel: {hotel_name} | "
                f"Start: {start_date} | End: {end_date} | Published: {published} | "
                f"Created by: {created_by} | Departments: {', '.join(departments) if departments else 'None'}"
            )

        return Response(serializer.data)
# ---------------------- Staff Roster ----------------------
class StaffRosterViewSet(viewsets.ModelViewSet):
    queryset = StaffRoster.objects.select_related('staff', 'hotel', 'period', 'approved_by', 'location').all()
    serializer_class = StaffRosterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = StaffRosterFilter
    pagination_class = None
    
    def get_queryset(self):
        qs = super().get_queryset()

        staff_id = self.request.query_params.get("staff") or self.request.query_params.get("staff_id")
        period_id = self.request.query_params.get("period")
        location_id = self.request.query_params.get("location")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        print(f"--- get_queryset filters ---")
        print(f"staff_id={staff_id}, period_id={period_id}, location_id={location_id}, start={start}, end={end}")

        if staff_id:
            qs = qs.filter(staff_id=staff_id)
            print(f"Filtered by staff_id, count={qs.count()}")
        if period_id:
            qs = qs.filter(period_id=period_id)
            print(f"Filtered by period_id, count={qs.count()}")
        if location_id:
            qs = qs.filter(location_id=location_id)
            print(f"Filtered by location_id, count={qs.count()}")
        if start and end:
            qs = qs.filter(shift_date__range=[start, end])
            print(f"Filtered by shift_date range, count={qs.count()}")

        print(f"Final queryset count: {qs.count()}")

        return qs

    def perform_create(self, serializer):
        staff = getattr(self.request.user, "staff_profile", None)
        serializer.save(approved_by=staff)

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request, *args, **kwargs):
        all_shifts = request.data.get('shifts', []) or []
        created_data = [s for s in all_shifts if not s.get("id")]
        updated_data = [s for s in all_shifts if s.get("id")]

        default_hotel = request.data.get("hotel")
        default_period = request.data.get("period")
        if default_hotel:
            for s in created_data:
                s.setdefault("hotel", default_hotel)
        if default_period:
            for s in created_data:
                s.setdefault("period", default_period)

        errors = []
        created_result, updated_result = [], []

        # Check for duplicates within created_data
        seen = set()
        for idx, shift in enumerate(created_data):
            key = (shift.get("staff"), shift.get("shift_date"), shift.get("shift_start"))
            if key in seen:
                errors.append({"index": idx, "error": "Duplicate shift in batch."})
            else:
                seen.add(key)

        if errors:
            return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Check duplicates for updated_data against existing shifts excluding self
        for idx, payload in enumerate(updated_data):
            instance = StaffRoster.objects.filter(pk=payload["id"]).first()
            if not instance:
                errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                continue

            # Check if new (staff, shift_date, shift_start) combination exists in another shift
            staff = payload.get("staff", instance.staff_id)
            shift_date = payload.get("shift_date", instance.shift_date)
            shift_start = payload.get("shift_start", instance.shift_start)

            conflict = StaffRoster.objects.filter(
                staff=staff,
                shift_date=shift_date,
                shift_start=shift_start
            ).exclude(id=instance.id).exists()

            if conflict:
                errors.append({"id": payload.get("id"), "detail": "Duplicate shift with these fields exists."})

        if errors:
            return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if created_data:
                staff_date_map = defaultdict(list)
                
                # Group new shifts by staff and shift_date
                for shift in created_data:
                    staff_id = shift.get("staff")
                    shift_date = shift.get("shift_date")
                    if staff_id and shift_date:
                        staff_date_map[(staff_id, shift_date)].append(shift)

                for (staff_id, shift_date), shifts in staff_date_map.items():
                    # Check if existing shifts for this staff and date
                    existing_shifts = StaffRoster.objects.filter(
                        staff_id=staff_id,
                        shift_date=shift_date
                    )
                    if existing_shifts.exists():
                        # Update existing shifts to split shift = True
                        existing_shifts.filter(is_split_shift=False).update(is_split_shift=True)

                    # If more than one new shift for the staff on the date, mark all new shifts as split shift
                    if len(shifts) > 1 or existing_shifts.exists():
                        for shift in shifts:
                            shift["is_split_shift"] = True
            create_ser = StaffRosterSerializer(data=created_data, many=True, context={'request': request})
            if create_ser.is_valid():
                create_ser.save()
                created_result = create_ser.data
            else:
                errors.extend(create_ser.errors)
            if updated_data and not errors:
                for payload in updated_data:
                    instance = StaffRoster.objects.filter(pk=payload["id"]).first()
                    if not instance:
                        errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                        continue
                    ser = StaffRosterSerializer(instance, data=payload, partial=True, context={'request': request})
                    if ser.is_valid():
                        ser.save()
                        updated_result.append(ser.data)
                    else:
                        errors.append(ser.errors)

            if errors:
                transaction.set_rollback(True)
                return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"created": created_result, "updated": updated_result, "errors": []}, status=status.HTTP_201_CREATED)
    
    
    @action(detail=False, methods=["get"], url_path="daily-pdf")
    def daily_pdf(self, request, hotel_slug=None, **kwargs):
        hotel_slug = request.query_params.get("hotel_slug")
        day = request.query_params.get("date")
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        if not (hotel_slug and day):
            return Response({"error": "hotel_slug and date are required."}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        qs = StaffRoster.objects.select_related("staff", "location").filter(hotel=hotel, shift_date=date.fromisoformat(day))

        if department:
            qs = qs.filter(department__slug=department)

        if location_id:
            qs = qs.filter(location_id=location_id)

        title = f"Daily Roster – {day}"
        meta = [
            f"Hotel: {hotel.name}",
            f"Date: {day}",
            f"Department: {department or 'All'}",
        ]

        pdf_bytes = build_roster_pdf(title, meta, qs, landscape_mode=False)
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="roster_{hotel.slug}_{day}.pdf"'
        return resp

    @action(detail=False, methods=["get"], url_path="staff-pdf")
    def staff_pdf(self, request, hotel_slug=None, **kwargs):
        hotel_slug = request.query_params.get("hotel_slug")
        staff_id = request.query_params.get("staff_id") or request.query_params.get("staff")
        period_id = request.query_params.get("period")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        department = request.query_params.get("department")
        location_id = request.query_params.get("location")

        if not (hotel_slug and staff_id):
            return Response({"error": "hotel_slug and staff_id are required."}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        qs = StaffRoster.objects.select_related("staff", "location", "period").filter(hotel=hotel, staff_id=staff_id)

        period_obj = None
        if period_id:
            qs = qs.filter(period_id=period_id)
            period_obj = RosterPeriod.objects.filter(pk=period_id).first()
        elif start and end:
            qs = qs.filter(shift_date__range=[start, end])
        else:
            return Response({"error": "Provide either 'period' or 'start' & 'end'."}, status=400)

        if department:
            qs = qs.filter(department__slug=department)
        if location_id:
            qs = qs.filter(location_id=location_id)

        staff = qs.first().staff if qs.exists() else None
        staff_name = (
            f"{getattr(staff, 'first_name', '')} {getattr(staff, 'last_name', '')}".strip()
            if staff else f"#{staff_id}"
        )

        if period_obj:
            date_str = f"{period_obj.start_date} – {period_obj.end_date}"
        else:
            date_str = f"{start} – {end}"

        title = f"Roster – {staff_name}"
        meta = [
            f"Hotel: {hotel.name}",
            f"Staff: {staff_name}",
            f"Range: {date_str}",
            f"Department: {department or 'All'}",
        ]

        pdf_bytes = build_roster_pdf(title, meta, qs, landscape_mode=False)
        resp = HttpResponse(pdf_bytes, content_type="application/pdf")
        resp["Content-Disposition"] = f'attachment; filename="roster_{hotel.slug}_staff_{staff_id}.pdf"'
        return resp
    
class ShiftLocationViewSet(viewsets.ModelViewSet):
    queryset = ShiftLocation.objects.all()
    serializer_class = ShiftLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_hotel(self):
        """
        Resolve the Hotel instance either from query params or kwargs.
        """
        hotel_slug = (
            self.kwargs.get("hotel_slug")
            or self.request.query_params.get("hotel_slug")
        )
        if not hotel_slug:
            return None
        return get_object_or_404(Hotel, slug=hotel_slug)

    def get_queryset(self):
        qs = super().get_queryset()
        hotel = self.get_hotel()
        if hotel:
            qs = qs.filter(hotel=hotel)
        return qs

    def perform_create(self, serializer):
        """
        Attach the hotel automatically during creation.
        """
        hotel = self.get_hotel()
        if hotel:
            serializer.save(hotel=hotel)
        else:
            raise ValueError("Hotel slug is required to create a shift location.")

    def perform_update(self, serializer):
        """
        Prevent changing the hotel on update (always enforce current hotel).
        """
        hotel = self.get_hotel()
        if hotel:
            serializer.save(hotel=hotel)
        else:
            serializer.save()

class DailyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = DailyPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_hotel(self):
        hotel_slug = self.kwargs.get("hotel_slug")
        return get_object_or_404(Hotel, slug=hotel_slug)

    def get_queryset(self):
        hotel = self.get_hotel()
        department_slug = self.kwargs.get('department_slug')
        queryset = DailyPlan.objects.filter(hotel=hotel)
        if department_slug:
            queryset = queryset.filter(
                entries__roster__department__slug=department_slug
            ).distinct()
        return queryset

    @action(detail=False, methods=['get'], url_path='prepare-daily-plan')
    def prepare_daily_plan(self, request, *args, **kwargs):
        hotel = self.get_hotel()
        department_slug = kwargs.get('department_slug')
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({'detail': 'date query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'detail': 'Invalid date format, expected YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        plan, created = DailyPlan.objects.get_or_create(hotel=hotel, date=date_obj)

        # Clear existing entries to regenerate fresh
        plan.entries.all().delete()

        # Filter roster shifts for that date
        filters = {
            "hotel": hotel,
            "shift_date": date_obj,
            "shift_start__isnull": False,
            "shift_end__isnull": False,
        }
        if department_slug:
            filters["department__slug"] = department_slug

        roster_shifts = StaffRoster.objects.filter(**filters).select_related(
            'staff', 'location', 'staff__role', 'department'
        )

        # Use update_or_create for each shift to avoid duplicates
        for shift in roster_shifts:
            DailyPlanEntry.objects.update_or_create(
                plan=plan,
                staff=shift.staff,
                location=shift.location,
                shift_start=shift.shift_start,
                shift_end=shift.shift_end,
                defaults={
                    'notes': '',
                    'roster': shift,
                }
            )

        # Return filtered entries with valid shift info
        filtered_entries = plan.entries.filter(
            roster__isnull=False,
            roster__shift_start__isnull=False,
            roster__shift_end__isnull=False,
        ).select_related('staff', 'location', 'roster', 'staff__role', 'staff__department')

        serializer = self.get_serializer(plan)
        data = serializer.data
        data['entries'] = DailyPlanEntrySerializer(filtered_entries, many=True).data

        return Response(data)


class DailyPlanEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DailyPlanEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_daily_plan(self):
        daily_plan_id = self.kwargs.get("daily_plan_pk")
        return get_object_or_404(DailyPlan, pk=daily_plan_id)

    def get_queryset(self):
        daily_plan = self.get_daily_plan()
        return DailyPlanEntry.objects.filter(plan=daily_plan)

    def perform_create(self, serializer):
        daily_plan = self.get_daily_plan()
        serializer.save(plan=daily_plan)   


class ShiftCopyViewSet(viewsets.ViewSet):
    """
    ViewSet to handle shift copying operations.
    """

    @action(detail=False, methods=['post'])
    def copy_shift(self, request, hotel_slug=None):
        serializer = CopyShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shift_id = serializer.validated_data['shift_id']
        target_date = serializer.validated_data['target_date']

        # Find the original shift
        original_shift = get_object_or_404(StaffRoster, id=shift_id)

        # Create a copy with updated date
        copied_shift = StaffRoster.objects.create(
            hotel=original_shift.hotel,
            staff=original_shift.staff,
            shift_date=target_date,
            start_time=original_shift.start_time,
            end_time=original_shift.end_time,
            expected_hours=original_shift.expected_hours,
            department=original_shift.department,
            location=original_shift.location,
            # copy other relevant fields as needed
        )
        return Response({'copied_shift_id': copied_shift.id}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def copy_day(self, request, hotel_slug=None):
        serializer = CopyDaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff_id = serializer.validated_data['staff_id']
        source_date = serializer.validated_data['source_date']
        target_date = serializer.validated_data['target_date']

        # Get all shifts for this staff on source date and hotel
        shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            staff_id=staff_id,
            shift_date=source_date,
        )

        new_shifts = []
        for shift in shifts:
            new_shift = StaffRoster.objects.create(
                hotel=shift.hotel,
                staff=shift.staff,
                shift_date=target_date,
                start_time=shift.start_time,
                end_time=shift.end_time,
                expected_hours=shift.expected_hours,
                department=shift.department,
                location=shift.location,
            )
            new_shifts.append(new_shift.id)

        return Response({'copied_shifts': new_shifts}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def copy_day_all(self, request, hotel_slug=None):
        serializer = CopyDayAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source_date = serializer.validated_data['source_date']
        target_date = serializer.validated_data['target_date']

        shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            shift_date=source_date,
        )

        new_shifts = []
        for shift in shifts:
            new_shift = StaffRoster.objects.create(
                hotel=shift.hotel,
                staff=shift.staff,
                shift_date=target_date,
                start_time=shift.start_time,
                end_time=shift.end_time,
                expected_hours=shift.expected_hours,
                department=shift.department,
                location=shift.location,
            )
            new_shifts.append(new_shift.id)

        return Response({'copied_shifts': new_shifts}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def copy_week(self, request, hotel_slug=None):
        serializer = CopyWeekSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        source_period_id = serializer.validated_data['source_period_id']
        target_period_id = serializer.validated_data['target_period_id']

        source_period = get_object_or_404(RosterPeriod, id=source_period_id, hotel__slug=hotel_slug)
        target_period = get_object_or_404(RosterPeriod, id=target_period_id, hotel__slug=hotel_slug)

        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            shift_date__gte=source_period.start_date,
            shift_date__lte=source_period.end_date,
        )

        # Calculate days difference between periods
        day_diff = (target_period.start_date - source_period.start_date).days

        new_shifts = []
        for shift in source_shifts:
            new_date = shift.shift_date + timedelta(days=day_diff)
            new_shift = StaffRoster.objects.create(
                hotel=shift.hotel,
                staff=shift.staff,
                shift_date=new_date,
                start_time=shift.start_time,
                end_time=shift.end_time,
                expected_hours=shift.expected_hours,
                department=shift.department,
                location=shift.location,
            )
            new_shifts.append(new_shift.id)

        return Response({'copied_shifts': new_shifts}, status=status.HTTP_201_CREATED)