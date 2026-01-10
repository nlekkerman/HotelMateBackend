from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Base/Admin views
from .base_views import (
    HotelViewSet,
    HotelBySlugView,
)

# Public views
from .public_views import (
    HotelPublicListView,
    HotelFilterOptionsView,
    HotelPublicPageView,
)

# Booking views
from .booking_views import (
    HotelAvailabilityView,
    HotelPricingQuoteView,
    HotelBookingCreateView,
)

# Guest portal views (token-authenticated)
from .guest_portal_views import (
    GuestContextView,
    GuestChatContextView,
    GuestRoomServiceView,
)

# Staff CRUD views and management views
from .staff_views import (
    # ViewSets
    StaffRoomTypeViewSet,
    StaffRoomViewSet,
    StaffAccessConfigViewSet,
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
    RoomsSectionViewSet,
    # Management Views
    HotelSettingsView,
    StaffBookingsListView,
    StaffBookingConfirmView,
    PublicPageBuilderView,
    HotelStatusCheckView,
    PublicPageBootstrapView,
    SectionCreateView,
    # Phase 2: Booking Assignment
    BookingAssignmentView,
    # Phase 3: Booking Party Management
    BookingPartyManagementView,
)

# Payment views
from .payment_views import (
    CreatePaymentSessionView,
    StripeWebhookView,
    VerifyPaymentView,
)

# Default router for the main HotelViewSet
router = DefaultRouter()
router.register(r'hotels', HotelViewSet)

# Staff router for CRUD views
staff_router = DefaultRouter()
staff_router.register(
    r'room-types',
    StaffRoomTypeViewSet,
    basename='staff-room-types'
)
staff_router.register(
    r'rooms',
    StaffRoomViewSet,
    basename='staff-rooms'
)
staff_router.register(
    r'access-config',
    StaffAccessConfigViewSet,
    basename='staff-access-config'
)
staff_router.register(
    r'public-sections',
    PublicSectionViewSet,
    basename='staff-public-sections'
)
staff_router.register(
    r'public-elements',
    PublicElementViewSet,
    basename='staff-public-elements'
)
staff_router.register(
    r'public-element-items',
    PublicElementItemViewSet,
    basename='staff-public-element-items'
)
staff_router.register(
    r'hero-sections',
    HeroSectionViewSet,
    basename='staff-hero-sections'
)
staff_router.register(
    r'gallery-containers',
    GalleryContainerViewSet,
    basename='staff-gallery-containers'
)
staff_router.register(
    r'gallery-images',
    GalleryImageViewSet,
    basename='staff-gallery-images'
)
staff_router.register(
    r'list-containers',
    ListContainerViewSet,
    basename='staff-list-containers'
)
staff_router.register(
    r'cards',
    CardViewSet,
    basename='staff-cards'
)
staff_router.register(
    r'news-items',
    NewsItemViewSet,
    basename='staff-news-items'
)
staff_router.register(
    r'content-blocks',
    ContentBlockViewSet,
    basename='staff-content-blocks'
)
staff_router.register(
    r'rooms-sections',
    RoomsSectionViewSet,
    basename='staff-rooms-sections'
)

urlpatterns = [
    # Guest Portal endpoints (token-authenticated)
    # No hotel slug required - token contains context
    path(
        "guest/context/",
        GuestContextView.as_view(),
        name="guest-context"
    ),
    path(
        "guest/chat/",
        GuestChatContextView.as_view(),
        name="guest-chat-context"
    ),
    path(
        "guest/room-service/",
        GuestRoomServiceView.as_view(),
        name="guest-room-service"
    ),
    
    # Staff CRUD endpoints (B5)
    # Accessed via: /api/staff/hotels/<slug>/hotel/offers/, etc.
    path(
        "staff/",
        include(staff_router.urls),
    ),
    
    # Public Page Builder (Super Staff Admin only)
    # Accessed via: /api/staff/hotel/<slug>/hotel/public-page-builder/
    path(
        "status/",
        HotelStatusCheckView.as_view(),
        name="hotel-status-check"
    ),
    path(
        "public-page-builder/",
        PublicPageBuilderView.as_view(),
        name="public-page-builder"
    ),
    path(
        "public-page-builder/bootstrap-default/",
        PublicPageBootstrapView.as_view(),
        name="public-page-bootstrap"
    ),
    path(
        "sections/create/",
        SectionCreateView.as_view(),
        name="section-create"
    ),
    

    
    # Internal/admin endpoints
    path("", include(router.urls)),
]
