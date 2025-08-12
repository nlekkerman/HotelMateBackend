# attendance/views.py

from datetime import timedelta, date, datetime, time
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
from .serializers import (
    ClockLogSerializer,
    RosterPeriodSerializer,
    StaffRosterSerializer,
    ShiftLocationSerializer,
    DailyPlanEntrySerializer,
    DailyPlanSerializer,
    CopyDayAllSerializer,
    CopyWeekSerializer,
    CopyWeekStaffSerializer,
)

from hotel.models import Hotel

# attendance/filters.py
import django_filters
from .filters import StaffRosterFilter

# ---------------------- helpers ----------------------
def euclidean(a, b):
    """Compute Euclidean distance between two equal‑length lists of floats."""
    import math
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def parse_time(t):
    print(f"parse_time input: {t} (type: {type(t)})")
    if isinstance(t, time):
        # Already a time object, just return it
        result = t
    else:
        # Assume it's a string, parse it
        result = datetime.strptime(t, "%H:%M").time()
    print(f"parse_time output: {result}")
    return result


def calculate_shift_range(shift_date, start_str, end_str):
    print(f"calculate_shift_range called with shift_date={shift_date}, start_str={start_str}, end_str={end_str}")
    start = parse_time(start_str)
    end = parse_time(end_str)

    start_dt = datetime.combine(shift_date, start)
    print(f"Start datetime: {start_dt}")

    if end <= start:
        # Crosses midnight
        end_dt = datetime.combine(shift_date + timedelta(days=1), end)
        print(f"Shift crosses midnight, end datetime set to: {end_dt}")
    else:
        end_dt = datetime.combine(shift_date, end)
        print(f"Shift does not cross midnight, end datetime set to: {end_dt}")

    # Special case: allow shifts until 4 AM to count as "today"
    if end <= time(4, 0) and end <= start:
        end_dt = datetime.combine(shift_date, end) + timedelta(days=1)
        print(f"Special case: shift ends before 4 AM, adjusted end datetime: {end_dt}")

    print(f"calculate_shift_range result: start_dt={start_dt}, end_dt={end_dt}")
    return start_dt, end_dt

def shifts_overlap(start1, end1, start2, end2):
    overlap = start1 < end2 and start2 < end1
    print(f"shifts_overlap called with start1={start1}, end1={end1}, start2={start2}, end2={end2} -> {overlap}")
    return overlap

def detect_overlapping_shifts(shifts):
    parsed = []
    for shift in shifts:
        print(f"Processing shift: {shift}")
        shift_date = shift["shift_date"]
        # Check if shift_date is a date object but NOT datetime
        if isinstance(shift_date, date) and not isinstance(shift_date, datetime):
            shift_date_str = shift_date.strftime("%Y-%m-%d")
            print(f"Converted date object to string: {shift_date_str}")
        else:
            shift_date_str = shift_date

        date_obj = datetime.strptime(shift_date_str, "%Y-%m-%d").date()
        start, end = calculate_shift_range(date_obj, shift["shift_start"], shift["shift_end"])
        parsed.append((start, end, shift))

    parsed.sort(key=lambda x: x[0])  # Sort by start datetime
    print("Parsed shifts sorted by start time:")
    for p in parsed:
        print(p)

    for i in range(1, len(parsed)):
        prev_start, prev_end, _ = parsed[i - 1]
        curr_start, curr_end, _ = parsed[i]

        if shifts_overlap(prev_start, prev_end, curr_start, curr_end) and prev_end != curr_start:
            print("Overlap detected between shifts:")
            print(f"Prev: {prev_start} - {prev_end}")
            print(f"Curr: {curr_start} - {curr_end}")
            return True

    print("No overlapping shifts detected.")
    return False
# ---------------------- Clock / Face ----------------------
class ClockLogViewSet(viewsets.ModelViewSet):
    queryset = ClockLog.objects.select_related('staff__department','staff', 'hotel').all()
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
    
    @action(detail=False, methods=['get'], url_path='currently-clocked-in')
    def currently_clocked_in(self, request):
        hotel_slug = request.query_params.get('hotel_slug')
        if not hotel_slug:
            return Response({"detail": "hotel_slug query parameter required"}, status=400)

        logs = self.queryset.filter(time_out__isnull=True, hotel__slug=hotel_slug).order_by('-time_in')

        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

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
        department_slug = self.request.query_params.get("department")
        hotel_slug = self.request.query_params.get("hotel_slug")

        print(f"--- get_queryset filters ---")
        print(f"hotel_slug={hotel_slug}, department_slug={department_slug}, staff_id={staff_id}, period_id={period_id}, location_id={location_id}, start={start}, end={end}")

        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        if department_slug:
            qs = qs.filter(staff__department__slug=department_slug)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        if period_id:
            qs = qs.filter(period_id=period_id)
        if location_id:
            qs = qs.filter(location_id=location_id)
        if start and end:
            qs = qs.filter(shift_date__range=[start, end])

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

        # In-batch duplicate check
        seen = set()
        for idx, shift in enumerate(created_data):
            key = (shift.get("staff"), shift.get("shift_date"), shift.get("shift_start"))
            if key in seen:
                errors.append({"index": idx, "error": "Duplicate shift in batch."})
            else:
                seen.add(key)

        if errors:
            return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # DB-level duplicate check for updates
        for idx, payload in enumerate(updated_data):
            instance = StaffRoster.objects.filter(pk=payload["id"]).first()
            if not instance:
                errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                continue

            staff = payload.get("staff", instance.staff_id)
            shift_date = payload.get("shift_date", instance.shift_date.strftime("%Y-%m-%d"))
            shift_start = payload.get("shift_start", instance.shift_start.strftime("%H:%M"))

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
            staff_date_map = defaultdict(list)
            for shift in created_data:
                staff_id = shift.get("staff")
                shift_date = shift.get("shift_date")
                if staff_id and shift_date:
                    staff_date_map[(staff_id, shift_date)].append(shift)

            for (staff_id, shift_date), new_shifts in staff_date_map.items():
                existing = list(
                    StaffRoster.objects.filter(staff_id=staff_id, shift_date=shift_date).values(
                        "shift_date", "shift_start", "shift_end"
                    )
                )
                all_combined = existing + new_shifts
                if detect_overlapping_shifts(all_combined):
                    errors.append({
                        "staff": staff_id,
                        "date": shift_date,
                        "detail": "Overlapping shifts are not allowed (except adjacent or ending before 04:00)."
                    })

                if len(new_shifts) > 1 or existing:
                    for shift in new_shifts:
                        shift["is_split_shift"] = True

            if errors:
                return Response({"created": [], "updated": [], "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

            create_ser = StaffRosterSerializer(data=created_data, many=True, context={'request': request})
            if create_ser.is_valid():
                create_ser.save()
                created_result = create_ser.data
            else:
                print("Create serializer errors:", create_ser.errors)
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
                        print("Update serializer errors:", ser.errors)
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


class CopyRosterViewSet(viewsets.ViewSet):
    """
    ViewSet to handle bulk roster copying using CopyWeekSerializer.
    """

    @action(detail=False, methods=['post'])
    def copy_roster_bulk(self, request, hotel_slug=None):
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

        day_diff = (target_period.start_date - source_period.start_date).days

        new_shifts = []
        for shift in source_shifts:
            new_date = shift.shift_date + timedelta(days=day_diff)
            new_shifts.append(
                StaffRoster(
                    hotel=shift.hotel,
                    staff=shift.staff,
                    shift_date=new_date,
                    shift_start=shift.shift_start,   # corrected here
                    shift_end=shift.shift_end,
                    expected_hours=shift.expected_hours,
                    department=shift.department,
                    location=shift.location,
                    period=target_period,
                )
            )

        StaffRoster.objects.bulk_create(new_shifts)

        return Response(
            {'copied_shifts_count': len(new_shifts)},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def copy_roster_day_all(self, request, hotel_slug=None):
        """
        Copy shifts for all staff from source_date to target_date.
        """
        serializer = CopyDayAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_date = serializer.validated_data['source_date']
        target_date = serializer.validated_data['target_date']

        source_period = RosterPeriod.objects.filter(
            hotel__slug=hotel_slug,
            start_date__lte=source_date,
            end_date__gte=source_date,
        ).first()
        target_period = RosterPeriod.objects.filter(
            hotel__slug=hotel_slug,
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).first()

        if not source_period or not target_period:
            return Response(
                {"detail": "Source or target date is not within any roster period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            shift_date=source_date,
        )

        new_shifts = []
        for shift in source_shifts:
            new_shifts.append(
                StaffRoster(
                    hotel=shift.hotel,
                    staff=shift.staff,
                    shift_date=target_date,
                    shift_start=shift.shift_start,
                    shift_end=shift.shift_end,
                    expected_hours=shift.expected_hours,
                    department=shift.department,
                    location=shift.location,
                    period=target_period,
                )
            )

        StaffRoster.objects.bulk_create(new_shifts)

        return Response(
            {'copied_shifts_count': len(new_shifts)},
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=False, methods=['post'])
    def copy_week_staff(self, request, hotel_slug=None):
        """
        Copy all shifts for a single staff member from one period (week) to another.
        """
        serializer = CopyWeekStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        staff_id = serializer.validated_data['staff_id']
        source_period_id = serializer.validated_data['source_period_id']
        target_period_id = serializer.validated_data['target_period_id']

        # Get source and target periods
        source_period = get_object_or_404(
            RosterPeriod, id=source_period_id, hotel__slug=hotel_slug
        )
        target_period = get_object_or_404(
            RosterPeriod, id=target_period_id, hotel__slug=hotel_slug
        )

        # Get shifts only for this staff in the source period
        source_shifts = StaffRoster.objects.filter(
            hotel__slug=hotel_slug,
            staff_id=staff_id,
            shift_date__gte=source_period.start_date,
            shift_date__lte=source_period.end_date,
        )

        if not source_shifts.exists():
            return Response(
                {"detail": "No shifts found for this staff in the source period."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate date difference between periods
        day_diff = (target_period.start_date - source_period.start_date).days

        # Build new shifts list
        new_shifts = []
        for shift in source_shifts:
            new_date = shift.shift_date + timedelta(days=day_diff)
            new_shifts.append(
                StaffRoster(
                    hotel=shift.hotel,
                    staff=shift.staff,
                    shift_date=new_date,
                    shift_start=shift.shift_start,
                    shift_end=shift.shift_end,
                    expected_hours=shift.expected_hours,
                    department=shift.department,
                    location=shift.location,
                    period=target_period,
                )
            )

        StaffRoster.objects.bulk_create(new_shifts)

        return Response(
            {"copied_shifts_count": len(new_shifts)},
            status=status.HTTP_201_CREATED,
        )