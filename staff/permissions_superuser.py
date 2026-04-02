from rest_framework.permissions import BasePermission

from staff.models import Staff


class IsSuperUser(BasePermission):
    """
    Allows access to Django superusers OR staff members with
    super_staff_admin / staff_admin access level.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Django superusers always pass
        if request.user.is_superuser:
            return True

        # App-level admins: super_staff_admin or staff_admin
        try:
            staff = request.user.staff_profile
            return staff.access_level in (
                'super_staff_admin', 'staff_admin'
            )
        except Staff.DoesNotExist:
            return False
