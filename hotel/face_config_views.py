"""
Face Configuration API Views

Provides hotel-specific face recognition configuration endpoints.
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Hotel


class HotelFaceConfigView(APIView):
    """
    Public endpoint to get hotel face recognition configuration.
    Used by frontend to determine face recognition capabilities.
    
    GET /api/hotels/{hotel_slug}/face-config/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        """Get face recognition configuration for the hotel"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Get face configuration from attendance settings with defaults
        face_config = self.get_hotel_face_config(hotel)
        
        return Response({
            'hotel_slug': hotel.slug,
            'face_recognition_config': face_config
        }, status=status.HTTP_200_OK)
    
    def get_hotel_face_config(self, hotel):
        """Get face attendance configuration for a hotel with fallbacks"""
        try:
            settings = hotel.attendance_settings
            return {
                'face_attendance_enabled': getattr(settings, 'face_attendance_enabled', False),
                'face_attendance_min_confidence': getattr(settings, 'face_attendance_min_confidence', 0.80),
                'require_face_consent': getattr(settings, 'require_face_consent', True),
                'allow_face_self_registration': getattr(settings, 'allow_face_self_registration', True),
                'face_data_retention_days': getattr(settings, 'face_data_retention_days', 365),
                'face_attendance_departments': getattr(settings, 'face_attendance_departments', [])
            }
        except AttributeError:
            # Return default configuration if no attendance settings exist
            return {
                'face_attendance_enabled': False,
                'face_attendance_min_confidence': 0.80,
                'require_face_consent': True,
                'allow_face_self_registration': True,
                'face_data_retention_days': 365,
                'face_attendance_departments': []
            }