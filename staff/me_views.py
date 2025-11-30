"""
Staff Profile API View

Provides a simplified /me endpoint for staff profile information.
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from staff.models import Staff
from staff.serializers import StaffSerializer


class StaffMeView(APIView):
    """
    Staff profile endpoint for the current authenticated user.
    
    GET /api/staff/hotel/{hotel_slug}/me/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, hotel_slug):
        """Get current staff profile information"""
        try:
            staff = Staff.objects.get(user=request.user, hotel__slug=hotel_slug)
        except Staff.DoesNotExist:
            return Response(
                {"detail": "Staff profile not found for the current user and hotel."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = StaffSerializer(staff)
        return Response(serializer.data, status=status.HTTP_200_OK)