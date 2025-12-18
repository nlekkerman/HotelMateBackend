"""
STAFF Zone Routing Wrapper - Phase 1
Routes all existing Django apps under:
/api/staff/hotel/<hotel_slug>/<app_name>/
Preserves existing app URL structures without modification.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import from separated view modules
from hotel.staff_views import (
    # Management views
    HotelSettingsView,
    PublicPageBuilderView,
    PublicPageBootstrapView,
    HotelStatusCheckView,
    SectionCreateView,
    HotelPrecheckinConfigView,
    # CRUD ViewSets
    StaffRoomTypeViewSet,
    PresetViewSet,
    HotelPublicPageViewSet,
    PublicSectionViewSet,
    PublicElementViewSet,
    PublicElementItemViewSet,
    HeroSectionViewSet,
    GalleryContainerViewSet,
    GalleryImageViewSet,
    ListContainerViewSet,
    CardViewSet,
    NewsItemViewSet,
    ContentBlockViewSet,
)

from staff.me_views import StaffMeView
from room_services.staff_views import (
    StaffRoomServiceItemViewSet,
    StaffBreakfastItemViewSet
)
from rooms.views import RoomViewSet, RoomTypeViewSet

# List of all apps with URLs to wrap in STAFF zone
# Note: 'posts' app excluded (no urls.py - only contains static files)
# Note: 'hotel' removed to avoid double nesting (using direct routes above)
STAFF_APPS = [
    'attendance',
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

# Create router for direct staff endpoints
staff_hotel_router = DefaultRouter()
staff_hotel_router.register(
    r'presets',
    PresetViewSet,
    basename='staff-presets'
)
staff_hotel_router.register(
    r'public-page',
    HotelPublicPageViewSet,
    basename='staff-public-page'
)
staff_hotel_router.register(
    r'room-types',
    StaffRoomTypeViewSet,
    basename='staff-room-types-direct'
)
staff_hotel_router.register(
    r'public-sections',
    PublicSectionViewSet,
    basename='staff-public-sections'
)
staff_hotel_router.register(
    r'public-elements',
    PublicElementViewSet,
    basename='staff-public-elements'
)
staff_hotel_router.register(
    r'public-element-items',
    PublicElementItemViewSet,
    basename='staff-public-element-items'
)
staff_hotel_router.register(
    r'hero-sections',
    HeroSectionViewSet,
    basename='staff-hero-sections'
)
staff_hotel_router.register(
    r'gallery-containers',
    GalleryContainerViewSet,
    basename='staff-gallery-containers'
)
staff_hotel_router.register(
    r'gallery-images',
    GalleryImageViewSet,
    basename='staff-gallery-images'
)
staff_hotel_router.register(
    r'list-containers',
    ListContainerViewSet,
    basename='staff-list-containers'
)
staff_hotel_router.register(
    r'cards',
    CardViewSet,
    basename='staff-cards'
)
staff_hotel_router.register(
    r'news-items',
    NewsItemViewSet,
    basename='staff-news-items'
)
staff_hotel_router.register(
    r'content-blocks',
    ContentBlockViewSet,
    basename='staff-content-blocks'
)
staff_hotel_router.register(
    r'room-service-items',
    StaffRoomServiceItemViewSet,
    basename='staff-room-service-items'
)
staff_hotel_router.register(
    r'breakfast-items',
    StaffBreakfastItemViewSet,
    basename='staff-breakfast-items'
)
staff_hotel_router.register(
    r'rooms',
    RoomViewSet,
    basename='staff-rooms'
)
staff_hotel_router.register(
    r'room-types',
    RoomTypeViewSet,
    basename='staff-room-types'
)

urlpatterns = [
    # Include staff authentication routes FIRST (no hotel_slug required)
    path('', include('staff.urls')),
    
    # Phase 1 Direct Staff Routes (cleaner URLs)
    # Staff Profile
    path(
        'hotel/<str:hotel_slug>/me/',
        StaffMeView.as_view(),
        name='staff-profile-me'
    ),
    
    # Room bookings management - Phase 2 routing
    path(
        'hotel/<str:hotel_slug>/room-bookings/',
        include('room_bookings.staff_urls')
    ),
    
    # Service bookings management - Phase 4A routing  
    path(
        'hotel/<str:hotel_slug>/service-bookings/',
        include('bookings.staff_urls')
    ),
    
    # Hotel Settings
    path(
        'hotel/<str:hotel_slug>/settings/',
        HotelSettingsView.as_view(),
        name='staff-hotel-settings'
    ),
    
    # Public Page Builder (Super Staff Admin only)
    path(
        'hotel/<str:hotel_slug>/status/',
        HotelStatusCheckView.as_view(),
        name='staff-hotel-status'
    ),
    path(
        'hotel/<str:hotel_slug>/public-page-builder/',
        PublicPageBuilderView.as_view(),
        name='staff-public-page-builder'
    ),
    path(
        'hotel/<str:hotel_slug>/public-page-builder/bootstrap-default/',
        PublicPageBootstrapView.as_view(),
        name='staff-public-page-bootstrap'
    ),
    path(
        'hotel/<str:hotel_slug>/sections/create/',
        SectionCreateView.as_view(),
        name='staff-section-create'
    ),
    
    # Precheckin Configuration (Super Staff Admin only)
    path(
        'hotel/<str:hotel_slug>/precheckin-config/',
        HotelPrecheckinConfigView.as_view(),
        name='staff-precheckin-config'
    ),
    
    # Room Types & Section CRUD (clean path)
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

# Add Room Turnover Workflow Staff URLs
urlpatterns += [
    path('', include('rooms.staff_urls')),
]


