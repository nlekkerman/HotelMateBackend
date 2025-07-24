from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

from .models import ClockLog, StaffFace
from .serializers import ClockLogSerializer
from hotel.models import Hotel

from deepface import DeepFace
import tempfile, os


class ClockLogViewSet(viewsets.ModelViewSet):
    queryset = ClockLog.objects.select_related('staff', 'hotel').all()
    serializer_class = ClockLogSerializer

    @action(detail=False, methods=['post'], url_path='register-face/(?P<hotel_slug>[^/.]+)')
    def register_face(self, request, hotel_slug=None):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Image required."}, status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        staff = getattr(request.user, "staff_profile", None)
        if not staff:
            return Response({"error": "User has no linked staff profile."}, status=status.HTTP_400_BAD_REQUEST)

        existing = StaffFace.objects.filter(staff=staff).first()
        if existing:
            existing.image.delete()
            existing.delete()

        StaffFace.objects.create(hotel=hotel, staff=staff, image=image_file)
        staff.has_registered_face = True
        staff.save(update_fields=["has_registered_face"])

        return Response({"message": "Face registered successfully."})

    @action(detail=False, methods=['post'], url_path='face-clock-in/(?P<hotel_slug>[^/.]+)')
    def face_clock_in(self, request, hotel_slug=None):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Image required."}, status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as uploaded_temp:
            for chunk in image_file.chunks():
                uploaded_temp.write(chunk)
            uploaded_temp_path = uploaded_temp.name

        staff_faces = StaffFace.objects.select_related('staff').filter(hotel=hotel, staff__is_active=True)

        for face_entry in staff_faces:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as known_temp:
                    known_temp.write(face_entry.image.read())
                    known_temp_path = known_temp.name

                result = DeepFace.verify(
                    img1_path=uploaded_temp_path,
                    img2_path=known_temp_path,
                    model_name="VGG-Face",
                    enforce_detection=False,
                    detector_backend='opencv',
                    distance_metric="cosine"
                )

                if result.get("verified"):
                    staff = face_entry.staff
                    today = now().date()

                    existing_log = ClockLog.objects.filter(
                        hotel=hotel,
                        staff=staff,
                        time_in__date=today,
                        time_out__isnull=True
                    ).first()

                    if existing_log:
                        existing_log.time_out = now()
                        existing_log.save()
                        action_message = "Clock-out"
                    else:
                        existing_log = ClockLog.objects.create(
                            hotel=hotel,
                            staff=staff,
                            verified_by_face=True
                        )
                        action_message = "Clock-in"

                    os.remove(uploaded_temp_path)
                    os.remove(known_temp_path)

                    return Response({
                        "message": f"{action_message} successful for {staff.first_name}",
                        "log": ClockLogSerializer(existing_log).data
                    })

                os.remove(known_temp_path)

            except Exception as e:
                print("⚠️ Face match error:", str(e))
                continue

        if os.path.exists(uploaded_temp_path):
            os.remove(uploaded_temp_path)

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=["get"], url_path="status")
    def current_status(self, request):
        staff = getattr(request.user, "staff_profile", None)
        hotel_slug = request.query_params.get("hotel_slug")
        if not staff or not hotel_slug:
            return Response({"error": "Missing staff or hotel."}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        latest_log = ClockLog.objects.filter(hotel=hotel, staff=staff).order_by("-time_in").first()

        if not latest_log:
            return Response({"status": "not_clocked_in"})
        if latest_log.time_out:
            return Response({"status": "clocked_out", "last_log": latest_log.time_out})

        return Response({"status": "clocked_in", "since": latest_log.time_in})

    @action(detail=False, methods=['post'], url_path='detect/(?P<hotel_slug>[^/.]+)')
    def detect_face_only(self, request, hotel_slug=None):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Image required."}, status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as uploaded_temp:
            for chunk in image_file.chunks():
                uploaded_temp.write(chunk)
            uploaded_temp_path = uploaded_temp.name

        staff_faces = StaffFace.objects.select_related('staff').filter(hotel=hotel, staff__is_active=True)

        for face_entry in staff_faces:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as known_temp:
                    known_temp.write(face_entry.image.read())
                    known_temp_path = known_temp.name

                result = DeepFace.verify(
                    img1_path=uploaded_temp_path,
                    img2_path=known_temp_path,
                    model_name="VGG-Face",
                    enforce_detection=False,
                    detector_backend='opencv',
                    distance_metric="cosine"
                )

                if result.get("verified"):
                    staff = face_entry.staff
                    today = now().date()
                    is_clocked_in = ClockLog.objects.filter(
                        hotel=hotel,
                        staff=staff,
                        time_in__date=today,
                        time_out__isnull=True
                    ).exists()

                    os.remove(uploaded_temp_path)
                    os.remove(known_temp_path)

                    return Response({
                        "staff_id": staff.id,
                        "staff_name": f"{staff.first_name} {staff.last_name}",
                        "clocked_in": is_clocked_in
                    })

                os.remove(known_temp_path)

            except Exception as e:
                print("⚠️ Detection error:", str(e))
                continue

        if os.path.exists(uploaded_temp_path):
            os.remove(uploaded_temp_path)

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)

