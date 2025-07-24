from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import ClockLog, StaffFace, RosterPeriod, StaffRoster
from .serializers import ClockLogSerializer, RosterPeriodSerializer, StaffRosterSerializer
from hotel.models import Hotel


def euclidean(a, b):
    """Compute Euclidean distance between two equal‑length lists of floats."""
    import math
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class ClockLogViewSet(viewsets.ModelViewSet):
    queryset = ClockLog.objects.select_related('staff', 'hotel').all()
    serializer_class = ClockLogSerializer

    @action(detail=False, methods=['post'], url_path=r'register-face/(?P<hotel_slug>[^/.]+)')
    def register_face(self, request, hotel_slug=None):
        """
        Client must POST JSON:
          {
            "descriptor": [0.123, -0.045, …]   # length‑128 list of floats
          }
        """
        descriptor = request.data.get("descriptor")
        if not isinstance(descriptor, list) or len(descriptor) != 128:
            return Response(
                {"error": "A 128‑length descriptor array is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff = getattr(request.user, "staff_profile", None)
        if not staff:
            return Response(
                {"error": "User has no linked staff profile."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # replace any existing face
        StaffFace.objects.filter(staff=staff).delete()
        StaffFace.objects.create(
            hotel=hotel,
            staff=staff,
            encoding=descriptor
        )
        staff.has_registered_face = True
        staff.save(update_fields=["has_registered_face"])

        return Response({"message": "Face descriptor registered."})

    @action(detail=False, methods=['post'], url_path=r'face-clock-in/(?P<hotel_slug>[^/.]+)')
    def face_clock_in(self, request, hotel_slug=None):
        """
        Client must POST JSON:
          {
            "descriptor": [ … ]   # length‑128 list
          }
        """
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response(
                {"error": "A 128‑length descriptor array is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # load all enrolled descriptors for this hotel
        staff_faces = StaffFace.objects.select_related('staff')\
                                       .filter(hotel=hotel, staff__is_active=True)

        best_id, best_dist = None, float('inf')
        for face_entry in staff_faces:
            dist = euclidean(probe, face_entry.encoding)
            if dist < best_dist:
                best_dist, best_id = dist, face_entry.staff.id

        # threshold chosen empirically; ~0.6 works for tiny models
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
                staff.save(update_fields=["is_on_duty"])

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
                "log":    ClockLogSerializer(log).data
            })

        return Response(
            {"error": "Face not recognized."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=["get"], url_path="status")
    def current_status(self, request):
        staff = getattr(request.user, "staff_profile", None)
        hotel_slug = request.query_params.get("hotel_slug")
        if not staff or not hotel_slug:
            return Response({"error": "Missing staff or hotel."}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        latest_log = ClockLog.objects.filter(hotel=hotel, staff=staff)\
                                     .order_by("-time_in").first()

        if not latest_log:
            return Response({"status": "not_clocked_in"})
        if latest_log.time_out:
            return Response({"status": "clocked_out", "last_log": latest_log.time_out})
        return Response({"status": "clocked_in", "since": latest_log.time_in})

    @action(detail=False, methods=['post'], url_path=r'detect/(?P<hotel_slug>[^/.]+)')
    def detect_face_only(self, request, hotel_slug=None):
        """
        Just return staff info if descriptor matches; same signature as clock-in
        """
        probe = request.data.get("descriptor")
        if not isinstance(probe, list) or len(probe) != 128:
            return Response(
                {"error": "A 128‑length descriptor array is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff_faces = StaffFace.objects.select_related('staff')\
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
                "staff_id":   staff.id,
                "staff_name": f"{staff.first_name} {staff.last_name}",
                "clocked_in": is_clocked_in
            })

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

class RosterPeriodViewSet(viewsets.ModelViewSet):
    queryset = RosterPeriod.objects.select_related('hotel', 'created_by').all()
    serializer_class = RosterPeriodSerializer

    @action(detail=True, methods=['post'], url_path='add-shift')
    def add_shift(self, request, pk=None):
        """
        Add a single shift to this RosterPeriod
        """
        period = self.get_object()
        serializer = StaffRosterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(period=period, hotel=period.hotel)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='create-department-roster')
    def create_department_roster(self, request, pk=None):
        """
        Bulk-create shifts for a department within a roster period.
        {
          "department": "kitchen",
          "shifts": [
            {
              "staff": 7,
              "shift_date": "2025-07-26",
              "shift_start": "08:00",
              "shift_end": "16:00"
            },
            ...
          ]
        }
        """
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
            serializer = StaffRosterSerializer(data=entry)
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append({"data": entry, "errors": serializer.errors})

        return Response({
            "created": created,
            "errors": errors
        }, status=201 if not errors else 207)


class StaffRosterViewSet(viewsets.ModelViewSet):
    queryset = StaffRoster.objects.select_related('staff', 'hotel', 'period', 'approved_by').all()
    serializer_class = StaffRosterSerializer

    def perform_create(self, serializer):
        staff = getattr(self.request.user, "staff_profile", None)
        serializer.save(approved_by=staff)