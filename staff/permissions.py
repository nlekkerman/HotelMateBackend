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
from staff.capability_catalog import (
    CANONICAL_CAPABILITIES,
    DEPARTMENT_PRESET_CAPABILITIES,
    ROLE_PRESET_CAPABILITIES,
    TIER_DEFAULT_CAPABILITIES,
    resolve_capabilities,
)
from staff.module_policy import resolve_module_policy

User = get_user_model()


# ---------------------------------------------------------------------------
# Canonical constants (CANONICAL_NAV_SLUGS imported from staff.nav_catalog)
# ---------------------------------------------------------------------------

TIER_DEFAULT_NAVS = {
    'super_staff_admin': {
        'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
        'housekeeping', 'attendance', 'staff_management',
        'room_services', 'maintenance', 'hotel_info',
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
        department_slug, role_slug,
        allowed_navs (list[str]), navigation_items (list[dict]),
        allowed_capabilities (list[str]),
        rbac (dict[module → {visible, read, actions}])  — Phase 6A
    """
    base_payload = {
        'is_staff': False,
        'is_superuser': bool(getattr(user, 'is_superuser', False)),
        'hotel_slug': None,
        'access_level': None,
        'tier': None,
        'department_slug': None,
        'role_slug': None,
        'allowed_navs': [],
        'navigation_items': [],
        'allowed_capabilities': [],
        'rbac': resolve_module_policy([]),
    }

    if not user or not getattr(user, 'is_authenticated', False):
        return base_payload

    # Django superuser: full access regardless of staff profile.
    if getattr(user, 'is_superuser', False):
        try:
            staff = user.staff_profile
        except (AttributeError, Staff.DoesNotExist):
            staff = None

        hotel_nav_items = (
            NavigationItem.objects.filter(
                hotel=staff.hotel, is_active=True,
            ).select_related('hotel').order_by('display_order', 'name')
            if staff else NavigationItem.objects.none()
        )
        base_payload.update({
            'is_staff': bool(staff),
            'hotel_slug': staff.hotel.slug if staff else None,
            'access_level': staff.access_level if staff else None,
            'tier': 'super_user',
            'department_slug': (
                staff.department.slug
                if staff and staff.department else None
            ),
            'role_slug': (
                staff.role.slug if staff and staff.role else None
            ),
            'allowed_navs': list(
                hotel_nav_items.values_list('slug', flat=True)
            ),
            'navigation_items': NavigationItemSerializer(
                hotel_nav_items, many=True
            ).data,
            'allowed_capabilities': resolve_capabilities(
                tier='super_user',
                role_slug=None,
                department_slug=None,
                is_superuser=True,
            ),
        })
        base_payload['rbac'] = resolve_module_policy(
            base_payload['allowed_capabilities']
        )
        return base_payload

    try:
        staff = user.staff_profile
    except (AttributeError, Staff.DoesNotExist):
        return base_payload

    tier = resolve_tier(user)
    department_slug = staff.department.slug if staff.department else None
    role_slug = staff.role.slug if staff.role else None

    base_payload.update({
        'is_staff': True,
        'hotel_slug': staff.hotel.slug,
        'access_level': staff.access_level,
        'tier': tier,
        'department_slug': department_slug,
        'role_slug': role_slug,
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
        'allowed_capabilities': resolve_capabilities(
            tier=tier,
            role_slug=role_slug,
            department_slug=department_slug,
            is_superuser=False,
        ),
    })
    base_payload['rbac'] = resolve_module_policy(
        base_payload['allowed_capabilities']
    )

    return base_payload


# ---------------------------------------------------------------------------
# Module visibility permission
# ---------------------------------------------------------------------------

class HasNavPermission(BasePermission):
    """
    View-level module visibility gate.

    Usage in get_permissions() (returns instances):
        return [IsAuthenticated(), HasNavPermission('stock_tracker'), IsStaffMember()]

    Usage in static permission_classes (requires zero-arg subclass):
        permission_classes = [IsAuthenticated, HasStockTrackerNav]

    Do NOT use HasNavPermission('slug') in permission_classes — DRF expects
    classes there, not instances.

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


class CanManageMaintenance(BasePermission):
    """
    Gates maintenance ticket status changes, assignment, and deletion.
    Required tier: staff_admin or above.
    """
    message = "You do not have permission to manage maintenance tickets."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


class CanManageRoomServices(BasePermission):
    """
    Gates room-service order status updates and item CUD (staff-side mutations).
    Required tier: staff_admin or above.
    """
    message = "You do not have permission to manage room services."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


class CanManageStaffChat(BasePermission):
    """
    Gates staff-chat moderation actions (delete others' messages/attachments).
    Required tier: staff_admin or above.
    Replaces the old role.slug in ['manager', 'admin'] checks.
    """
    message = "You do not have permission to manage staff chat."

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        tier = resolve_tier(request.user)
        return _tier_at_least(tier, 'staff_admin')


# ---------------------------------------------------------------------------
# Additional slug-bound HasNavPermission subclasses (missing from above)
# ---------------------------------------------------------------------------

class HasMaintenanceNav(HasNavPermission):
    """Module visibility gate for the maintenance domain."""
    def __init__(self): super().__init__('maintenance')


# ---------------------------------------------------------------------------
# Capability-based action permission (Phase 5)
#
# This class is the capability-first enforcement primitive required by
# hotelmates_auth_contract_v1.md §4. Endpoints declare a required capability
# slug; the resolved `allowed_capabilities` list from
# resolve_effective_access() is the sole source of truth at runtime.
#
# Not wired into endpoints yet — Phase 5b migrates the legacy role-slug and
# department-slug callsites to this class.
# ---------------------------------------------------------------------------

class HasCapability(BasePermission):
    """
    View-level capability gate.

    Usage in get_permissions() (returns instances):
        return [IsAuthenticated(), HasCapability('chat.message.moderate')]

    Usage in static permission_classes (requires zero-arg subclass — define
    one in the consuming app and assign `required_capability`):
        class CanModerateChat(HasCapability):
            required_capability = 'chat.message.moderate'
        permission_classes = [IsAuthenticated, CanModerateChat]

    Behavior:
    - Safe methods (GET/HEAD/OPTIONS) pass through by default; capability
      enforcement is for mutating / non-safe actions (contract §4 rule 14).
      Set ``safe_methods_bypass = False`` on a subclass to enforce the
      capability on reads as well (e.g. module visibility / read gates
      whose whole purpose is to gate GET).
    - Django superusers always pass.
    - Unauthenticated requests always fail.
    - Unknown capability slugs always fail closed (the capability must be
      registered in staff.capability_catalog.CANONICAL_CAPABILITIES).
    """
    message = "You do not have the required capability for this action."
    required_capability: str | None = None
    safe_methods_bypass: bool = True

    def __init__(self, required_capability: str | None = None):
        if required_capability is not None:
            self.required_capability = required_capability
        super().__init__()

    def has_permission(self, request, view):
        capability = self.required_capability
        if capability is None or capability not in CANONICAL_CAPABILITIES:
            # Misconfigured endpoint — fail closed.
            return False

        user = request.user
        if not user or not getattr(user, 'is_authenticated', False):
            return False

        if getattr(user, 'is_superuser', False):
            return True

        if (
            self.safe_methods_bypass
            and request.method in ('GET', 'HEAD', 'OPTIONS')
        ):
            return True

        perms = resolve_effective_access(user)
        return capability in perms.get('allowed_capabilities', [])


def has_capability(user, capability: str) -> bool:
    """
    Imperative capability check for use inside view bodies, services, and
    notification routing where a permission class is not appropriate.

    Returns True iff:
        - `capability` is a canonical capability, AND
        - the user is authenticated, AND
        - the user is a Django superuser OR the capability appears in their
          resolved `allowed_capabilities`.

    Fails closed on unknown capabilities and on missing users.
    """
    if not capability or capability not in CANONICAL_CAPABILITIES:
        return False
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    perms = resolve_effective_access(user)
    return capability in perms.get('allowed_capabilities', [])


def staff_with_capability(hotel, capability: str):
    """
    Return a ``Staff`` queryset scoped to ``hotel`` of every staff member
    who, per the capability catalog preset maps, currently holds
    ``capability``.

    Expansion rule (matches ``resolve_capabilities``):
        A staff row S has capability C iff any of:
          - S.access_level is a tier whose TIER_DEFAULT_CAPABILITIES includes C
          - S.role.slug is a key in ROLE_PRESET_CAPABILITIES whose bundle includes C
          - S.department.slug is a key in DEPARTMENT_PRESET_CAPABILITIES whose bundle includes C

    Django superusers are not expanded here; this helper targets staff
    routing/eligibility queries (notifications, "who can respond"). Callers
    that need superuser inclusion should union it explicitly.

    Fail-closed: unknown capability slugs return an empty queryset.
    Active-only: filters ``is_active=True`` so deactivated rows never match.
    """
    from django.db.models import Q

    if not capability or capability not in CANONICAL_CAPABILITIES:
        return Staff.objects.none()

    tiers = [
        tier for tier, caps in TIER_DEFAULT_CAPABILITIES.items()
        if capability in caps
    ]
    role_slugs = [
        slug for slug, caps in ROLE_PRESET_CAPABILITIES.items()
        if capability in caps
    ]
    dept_slugs = [
        slug for slug, caps in DEPARTMENT_PRESET_CAPABILITIES.items()
        if capability in caps
    ]

    q = Q()
    matched = False
    if tiers:
        q |= Q(access_level__in=tiers)
        matched = True
    if role_slugs:
        q |= Q(role__slug__in=role_slugs)
        matched = True
    if dept_slugs:
        q |= Q(department__slug__in=dept_slugs)
        matched = True

    if not matched:
        return Staff.objects.none()

    return Staff.objects.filter(hotel=hotel, is_active=True).filter(q).distinct()


# ---------------------------------------------------------------------------
# Bookings capability permission classes (Phase 6A)
#
# These are the single source of truth for endpoint enforcement in the
# bookings module. They must stay in lock-step with
# staff.module_policy.BOOKINGS_ACTIONS so the frontend rbac object and the
# backend enforcement derive from the same capability slugs.
#
# Read/visibility gates (CanViewBookings, CanReadBookings) set
# safe_methods_bypass = False so GETs are actually gated. Mutation gates
# inherit the default (pass GET, enforce non-safe methods) — chain them
# with a read/view gate when the endpoint also serves GET.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402  (keep import grouped)
    BOOKING_CONFIG_MANAGE,
    BOOKING_GUEST_COMMUNICATE,
    BOOKING_MODULE_VIEW,
    BOOKING_OVERRIDE_SUPERVISE,
    BOOKING_RECORD_CANCEL,
    BOOKING_RECORD_READ,
    BOOKING_RECORD_UPDATE,
    BOOKING_ROOM_ASSIGN,
    BOOKING_STAY_CHECKIN,
    BOOKING_STAY_CHECKOUT,
)


class CanViewBookings(HasCapability):
    """Module visibility gate for the bookings module (all methods)."""
    required_capability = BOOKING_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the bookings module."


class CanReadBookings(HasCapability):
    """Read access gate for booking records (all methods)."""
    required_capability = BOOKING_RECORD_READ
    safe_methods_bypass = False
    message = "You do not have permission to read bookings."


class CanUpdateBooking(HasCapability):
    required_capability = BOOKING_RECORD_UPDATE
    message = "You do not have permission to update bookings."


class CanCancelBooking(HasCapability):
    required_capability = BOOKING_RECORD_CANCEL
    message = "You do not have permission to cancel bookings."


class CanAssignBookingRoom(HasCapability):
    required_capability = BOOKING_ROOM_ASSIGN
    message = "You do not have permission to assign booking rooms."


class CanCheckInBooking(HasCapability):
    required_capability = BOOKING_STAY_CHECKIN
    message = "You do not have permission to check bookings in."


class CanCheckOutBooking(HasCapability):
    required_capability = BOOKING_STAY_CHECKOUT
    message = "You do not have permission to check bookings out."


class CanCommunicateWithBookingGuest(HasCapability):
    required_capability = BOOKING_GUEST_COMMUNICATE
    message = (
        "You do not have permission to send guest booking communications."
    )


class CanSuperviseBooking(HasCapability):
    """Supervisor overrides (acknowledge overstay, force checkin/checkout,
    override conflicts, modify locked bookings)."""
    required_capability = BOOKING_OVERRIDE_SUPERVISE
    message = "You do not have permission to override bookings."


class CanManageBookingConfig(HasCapability):
    required_capability = BOOKING_CONFIG_MANAGE
    message = "You do not have permission to manage booking configuration."


# ---------------------------------------------------------------------------
# Rooms capability permission classes (Phase 6B.1)
#
# Single source of truth for endpoint enforcement in the rooms module.
# Must stay in lock-step with staff.module_policy MODULE_POLICY['rooms']
# so the frontend rbac.rooms object and backend enforcement derive from
# the same capability slugs.
#
# Read/visibility gates (CanViewRooms, CanRead*) set safe_methods_bypass =
# False so GETs are gated. Mutation gates inherit the default (pass GET,
# enforce non-safe methods) and are always chained with CanViewRooms plus
# the relevant read gate when the endpoint also serves GET.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    ROOM_CHECKOUT_BULK,
    ROOM_CHECKOUT_DESTRUCTIVE,
    ROOM_INSPECTION_PERFORM,
    ROOM_INVENTORY_CREATE,
    ROOM_INVENTORY_DELETE,
    ROOM_INVENTORY_READ,
    ROOM_INVENTORY_UPDATE,
    ROOM_MAINTENANCE_CLEAR,
    ROOM_MAINTENANCE_FLAG,
    ROOM_MEDIA_MANAGE,
    ROOM_MEDIA_READ,
    ROOM_MODULE_VIEW,
    ROOM_OUT_OF_ORDER_SET,
    ROOM_STATUS_READ,
    ROOM_STATUS_TRANSITION,
    ROOM_TYPE_MANAGE,
    ROOM_TYPE_READ,
)


class CanViewRooms(HasCapability):
    """Module visibility gate for the rooms module (all methods)."""
    required_capability = ROOM_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the rooms module."


class CanReadRoomInventory(HasCapability):
    required_capability = ROOM_INVENTORY_READ
    safe_methods_bypass = False
    message = "You do not have permission to read room inventory."


class CanCreateRoomInventory(HasCapability):
    required_capability = ROOM_INVENTORY_CREATE
    message = "You do not have permission to create rooms."


class CanUpdateRoomInventory(HasCapability):
    required_capability = ROOM_INVENTORY_UPDATE
    message = "You do not have permission to update rooms."


class CanDeleteRoomInventory(HasCapability):
    required_capability = ROOM_INVENTORY_DELETE
    message = "You do not have permission to delete rooms."


class CanReadRoomTypes(HasCapability):
    required_capability = ROOM_TYPE_READ
    safe_methods_bypass = False
    message = "You do not have permission to read room types."


class CanManageRoomTypes(HasCapability):
    required_capability = ROOM_TYPE_MANAGE
    message = "You do not have permission to manage room types."


class CanReadRoomMedia(HasCapability):
    required_capability = ROOM_MEDIA_READ
    safe_methods_bypass = False
    message = "You do not have permission to read room media."


class CanManageRoomMedia(HasCapability):
    required_capability = ROOM_MEDIA_MANAGE
    message = "You do not have permission to manage room media."


class CanReadRoomStatus(HasCapability):
    required_capability = ROOM_STATUS_READ
    safe_methods_bypass = False
    message = "You do not have permission to read room status."


class CanTransitionRoomStatus(HasCapability):
    required_capability = ROOM_STATUS_TRANSITION
    message = "You do not have permission to transition room status."


class CanInspectRoom(HasCapability):
    required_capability = ROOM_INSPECTION_PERFORM
    message = "You do not have permission to inspect rooms."


class CanFlagRoomMaintenance(HasCapability):
    required_capability = ROOM_MAINTENANCE_FLAG
    message = "You do not have permission to flag room maintenance."


class CanClearRoomMaintenance(HasCapability):
    required_capability = ROOM_MAINTENANCE_CLEAR
    message = "You do not have permission to clear room maintenance."


class CanSetRoomOutOfOrder(HasCapability):
    required_capability = ROOM_OUT_OF_ORDER_SET
    message = "You do not have permission to set a room out of order."


class CanBulkCheckoutRooms(HasCapability):
    required_capability = ROOM_CHECKOUT_BULK
    message = "You do not have permission to bulk-check-out rooms."


class CanDestructiveCheckoutRooms(HasCapability):
    required_capability = ROOM_CHECKOUT_DESTRUCTIVE
    message = (
        "You do not have permission to perform destructive room checkout."
    )


# ---------------------------------------------------------------------------
# Housekeeping capability permission classes (Phase 6C)
#
# Single source of truth for endpoint enforcement in the housekeeping
# module. Stays in lock-step with MODULE_POLICY['housekeeping'] so the
# frontend rbac.housekeeping object and backend enforcement derive from
# the same capability slugs.
#
# Read/visibility gates set safe_methods_bypass = False so GETs are
# gated. Mutation gates inherit the default (pass GET, enforce non-safe
# methods) and are chained on top of CanViewHousekeepingModule by the
# views.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    HOUSEKEEPING_DASHBOARD_READ,
    HOUSEKEEPING_MODULE_VIEW,
    HOUSEKEEPING_ROOM_STATUS_FRONT_DESK,
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ,
    HOUSEKEEPING_ROOM_STATUS_OVERRIDE,
    HOUSEKEEPING_ROOM_STATUS_TRANSITION,
    HOUSEKEEPING_TASK_ASSIGN,
    HOUSEKEEPING_TASK_CANCEL,
    HOUSEKEEPING_TASK_CREATE,
    HOUSEKEEPING_TASK_DELETE,
    HOUSEKEEPING_TASK_EXECUTE,
    HOUSEKEEPING_TASK_READ,
    HOUSEKEEPING_TASK_UPDATE,
)


class CanViewHousekeepingModule(HasCapability):
    """Module visibility gate for the housekeeping module (all methods)."""
    required_capability = HOUSEKEEPING_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the housekeeping module."


class CanReadHousekeepingDashboard(HasCapability):
    required_capability = HOUSEKEEPING_DASHBOARD_READ
    safe_methods_bypass = False
    message = "You do not have permission to read the housekeeping dashboard."


class CanReadHousekeepingTasks(HasCapability):
    required_capability = HOUSEKEEPING_TASK_READ
    safe_methods_bypass = False
    message = "You do not have permission to read housekeeping tasks."


class CanCreateHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_CREATE
    message = "You do not have permission to create housekeeping tasks."


class CanUpdateHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_UPDATE
    message = "You do not have permission to update housekeeping tasks."


class CanDeleteHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_DELETE
    message = "You do not have permission to delete housekeeping tasks."


class CanAssignHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_ASSIGN
    message = "You do not have permission to assign housekeeping tasks."


class CanExecuteHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_EXECUTE
    message = "You do not have permission to execute housekeeping tasks."


class CanCancelHousekeepingTask(HasCapability):
    required_capability = HOUSEKEEPING_TASK_CANCEL
    message = "You do not have permission to cancel housekeeping tasks."


class CanTransitionHousekeepingRoomStatus(HasCapability):
    required_capability = HOUSEKEEPING_ROOM_STATUS_TRANSITION
    message = (
        "You do not have permission to transition housekeeping room status."
    )


class CanFrontDeskHousekeepingRoomStatus(HasCapability):
    required_capability = HOUSEKEEPING_ROOM_STATUS_FRONT_DESK
    message = (
        "You do not have permission to perform front-desk room status changes."
    )


class CanOverrideHousekeepingRoomStatus(HasCapability):
    required_capability = HOUSEKEEPING_ROOM_STATUS_OVERRIDE
    message = (
        "You do not have permission to override housekeeping room status."
    )


class CanReadHousekeepingStatusHistory(HasCapability):
    required_capability = HOUSEKEEPING_ROOM_STATUS_HISTORY_READ
    safe_methods_bypass = False
    message = (
        "You do not have permission to read housekeeping room status history."
    )



# ---------------------------------------------------------------------------
# Maintenance capability permission classes (Phase 6D.1)
#
# Single source of truth for endpoint enforcement in the maintenance
# module. Stays in lock-step with MODULE_POLICY['maintenance'] so the
# frontend rbac.maintenance object and backend enforcement derive from
# the same capability slugs.
#
# Read/visibility gates set safe_methods_bypass = False so GETs are
# gated. Mutation gates inherit the default (pass GET, enforce non-safe
# methods) and are chained on top of CanViewMaintenanceModule by the
# views.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    MAINTENANCE_COMMENT_CREATE,
    MAINTENANCE_COMMENT_MODERATE,
    MAINTENANCE_MODULE_VIEW,
    MAINTENANCE_PHOTO_DELETE,
    MAINTENANCE_PHOTO_UPLOAD,
    MAINTENANCE_REQUEST_ACCEPT,
    MAINTENANCE_REQUEST_CLOSE,
    MAINTENANCE_REQUEST_CREATE,
    MAINTENANCE_REQUEST_DELETE,
    MAINTENANCE_REQUEST_READ,
    MAINTENANCE_REQUEST_REASSIGN,
    MAINTENANCE_REQUEST_REOPEN,
    MAINTENANCE_REQUEST_RESOLVE,
    MAINTENANCE_REQUEST_UPDATE,
)


class CanViewMaintenanceModule(HasCapability):
    """Module visibility gate for the maintenance module (all methods)."""
    required_capability = MAINTENANCE_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the maintenance module."


class CanReadMaintenanceRequests(HasCapability):
    required_capability = MAINTENANCE_REQUEST_READ
    safe_methods_bypass = False
    message = "You do not have permission to read maintenance requests."


class CanCreateMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_CREATE
    message = "You do not have permission to create maintenance requests."


class CanAcceptMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_ACCEPT
    message = "You do not have permission to accept maintenance requests."


class CanResolveMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_RESOLVE
    message = "You do not have permission to resolve maintenance requests."


class CanUpdateMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_UPDATE
    message = "You do not have permission to update maintenance requests."


class CanReassignMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_REASSIGN
    message = "You do not have permission to reassign maintenance requests."


class CanReopenMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_REOPEN
    message = "You do not have permission to reopen maintenance requests."


class CanCloseMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_CLOSE
    message = "You do not have permission to close maintenance requests."


class CanDeleteMaintenanceRequest(HasCapability):
    required_capability = MAINTENANCE_REQUEST_DELETE
    message = "You do not have permission to delete maintenance requests."


class CanCreateMaintenanceComment(HasCapability):
    required_capability = MAINTENANCE_COMMENT_CREATE
    message = "You do not have permission to create maintenance comments."


class CanModerateMaintenanceComment(HasCapability):
    required_capability = MAINTENANCE_COMMENT_MODERATE
    message = "You do not have permission to moderate maintenance comments."


class CanUploadMaintenancePhoto(HasCapability):
    required_capability = MAINTENANCE_PHOTO_UPLOAD
    message = "You do not have permission to upload maintenance photos."


class CanDeleteMaintenancePhoto(HasCapability):
    required_capability = MAINTENANCE_PHOTO_DELETE
    message = "You do not have permission to delete maintenance photos."

# ---------------------------------------------------------------------------
# Staff Management capability permission classes (Phase 6E.1)
#
# Single source of truth for endpoint enforcement in the staff-management
# module. Stays in lock-step with MODULE_POLICY['staff_management'] so the
# frontend rbac.staff_management object and backend enforcement derive
# from the same capability slugs.
#
# Read/visibility gates set safe_methods_bypass = False so GETs are
# gated. Mutation gates inherit the default (pass GET, enforce non-safe
# methods) and are chained on top of CanViewStaffManagementModule by the
# views.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN,
    STAFF_MANAGEMENT_AUTHORITY_SUPERVISE,
    STAFF_MANAGEMENT_AUTHORITY_VIEW,
    STAFF_MANAGEMENT_DEPARTMENT_MANAGE,
    STAFF_MANAGEMENT_DEPARTMENT_READ,
    STAFF_MANAGEMENT_MODULE_VIEW,
    STAFF_MANAGEMENT_PENDING_REGISTRATION_READ,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT,
    STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ,
    STAFF_MANAGEMENT_ROLE_MANAGE,
    STAFF_MANAGEMENT_ROLE_READ,
    STAFF_MANAGEMENT_STAFF_CREATE,
    STAFF_MANAGEMENT_STAFF_DEACTIVATE,
    STAFF_MANAGEMENT_STAFF_DELETE,
    STAFF_MANAGEMENT_STAFF_READ,
    STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE,
    STAFF_MANAGEMENT_USER_READ,
)


class CanViewStaffManagementModule(HasCapability):
    """Module visibility gate for the staff-management module
    (all methods)."""
    required_capability = STAFF_MANAGEMENT_MODULE_VIEW
    safe_methods_bypass = False
    message = (
        "You do not have permission to view the staff management module."
    )


class CanReadStaff(HasCapability):
    required_capability = STAFF_MANAGEMENT_STAFF_READ
    safe_methods_bypass = False
    message = "You do not have permission to read staff."


class CanReadStaffUsers(HasCapability):
    required_capability = STAFF_MANAGEMENT_USER_READ
    safe_methods_bypass = False
    message = "You do not have permission to read users."


class CanReadPendingRegistrations(HasCapability):
    required_capability = STAFF_MANAGEMENT_PENDING_REGISTRATION_READ
    safe_methods_bypass = False
    message = "You do not have permission to read pending registrations."


class CanCreateStaff(HasCapability):
    required_capability = STAFF_MANAGEMENT_STAFF_CREATE
    message = "You do not have permission to create staff."


class CanUpdateStaffProfile(HasCapability):
    required_capability = STAFF_MANAGEMENT_STAFF_UPDATE_PROFILE
    message = "You do not have permission to update staff profiles."


class CanDeactivateStaff(HasCapability):
    required_capability = STAFF_MANAGEMENT_STAFF_DEACTIVATE
    message = "You do not have permission to deactivate staff."


class CanDeleteStaff(HasCapability):
    required_capability = STAFF_MANAGEMENT_STAFF_DELETE
    message = "You do not have permission to delete staff."


class CanViewStaffAuthority(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view staff authority."


class CanAssignStaffRole(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_ROLE_ASSIGN
    message = "You do not have permission to assign staff roles."


class CanAssignStaffDepartment(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_DEPARTMENT_ASSIGN
    message = "You do not have permission to assign staff departments."


class CanAssignStaffAccessLevel(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_ACCESS_LEVEL_ASSIGN
    message = "You do not have permission to assign staff access levels."


class CanAssignStaffNavigation(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_NAV_ASSIGN
    message = "You do not have permission to assign staff navigation."


class CanSuperviseStaffAuthority(HasCapability):
    required_capability = STAFF_MANAGEMENT_AUTHORITY_SUPERVISE
    message = "You do not have permission to supervise staff authority."


class CanReadStaffRoles(HasCapability):
    required_capability = STAFF_MANAGEMENT_ROLE_READ
    safe_methods_bypass = False
    message = "You do not have permission to read staff roles."


class CanManageStaffRoles(HasCapability):
    required_capability = STAFF_MANAGEMENT_ROLE_MANAGE
    message = "You do not have permission to manage staff roles."


class CanReadStaffDepartments(HasCapability):
    required_capability = STAFF_MANAGEMENT_DEPARTMENT_READ
    safe_methods_bypass = False
    message = "You do not have permission to read staff departments."


class CanManageStaffDepartments(HasCapability):
    required_capability = STAFF_MANAGEMENT_DEPARTMENT_MANAGE
    message = "You do not have permission to manage staff departments."


class CanReadRegistrationPackages(HasCapability):
    required_capability = STAFF_MANAGEMENT_REGISTRATION_PACKAGE_READ
    safe_methods_bypass = False
    message = "You do not have permission to read registration packages."


class CanCreateRegistrationPackages(HasCapability):
    required_capability = STAFF_MANAGEMENT_REGISTRATION_PACKAGE_CREATE
    message = "You do not have permission to create registration packages."


class CanEmailRegistrationPackages(HasCapability):
    required_capability = STAFF_MANAGEMENT_REGISTRATION_PACKAGE_EMAIL
    message = "You do not have permission to email registration packages."


class CanPrintRegistrationPackages(HasCapability):
    required_capability = STAFF_MANAGEMENT_REGISTRATION_PACKAGE_PRINT
    message = "You do not have permission to print registration packages."


# ---------------------------------------------------------------------------
# Staff-management anti-escalation helpers (Phase 6E.1)
#
# Every authority-mutating endpoint composes these helpers in this
# order (see views.py for call sites):
#
#   1. assert_not_self_authority    — requester != target (authority fields)
#   2. assert_same_hotel             — requester.hotel == target.hotel
#   3. assert_access_level_allowed   — supervise OR strict less-than
#   4. assert_nav_subset             — supervise OR requested ⊆ requester
#   5. assert_role_department_ceiling — supervise OR role∪dept caps ⊆ requester
#
# Django superusers bypass every helper (platform-admin contract).
# ---------------------------------------------------------------------------

# Access-level strict-less-than ordering (lower index = higher authority).
# super_user > super_staff_admin > staff_admin > regular_staff.
_ACCESS_LEVEL_ORDER: tuple[str, ...] = (
    'super_user',
    'super_staff_admin',
    'staff_admin',
    'regular_staff',
)


def _access_level_rank(access_level: str | None) -> int:
    """Lower rank = higher authority. Unknown → max (lowest authority)."""
    try:
        return _ACCESS_LEVEL_ORDER.index(access_level)
    except (ValueError, TypeError):
        return len(_ACCESS_LEVEL_ORDER)


def assert_not_self_authority(requester_user, target_staff) -> str | None:
    """Rule 1 — requester may never mutate authority on their own row."""
    if getattr(requester_user, 'is_superuser', False):
        return None
    target_user = getattr(target_staff, 'user', None)
    if target_user is not None and target_user == requester_user:
        return "You cannot change authority fields on your own profile."
    return None


def assert_same_hotel(requester_user, target_staff) -> str | None:
    """Rule 3 — cross-hotel authority assignment is forbidden except for
    platform superusers."""
    if getattr(requester_user, 'is_superuser', False):
        return None
    requester_staff = getattr(requester_user, 'staff_profile', None)
    if requester_staff is None:
        return "You must be a staff member of this hotel."
    if getattr(target_staff, 'hotel_id', None) != requester_staff.hotel_id:
        return "Cannot mutate authority for a staff member in another hotel."
    return None


def _has_supervise(capabilities) -> bool:
    return STAFF_MANAGEMENT_AUTHORITY_SUPERVISE in (capabilities or ())


def assert_access_level_allowed(
    requester_user,
    requester_capabilities,
    requester_access_level: str | None,
    target_access_level: str | None,
) -> str | None:
    """Rule 4 — without supervise, requester may only assign strictly
    below their own access level."""
    if getattr(requester_user, 'is_superuser', False):
        return None
    if _has_supervise(requester_capabilities):
        return None
    requester_rank = _access_level_rank(requester_access_level)
    target_rank = _access_level_rank(target_access_level)
    # "strictly below" → target has a higher rank number than requester.
    if target_rank <= requester_rank:
        return (
            "You cannot assign an equal or higher access level without "
            "the supervise capability."
        )
    return None


def assert_nav_subset(
    requester_user,
    requester_capabilities,
    requester_navs,
    requested_navs,
) -> str | None:
    """Rule 5 — without supervise, assigned nav slugs must be a subset of
    requester's own effective navs."""
    if getattr(requester_user, 'is_superuser', False):
        return None
    if _has_supervise(requester_capabilities):
        return None
    requester_set = set(requester_navs or [])
    requested_set = set(requested_navs or [])
    extras = requested_set - requester_set
    if extras:
        return (
            "You cannot assign navigation slugs beyond your own "
            "effective set without the supervise capability."
        )
    return None


def _caps_for_role_slug(role_slug: str | None) -> set[str]:
    if not role_slug:
        return set()
    return set(ROLE_PRESET_CAPABILITIES.get(role_slug, frozenset()))


def _caps_for_department_slug(department_slug: str | None) -> set[str]:
    if not department_slug:
        return set()
    return set(DEPARTMENT_PRESET_CAPABILITIES.get(department_slug, frozenset()))


def assert_role_department_ceiling(
    requester_user,
    requester_capabilities,
    target_role_slug: str | None,
    target_department_slug: str | None,
) -> str | None:
    """Rule 6 — without supervise, the union of capabilities granted by
    the target role + department presets must not exceed the requester's
    own resolved capability set."""
    if getattr(requester_user, 'is_superuser', False):
        return None
    if _has_supervise(requester_capabilities):
        return None
    granted = (
        _caps_for_role_slug(target_role_slug)
        | _caps_for_department_slug(target_department_slug)
    )
    requester_set = set(requester_capabilities or ())
    overshoot = granted - requester_set
    if overshoot:
        return (
            "You cannot assign a role/department whose preset grants "
            "capabilities beyond your own without the supervise capability."
        )
    return None


# ---------------------------------------------------------------------------
# Guests capability permission classes (Wave 1)
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    GUEST_RECORD_READ,
    GUEST_RECORD_UPDATE,
    HOTEL_INFO_CATEGORY_MANAGE,
    HOTEL_INFO_CATEGORY_READ,
    HOTEL_INFO_ENTRY_CREATE,
    HOTEL_INFO_ENTRY_DELETE,
    HOTEL_INFO_ENTRY_READ,
    HOTEL_INFO_ENTRY_UPDATE,
    HOTEL_INFO_MODULE_VIEW,
    HOTEL_INFO_QR_GENERATE,
    HOTEL_INFO_QR_READ,
)


class CanReadGuests(HasCapability):
    required_capability = GUEST_RECORD_READ
    safe_methods_bypass = False
    message = "You do not have permission to read guest records."


class CanUpdateGuests(HasCapability):
    required_capability = GUEST_RECORD_UPDATE
    message = "You do not have permission to update guest records."


# ---------------------------------------------------------------------------
# Hotel Info capability permission classes (Wave 1)
# ---------------------------------------------------------------------------

class CanViewHotelInfoModule(HasCapability):
    required_capability = HOTEL_INFO_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the hotel info module."


class CanReadHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_READ
    safe_methods_bypass = False
    message = "You do not have permission to read hotel info entries."


class CanCreateHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_CREATE
    message = "You do not have permission to create hotel info entries."


class CanUpdateHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_UPDATE
    message = "You do not have permission to update hotel info entries."


class CanDeleteHotelInfo(HasCapability):
    required_capability = HOTEL_INFO_ENTRY_DELETE
    message = "You do not have permission to delete hotel info entries."


class CanReadHotelInfoCategory(HasCapability):
    required_capability = HOTEL_INFO_CATEGORY_READ
    safe_methods_bypass = False
    message = "You do not have permission to read hotel info categories."


class CanManageHotelInfoCategory(HasCapability):
    required_capability = HOTEL_INFO_CATEGORY_MANAGE
    message = "You do not have permission to manage hotel info categories."


class CanReadHotelInfoQR(HasCapability):
    required_capability = HOTEL_INFO_QR_READ
    safe_methods_bypass = False
    message = "You do not have permission to read hotel info QR codes."


class CanGenerateHotelInfoQR(HasCapability):
    required_capability = HOTEL_INFO_QR_GENERATE
    message = "You do not have permission to generate hotel info QR codes."








# ---------------------------------------------------------------------------
# Guest chat (chat app) capability permission classes (Wave 2A)
#
# Single source of truth for endpoint enforcement in the guest-chat
# module. Stays in lock-step with staff.module_policy MODULE_POLICY['chat'].
# Read/visibility gates set safe_methods_bypass = False so GETs are
# gated. Mutation gates inherit the default (pass GET, enforce non-safe
# methods) and are chained on top of CanViewChatModule by the views.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    CHAT_ATTACHMENT_DELETE,
    CHAT_ATTACHMENT_UPLOAD,
    CHAT_CONVERSATION_ASSIGN,
    CHAT_CONVERSATION_READ,
    CHAT_GUEST_RESPOND,
    CHAT_MESSAGE_MODERATE,
    CHAT_MESSAGE_SEND,
    CHAT_MODULE_VIEW,
)


class CanViewChatModule(HasCapability):
    """Module visibility gate for the guest-chat module (all methods)."""
    required_capability = CHAT_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the chat module."


class CanReadChatConversation(HasCapability):
    """Read access gate for guest-chat conversations / messages."""
    required_capability = CHAT_CONVERSATION_READ
    safe_methods_bypass = False
    message = "You do not have permission to read guest chat conversations."


class CanSendChatMessage(HasCapability):
    required_capability = CHAT_MESSAGE_SEND
    message = "You do not have permission to send guest chat messages."


class CanModerateChatMessage(HasCapability):
    required_capability = CHAT_MESSAGE_MODERATE
    message = "You do not have permission to moderate guest chat messages."


class CanUploadChatAttachment(HasCapability):
    required_capability = CHAT_ATTACHMENT_UPLOAD
    message = "You do not have permission to upload guest chat attachments."


class CanDeleteChatAttachment(HasCapability):
    required_capability = CHAT_ATTACHMENT_DELETE
    message = "You do not have permission to delete guest chat attachments."


class CanAssignChatConversation(HasCapability):
    required_capability = CHAT_CONVERSATION_ASSIGN
    message = "You do not have permission to assign guest chat conversations."


class CanRespondToGuest(HasCapability):
    required_capability = CHAT_GUEST_RESPOND
    message = "You do not have permission to respond to guest chat traffic."

# ---------------------------------------------------------------------------
# Staff-to-staff chat (staff_chat app) capability permission classes
# (Wave 2C)
#
# Single source of truth for endpoint enforcement in the staff-chat
# module. Stays in lock-step with staff.module_policy MODULE_POLICY['staff_chat'].
# Module visibility / read gates set safe_methods_bypass = False so GETs
# are gated. Mutation gates inherit the default (pass GET, enforce
# non-safe methods) and are chained on top of CanViewStaffChatModule by
# the views. No role / nav / tier checks.
# ---------------------------------------------------------------------------

from staff.capability_catalog import (  # noqa: E402
    STAFF_CHAT_ATTACHMENT_DELETE,
    STAFF_CHAT_ATTACHMENT_UPLOAD,
    STAFF_CHAT_CONVERSATION_CREATE,
    STAFF_CHAT_CONVERSATION_DELETE,
    STAFF_CHAT_CONVERSATION_MODERATE,
    STAFF_CHAT_CONVERSATION_READ,
    STAFF_CHAT_MESSAGE_SEND,
    STAFF_CHAT_MODULE_VIEW,
    STAFF_CHAT_REACTION_MANAGE,
)


class CanViewStaffChatModule(HasCapability):
    """Module visibility gate for the staff-chat module (all methods)."""
    required_capability = STAFF_CHAT_MODULE_VIEW
    safe_methods_bypass = False
    message = "You do not have permission to view the staff chat module."


class CanReadStaffChatConversation(HasCapability):
    """Read access gate for staff-chat conversations / messages."""
    required_capability = STAFF_CHAT_CONVERSATION_READ
    safe_methods_bypass = False
    message = "You do not have permission to read staff chat conversations."


class CanCreateStaffChatConversation(HasCapability):
    required_capability = STAFF_CHAT_CONVERSATION_CREATE
    message = "You do not have permission to create staff chat conversations."


class CanDeleteStaffChatConversation(HasCapability):
    required_capability = STAFF_CHAT_CONVERSATION_DELETE
    message = "You do not have permission to delete staff chat conversations."


class CanSendStaffChatMessage(HasCapability):
    required_capability = STAFF_CHAT_MESSAGE_SEND
    message = "You do not have permission to send staff chat messages."


class CanModerateStaffChatMessage(HasCapability):
    required_capability = STAFF_CHAT_CONVERSATION_MODERATE
    message = "You do not have permission to moderate staff chat messages."


class CanUploadStaffChatAttachment(HasCapability):
    required_capability = STAFF_CHAT_ATTACHMENT_UPLOAD
    message = "You do not have permission to upload staff chat attachments."


class CanDeleteStaffChatAttachment(HasCapability):
    required_capability = STAFF_CHAT_ATTACHMENT_DELETE
    message = "You do not have permission to delete staff chat attachments."


class CanManageStaffChatReaction(HasCapability):
    required_capability = STAFF_CHAT_REACTION_MANAGE
    message = "You do not have permission to manage staff chat reactions."