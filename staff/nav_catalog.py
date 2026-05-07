"""
Canonical navigation catalog for HotelMate.

This module is the SINGLE SOURCE OF TRUTH for:
- CANONICAL_NAV_SLUGS: the complete set of valid navigation slugs
- CANONICAL_NAV_ITEMS: the full definition list (slug, name, path, description, display_order)

All consumers (permissions, signals, management commands) MUST import from here.
Do NOT define nav constants elsewhere.
"""

CANONICAL_NAV_SLUGS = frozenset({
    'home', 'rooms', 'room_bookings', 'restaurant_bookings', 'chat',
    'housekeeping', 'attendance', 'staff_management',
    'room_services', 'maintenance', 'hotel_info',
    'admin_settings',
})

CANONICAL_NAV_ITEMS = [
    {
        'slug': 'home',
        'name': 'Home',
        'path': '/',
        'description': 'Dashboard and overview',
        'display_order': 1,
    },
    {
        'slug': 'chat',
        'name': 'Chat',
        'path': '/chat',
        'description': 'Staff communication',
        'display_order': 2,
    },
    {
        'slug': 'rooms',
        'name': 'Rooms',
        'path': '/rooms',
        'description': 'Room management',
        'display_order': 3,
    },
    {
        'slug': 'room_bookings',
        'name': 'Room Bookings',
        'path': '/room-bookings',
        'description': 'Accommodation booking management',
        'display_order': 4,
    },
    {
        'slug': 'restaurant_bookings',
        'name': 'Restaurant Bookings',
        'path': '/restaurant-bookings',
        'description': 'Dining reservation management',
        'display_order': 5,
    },
    {
        'slug': 'housekeeping',
        'name': 'Housekeeping',
        'path': '/housekeeping',
        'description': 'Housekeeping task management',
        'display_order': 6,
    },
    {
        'slug': 'maintenance',
        'name': 'Maintenance',
        'path': '/maintenance',
        'description': 'Maintenance requests',
        'display_order': 7,
    },
    {
        'slug': 'attendance',
        'name': 'Attendance',
        'path': '/attendance',
        'description': 'Staff scheduling and attendance',
        'display_order': 8,
    },
    {
        'slug': 'staff_management',
        'name': 'Staff Management',
        'path': '/staff-management',
        'description': 'Staff administration',
        'display_order': 9,
    },
    {
        'slug': 'room_services',
        'name': 'Room Services',
        'path': '/room-services',
        'description': 'Room service orders',
        'display_order': 10,
    },
    {
        'slug': 'hotel_info',
        'name': 'Hotel Info',
        'path': '/hotel-info',
        'description': 'Hotel information',
        'display_order': 13,
    },
    {
        'slug': 'admin_settings',
        'name': 'Admin Settings',
        'path': '/admin-settings',
        'description': 'Hotel configuration and settings',
        'display_order': 14,
    },
]

# Sanity check: item slugs must exactly match CANONICAL_NAV_SLUGS
assert {item['slug'] for item in CANONICAL_NAV_ITEMS} == CANONICAL_NAV_SLUGS, (
    "CANONICAL_NAV_ITEMS slugs do not match CANONICAL_NAV_SLUGS"
)


# ---------------------------------------------------------------------------
# Nav slug -> module_policy module slug projection.
#
# Some navigation slugs are pure UX containers (``home``, ``admin_settings``)
# and have no corresponding module in ``staff.module_policy.MODULE_POLICY``.
# Those slugs are deliberately absent from this map; consumers MUST treat
# missing keys as "no module to gate" and skip nav-vs-module checks for
# them.
#
# This map is the SINGLE SOURCE OF TRUTH for the nav <-> module relation
# used by ``validate_nav_capability_consistency`` (Phase 5). It does not
# affect runtime authorization — frontend nav rendering still consumes
# ``allowed_navs`` and ``rbac.<module>.visible`` independently.
# ---------------------------------------------------------------------------

NAV_TO_MODULE_SLUG: dict[str, str] = {
    'rooms': 'rooms',
    'room_bookings': 'bookings',
    'restaurant_bookings': 'restaurant_bookings',
    'chat': 'chat',
    'housekeeping': 'housekeeping',
    'attendance': 'attendance',
    'staff_management': 'staff_management',
    'room_services': 'room_services',
    'maintenance': 'maintenance',
    'hotel_info': 'hotel_info',
    # 'home' and 'admin_settings' have no module_policy entry.
}

# Modules that exist in MODULE_POLICY but have no top-level nav slug
# (surfaced inline within other modules / UX surfaces).
MODULES_WITHOUT_NAV: frozenset[str] = frozenset({
    'guests',
    'staff_chat',
})

assert set(NAV_TO_MODULE_SLUG.keys()).issubset(CANONICAL_NAV_SLUGS), (
    "NAV_TO_MODULE_SLUG keys must be a subset of CANONICAL_NAV_SLUGS"
)
