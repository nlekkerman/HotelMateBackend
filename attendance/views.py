from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage

from .models import ClockLog, StaffFace
from .serializers import ClockLogSerializer
from hotel.models import Hotel

from deepface import DeepFace
import tempfile
import os


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

        # Ensure only one face per staff
        existing = StaffFace.objects.filter(staff=staff).first()
        if existing:
            existing.image.delete()
            existing.delete()

        # Save face data
        face_entry = StaffFace.objects.create(
            hotel=hotel,
            staff=staff,
            image=image_file
        )

        # Update staff model if using has_registered_face = models.BooleanField(default=False)
        staff.has_registered_face = True
        staff.save(update_fields=["has_registered_face"])

        return Response({"message": "Face registered successfully."})

    @action(detail=False, methods=['post'], url_path='face-clock-in/(?P<hotel_slug>[^/.]+)')
    def face_clock_in(self, request, hotel_slug=None):
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"error": "Image required."}, status=status.HTTP_400_BAD_REQUEST)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # Save uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as uploaded_temp:
            for chunk in image_file.chunks():
                uploaded_temp.write(chunk)
            uploaded_temp_path = uploaded_temp.name

        # Loop over known staff faces
        staff_faces = StaffFace.objects.select_related('staff').filter(
            hotel=hotel,
            staff__is_active=True
        )

        for face_entry in staff_faces:
            try:
                # Save stored image temporarily for comparison
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as known_temp:
                    known_temp.write(face_entry.image.read())
                    known_temp_path = known_temp.name

                # Perform face verification
                result = DeepFace.verify(
                    img1_path=uploaded_temp_path,
                    img2_path=known_temp_path,
                    model_name="VGG-Face",
                    enforce_detection=False,
                    detector_backend='opencv',
                    distance_metric="cosine"
                )

                if result.get("verified"):
                    log = ClockLog.objects.create(
                        hotel=hotel,
                        staff=face_entry.staff,
                        verified_by_face=True
                    )
                    os.remove(uploaded_temp_path)
                    os.remove(known_temp_path)

                    return Response({
                        "message": f"Clock-in successful for {face_entry.staff.first_name}",
                        "log": ClockLogSerializer(log).data
                    })

                os.remove(known_temp_path)

            except Exception as e:
                continue  # skip failed comparisons

        # Final cleanup
        if os.path.exists(uploaded_temp_path):
            os.remove(uploaded_temp_path)

        return Response({"error": "Face not recognized."}, status=status.HTTP_401_UNAUTHORIZED)
