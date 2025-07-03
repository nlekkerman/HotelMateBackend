from rest_framework import permissions
from .models import Staff

# ─── Section-Based Role/Department Access ───
DEPARTMENT_ROLE_PERMISSIONS = {
    "reception": {
        "departments": ["front_office", "management"],
        "roles": ["receptionist", "manager", "concierge"],
    },
    "kitchen": {
        "departments": ["kitchen"],
        "roles": ["chef", "waiter", "bartender"],
    },
    "maintenance": {
        "departments": ["maintenance"],
        "roles": ["technician", "maintenance_staff", "manager"],
    },
    "housekeeping": {
        "departments": ["housekeeping"],
        "roles": ["housekeeping_attendant", "manager"],
    },
    "admin_panels": {
        "access_levels": ["staff_admin", "super_staff_admin"],
    },
    "stock_tracker": {
        "departments": ["kitchen", "bar", "management"],
        "roles": ["chef", "bartender", "manager"],
    },
    "profile": {
        "everyone": True,
    },
    "services": {
        "roles": ["receptionist", "porter", "waiter", "manager"],
        "allow_on_duty": True,  # 👈 NEW override
    },
    # Add more as needed
}

class HasSectionAccess(permissions.BasePermission):
    """
    Grants access to specific app sections based on staff department, role, access level, or duty status.
    Requires the view to define: `required_section = "<section_key>"`
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        section = getattr(view, 'required_section', None)
        if not section:
            return False

        try:
            staff_profile = request.user.staff_profile
        except Staff.DoesNotExist:
            return False

        rule = DEPARTMENT_ROLE_PERMISSIONS.get(section)
        if not rule:
            return False

        # Universal access (like profile)
        if rule.get("everyone") is True:
            return True

        if "access_levels" in rule and staff_profile.access_level in rule["access_levels"]:
            return True

        if "departments" in rule and staff_profile.department in rule["departments"]:
            return True

        if "roles" in rule and staff_profile.role in rule["roles"]:
            return True

        # ✅ Special override: allow if on duty
        if rule.get("allow_on_duty") and staff_profile.is_on_duty:
            return True

        return False


# ─── Hotel-Specific Object-Level Permission ───
class IsSameHotelOrAdmin(permissions.BasePermission):
    """
    Object-level permission to restrict access to resources based on the user's hotel.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        try:
            staff_profile = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return False

        return obj.hotel_id == staff_profile.hotel_id
