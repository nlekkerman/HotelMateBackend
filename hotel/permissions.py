"""
Permissions for hotel app (Public Page Builder).
"""
from rest_framework.permissions import BasePermission
from staff.models import Staff


class IsSuperStaffAdminForHotel(BasePermission):
    """
    Permission to check if the user is a Super Staff Admin for the given hotel.
    
    This permission requires:
    1. User is authenticated
    2. User has a Staff profile
    3. Staff has access_level == 'super_staff_admin'
    4. Staff belongs to the hotel specified in the URL (hotel_slug)
    """
    
    def has_permission(self, request, view):
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get hotel_slug from URL kwargs
        hotel_slug = view.kwargs.get('hotel_slug')
        if not hotel_slug:
            return False
        
        try:
            # Check if user has a staff profile
            staff = Staff.objects.get(user=request.user)
            
            # Check if staff is super_staff_admin
            if staff.access_level != 'super_staff_admin':
                return False
            
            # Check if staff belongs to the hotel
            if staff.hotel.slug != hotel_slug:
                return False
            
            return True
            
        except Staff.DoesNotExist:
            return False
