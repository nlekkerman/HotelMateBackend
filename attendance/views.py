# attendance/views.py

from datetime import timedelta
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from django_filters.rest_framework import DjangoFilterBackend

from .models import ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftLocation
from .serializers import ClockLogSerializer, RosterPeriodSerializer, StaffRosterSerializer, ShiftLocationSerializer
from hotel.models import Hotel


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
# ---------------------- Staff Roster ----------------------
class StaffRosterViewSet(viewsets.ModelViewSet):
    queryset = StaffRoster.objects.select_related('staff', 'hotel', 'period', 'approved_by', 'location').all()
    serializer_class = StaffRosterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['hotel__slug', 'department', 'period', 'location']

    def get_queryset(self):
        qs = super().get_queryset()

        hotel_slug = self.kwargs.get("hotel_slug") or self.request.query_params.get("hotel_slug")
        department = self.request.query_params.get("department")
        period_id = self.request.query_params.get("period")
        staff_id = self.request.query_params.get("staff") or self.request.query_params.get("staff_id")
        location_id = self.request.query_params.get("location")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        if department:
            qs = qs.filter(department=department)
        if period_id:
            qs = qs.filter(period_id=period_id)
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        if location_id:
            qs = qs.filter(location_id=location_id)
        if start and end:
            qs = qs.filter(shift_date__range=[start, end])

        return qs

    def perform_create(self, serializer):
        staff = getattr(self.request.user, "staff_profile", None)
        serializer.save(approved_by=staff)

    @action(detail=False, methods=['post'], url_path='bulk-save')
    def bulk_save(self, request, *args, **kwargs):
        """
        Accepts:
        {
          "shifts": [
            { id?, hotel, period, staff, department, shift_date, shift_start, shift_end, ... },
            ...
          ],
          "hotel": <id?>,  # optional top-level default
          "period": <id?>  # optional top-level default
        }
        Works with split shifts (unique_together = staff, shift_date, shift_start).
        """
        all_shifts = request.data.get('shifts', []) or []
        created_data = [s for s in all_shifts if not s.get("id")]
        updated_data = [s for s in all_shifts if s.get("id")]

        # propagate optional defaults
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

        with transaction.atomic():
            # CREATE
            if created_data:
                create_ser = StaffRosterSerializer(
                    data=created_data, many=True, context={'request': request}
                )
                if create_ser.is_valid():
                    create_ser.save()
                    created_result = create_ser.data
                else:
                    errors.extend(create_ser.errors)

            # UPDATE
            if updated_data and not errors:
                for payload in updated_data:
                    instance = StaffRoster.objects.filter(pk=payload["id"]).first()
                    if not instance:
                        errors.append({"id": payload.get("id"), "detail": "Shift not found"})
                        continue

                    ser = StaffRosterSerializer(
                        instance, data=payload, partial=True, context={'request': request}
                    )
                    if ser.is_valid():
                        ser.save()
                        updated_result.append(ser.data)
                    else:
                        errors.append(ser.errors)

            if errors:
                transaction.set_rollback(True)
                return Response(
                    {"created": [], "updated": [], "errors": errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {"created": created_result, "updated": updated_result, "errors": []},
            status=status.HTTP_201_CREATED
        )

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

