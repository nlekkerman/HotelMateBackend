"""
STAFF Zone Routing Wrapper - Phase 1
Routes all existing Django apps under:
/api/staff/hotel/<hotel_slug>/<app_name>/
Preserves existing app URL structures without modification.
"""

from django.urls import path, include
from hotel.views import (
    HotelPublicSettingsStaffView,
    StaffBookingsListView,
    StaffBookingConfirmView,
)
from hotel.staff_views import (
    StaffRoomTypeViewSet,
    StaffGalleryViewSet,
    StaffGalleryImageViewSet,
)
from rest_framework.routers import DefaultRouter

# List of all apps with URLs to wrap in STAFF zone
# Note: 'posts' app excluded (no urls.py - only contains static files)
# Note: 'hotel' removed to avoid double nesting (using direct routes above)
STAFF_APPS = [
    'attendance',
    'bookings',
    'chat',
    'common',
    'entertainment',
    'guests',
    'home',
    'hotel_info',
    'maintenance',
    'notifications',
    'room_services',
    'rooms',
    'staff',
    'staff_chat',
    'stock_tracker',
]

# Create router for room-types and galleries
staff_hotel_router = DefaultRouter()
staff_hotel_router.register(
    r'room-types',
    StaffRoomTypeViewSet,
    basename='staff-room-types-direct'
)
staff_hotel_router.register(
    r'galleries',
    StaffGalleryViewSet,
    basename='staff-galleries'
)
staff_hotel_router.register(
    r'gallery-images',
    StaffGalleryImageViewSet,
    basename='staff-gallery-images'
)

urlpatterns = [
    # Phase 1 Direct Staff Routes (cleaner URLs)
    # Hotel settings management
    path(
        'hotel/<str:hotel_slug>/settings/',
        HotelPublicSettingsStaffView.as_view(),
        name='staff-hotel-settings'
    ),
    # Bookings management
    path(
        'hotel/<str:hotel_slug>/bookings/',
        StaffBookingsListView.as_view(),
        name='staff-hotel-bookings'
    ),
    path(
        'hotel/<str:hotel_slug>/bookings/<str:booking_id>/confirm/',
        StaffBookingConfirmView.as_view(),
        name='staff-hotel-booking-confirm'
    ),
    # Room Types & Galleries CRUD (clean path)
    path(
        'hotel/<str:hotel_slug>/',
        include(staff_hotel_router.urls)
    ),
]

# App-wrapped routes for legacy compatibility
urlpatterns += [
    path(
        f'hotel/<str:hotel_slug>/{app}/',
        include(f'{app}.urls'),
        name=f'staff-{app}'
    )
    for app in STAFF_APPS
]
