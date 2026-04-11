"""
Canonical permissions system for HotelMate RBAC.

This module is the SINGLE SOURCE OF TRUTH for:
- Tier resolution (resolve_tier)
- Effective access computation (resolve_effective_access)
- Module visibility enforcement (HasNavPermission)
- Action authority enforcement (CanManage* classes)
- Platform/admin tier gates (IsDjangoSuperUser, IsAdminTier, IsSuperStaffAdminOrAbove)

ENFORCEMENT RULES:
- HasNavPermission controls ONLY module/route visibility — never mutation authority
- EVERY mutation endpoint MUST use an explicit action-level permission class
- Tier defaults are minimal: regular_staff sees only home+chat by default
- Role.default_navigation_items is the primary source of module access for regular_staff
- Staff.allowed_navigation_items is additive-only override
"""
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission

from staff.models import Staff, NavigationItem
from staff.nav_catalog import CANONICAL_NAV_SLUGS
from staff.serializers import NavigationItemSerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# Canonical constants (CANONICAL_NAV_SLUGS imported from staff.nav_catalog)
# ---------------------------------------------------------------------------

TIER_DEFAULT_NAVS = {
    'super_staff_admin': {
        'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
        'stock_tracker', 'housekeeping', 'attendance', 'staff_management',
        'room_services', 'maintenance', 'entertainment', 'hotel_info',
        'admin_settings',
    },
    'staff_admin': {
        'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
        'housekeeping', 'attendance', 'maintenance', 'hotel_info',
    },
    'regular_staff': {
        'home', 'chat',
    },
}

# Tiers ordered by descending authority
TIER_HIERARCHY = ('super_user', 'super_staff_admin', 'staff_admin', 'regular_staff')


# ---------------------------------------------------------------------------
# Tier resolver — single source of truth
# ---------------------------------------------------------------------------

def resolve_tier(user) -> str | None:
    """
    Canonical tier resolver. Returns the user's authority tier.

    Returns one of:
        'super_user'          — Django superuser (platform-level, all hotels)
        'super_staff_admin'   — Full hotel authority
        'staff_admin'         — Supervisor / department-lead
        'regular_staff'       — Operational only
        None                  — Not authenticated or no staff profile
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None

    if user.is_superuser:
        return 'super_user'

    try:
        staff = user.staff_profile
        return staff.access_level  # one of the ACCESS_LEVEL_CHOICES values
    except (AttributeError, Staff.DoesNotExist):
        return None


def _tier_at_least(tier: str | None, minimum: str) -> bool:
    """Return True if *tier* is at or above *minimum* in the hierarchy."""
    if tier is None:
        return False
    try:
        return TIER_HIERARCHY.index(tier) <= TIER_HIERARCHY.index(minimum)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Effective access resolver (replaces resolve_staff_navigation)
# ---------------------------------------------------------------------------

def resolve_effective_access(user) -> dict:
    """
    Canonical source of truth for staff navigation permissions.

    Computation:
        effective_navs = tier_defaults ∪ role_defaults ∪ staff_overrides
        (super_user gets ALL active navs for the hotel)

    Returns dict with keys:
        is_staff, is_superuser, hotel_slug, access_level, tier,
        allowed_navs (list[str]), navigation_items (list[dict])
    """
    base_payload = {
        'is_staff': False,
        'is_superuser': bool(getattr(user, 'is_superuser', False)),
        'hotel_slug': None,
        'access_level': None,
        'tier': None,
        'allowed_navs': [],
        'navigation_items': [],
    }

    if not user or not getattr(user, 'is_authenticated', False):
        return base_payload

    try:
        staff = user.staff_profile
    except (AttributeError, Staff.DoesNotExist):
        return base_payload

    tier = resolve_tier(user)

    base_payload.update({
        'is_staff': True,
        'hotel_slug': staff.hotel.slug,
        'access_level': staff.access_level,
        'tier': tier,
    })

    # All active nav items for this hotel
    hotel_nav_items = NavigationItem.objects.filter(
        hotel=staff.hotel,
        is_active=True,
    ).select_related('hotel').order_by('display_order', 'name')

    if tier == 'super_user':
        allowed_nav_items = hotel_nav_items
    else:
        # Tier defaults
        tier_navs = set(TIER_DEFAULT_NAVS.get(tier, set()))

        # Role defaults
        role = staff.role
        if role and hasattr(role, 'default_navigation_items'):
            role_navs = set(
                role.default_navigation_items.filter(
                    hotel=staff.hotel, is_active=True,
                ).values_list('slug', flat=True)
            )
        else:
            role_navs = set()

        # Staff overrides (additive only)
        override_navs = set(
            staff.allowed_navigation_items.filter(
                hotel=staff.hotel, is_active=True,
            ).values_list('slug', flat=True)
        )

        effective_slugs = tier_navs | role_navs | override_navs
        allowed_nav_items = hotel_nav_items.filter(slug__in=effective_slugs)

    base_payload.update({
        'allowed_navs': list(allowed_nav_items.values_list('slug', flat=True)),
        'navigation_items': NavigationItemSerializer(allowed_nav_items, many=True).data,
    })

    return base_payload


# ---------------------------------------------------------------------------
# Module visibility permission
# ---------------------------------------------------------------------------

class HasNavPermission(BasePermission):
    """
    View-level module visibility gate.

    Usage:
        permission_classes = [IsAuthenticated, HasNavPermission('stock_tracker')]

    This class enforces module VISIBILITY only — it does NOT grant mutation
    authority.  Every mutation endpoint MUST additionally use an action-level
    permission class (CanManage*, IsSuperStaffAdminOrAbove, etc.).
    """

    def __init__(self, required_slug: str):
        self.required_slug = required_slug
        super().__init__()

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        # super_user bypasses module visibility
        if user.is_superuser:
            return True

        perms = resolve_effective_access(user)
        return self.required_slug in perms.get('allowed_navs', [])


# ---------------------------------------------------------------------------
# Tier-based gate permissions
# ---------------------------------------------------------------------------

class IsDjangoSuperUser(BasePermission):
    """
    Platform-level superuser check — user.is_superuser ONLY.
    Use for: hotel provisioning, NavigationItem CUD, cross-hotel data.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsAdminTier(BasePermission):
    """
    Allows super_user + super_staff_admin + staff_admin.
    Replaces the old staff/permissions_superuser.py::IsSuperUser.
    Use for: hotel CRUD by any admin.
    """

    def has_permission(self, request, view):
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


class IsSuperStaffAdminOrAbove(BasePermission):
    """
    Allows super_user + super_staff_admin ONLY.
    staff_admin does NOT pass.
    Use for: structural hotel mutations that only top admins should perform.
    """

    def has_permission(self, request, view):
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')


# ---------------------------------------------------------------------------
# Action-level permission classes (Enforcement Rule 3)
#
# These are MANDATORY for every mutation endpoint.  HasNavPermission alone
# is NEVER sufficient for writes.
# ---------------------------------------------------------------------------

class CanManageRoster(BasePermission):
    """
    Gates roster / attendance CUD operations.
    Required tier: super_staff_admin or above.
    """
    message = "You do not have permission to manage the roster."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True  # reads pass through — visibility handled by HasNavPermission
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')


class CanManageStaff(BasePermission):
    """
    Gates staff creation, deletion, nav assignment, department/role CUD.
    Required tier: super_staff_admin or above.
    """
    message = "You do not have permission to manage staff."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')


class CanManageRooms(BasePermission):
    """
    Gates room CUD operations (create, update, bulk checkout, move).
    Required tier: super_staff_admin or above.
    """
    message = "You do not have permission to manage rooms."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')


class CanManageRoomBookings(BasePermission):
    """
    Gates room-booking CUD operations (confirm, cancel, assign room, etc.).
    Required tier: staff_admin or above.
    """
    message = "You do not have permission to manage room bookings."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


class CanManageRestaurantBookings(BasePermission):
    """
    Gates restaurant-booking CUD operations (create, unseat, delete, assign table).
    Required tier: staff_admin or above.
    """
    message = "You do not have permission to manage restaurant bookings."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


class CanConfigureHotel(BasePermission):
    """
    Gates hotel settings, precheckin/survey config, public page builder CUD.
    Required tier: super_staff_admin or above.
    """
    message = "You do not have permission to configure hotel settings."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'super_staff_admin')


# ---------------------------------------------------------------------------
# Slug-bound HasNavPermission classes for use in static permission_classes
#
# DRF's default get_permissions() calls  [P() for P in permission_classes],
# so HasNavPermission('slug') (an instance) cannot appear in the list.
# These zero-arg subclasses solve that.
# ---------------------------------------------------------------------------

class HasRoomsNav(HasNavPermission):
    def __init__(self): super().__init__('rooms')

class HasRoomBookingsNav(HasNavPermission):
    """Module visibility gate for the room-bookings domain."""
    def __init__(self): super().__init__('room_bookings')

class HasRestaurantBookingsNav(HasNavPermission):
    """Module visibility gate for the restaurant-bookings domain."""
    def __init__(self): super().__init__('restaurant_bookings')

class HasHotelInfoNav(HasNavPermission):
    def __init__(self): super().__init__('hotel_info')

class HasAdminSettingsNav(HasNavPermission):
    def __init__(self): super().__init__('admin_settings')

class HasAttendanceNav(HasNavPermission):
    def __init__(self): super().__init__('attendance')

class HasStaffManagementNav(HasNavPermission):
    def __init__(self): super().__init__('staff_management')

class HasHousekeepingNav(HasNavPermission):
    def __init__(self): super().__init__('housekeeping')

class HasRoomServicesNav(HasNavPermission):
    def __init__(self): super().__init__('room_services')

class HasChatNav(HasNavPermission):
    def __init__(self): super().__init__('chat')

class HasHomeNav(HasNavPermission):
    def __init__(self): super().__init__('home')


# ---------------------------------------------------------------------------
# Action-level: Housekeeping management
# ---------------------------------------------------------------------------

class CanManageHousekeeping(BasePermission):
    """
    Gates housekeeping task CUD and room status mutations.
    Required tier: staff_admin or above (supervisors manage housekeeping).
    Regular housekeeping staff can start/complete their own assigned tasks
    via self-service actions — those bypass this check.
    """
    message = "You do not have permission to manage housekeeping."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')