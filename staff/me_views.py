"""
Staff Profile API View

Provides a simplified /me endpoint for staff profile information
with canonical permissions payload.
"""

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from staff.models import Staff
from staff.serializers import StaffSerializer
from staff.permissions import resolve_staff_navigation


class StaffMeView(APIView):
    """
    Staff profile endpoint for the current authenticated user.
    
    GET /api/staff/hotel/{hotel_slug}/me/
    
    Returns staff data with canonical permissions payload structure.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, hotel_slug):
        """Get current staff profile information with canonical permissions."""
        try:
            staff = Staff.objects.get(user=request.user, hotel__slug=hotel_slug)
            
            # Get staff data
            staff_data = StaffSerializer(staff).data
            
            # Get canonical permissions payload
            permissions = resolve_staff_navigation(request.user)
            
            # Merge canonical permissions into staff data
            staff_data.update(permissions)
            
            return Response(staff_data, status=status.HTTP_200_OK)
            
        except Staff.DoesNotExist:
            # No staff profile - return canonical structure with empty values
            permissions = resolve_staff_navigation(request.user)
            
            return Response(
                {
                    "detail": "Staff profile not found for the current user and hotel.",
                    **permissions  # Still provide canonical structure
                },
                status=status.HTTP_404_NOT_FOUND,
            )