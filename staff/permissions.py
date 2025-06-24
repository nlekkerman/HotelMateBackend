# permissions.py
from rest_framework import permissions
from .models import Staff

class IsSameHotelOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        try:
            staff_profile = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return False

        return obj.hotel_id == staff_profile.hotel_id
