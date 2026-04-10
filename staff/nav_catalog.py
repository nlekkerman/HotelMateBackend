"""
Canonical navigation catalog for HotelMate.

This module is the SINGLE SOURCE OF TRUTH for:
- CANONICAL_NAV_SLUGS: the complete set of valid navigation slugs
- CANONICAL_NAV_ITEMS: the full definition list (slug, name, path, description, display_order)

All consumers (permissions, signals, management commands) MUST import from here.
Do NOT define nav constants elsewhere.
"""

CANONICAL_NAV_SLUGS = frozenset({
    'home', 'rooms', 'bookings', 'chat', 'stock_tracker',
    'housekeeping', 'attendance', 'staff_management', 'room_services',
    'maintenance', 'entertainment', 'hotel_info', 'admin_settings',
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
        'slug': 'bookings',
        'name': 'Bookings',
        'path': '/bookings',
        'description': 'Booking management',
        'display_order': 4,
    },
    {
        'slug': 'housekeeping',
        'name': 'Housekeeping',
        'path': '/housekeeping',
        'description': 'Housekeeping task management',
        'display_order': 5,
    },
    {
        'slug': 'maintenance',
        'name': 'Maintenance',
        'path': '/maintenance',
        'description': 'Maintenance requests',
        'display_order': 6,
    },
    {
        'slug': 'attendance',
        'name': 'Attendance',
        'path': '/attendance',
        'description': 'Staff scheduling and attendance',
        'display_order': 7,
    },
    {
        'slug': 'staff_management',
        'name': 'Staff Management',
        'path': '/staff-management',
        'description': 'Staff administration',
        'display_order': 8,
    },
    {
        'slug': 'room_services',
        'name': 'Room Services',
        'path': '/room-services',
        'description': 'Room service orders',
        'display_order': 9,
    },
    {
        'slug': 'stock_tracker',
        'name': 'Stock Tracker',
        'path': '/stock-tracker',
        'description': 'Inventory management',
        'display_order': 10,
    },
    {
        'slug': 'entertainment',
        'name': 'Entertainment',
        'path': '/entertainment',
        'description': 'Entertainment and games',
        'display_order': 11,
    },
    {
        'slug': 'hotel_info',
        'name': 'Hotel Info',
        'path': '/hotel-info',
        'description': 'Hotel information',
        'display_order': 12,
    },
    {
        'slug': 'admin_settings',
        'name': 'Admin Settings',
        'path': '/admin-settings',
        'description': 'Hotel configuration and settings',
        'display_order': 13,
    },
]

# Sanity check: item slugs must exactly match CANONICAL_NAV_SLUGS
assert {item['slug'] for item in CANONICAL_NAV_ITEMS} == CANONICAL_NAV_SLUGS, (
    "CANONICAL_NAV_ITEMS slugs do not match CANONICAL_NAV_SLUGS"
)
