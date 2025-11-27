from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Base/Admin views
from .views import (
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
    # Management Views
    HotelSettingsView,
    StaffBookingsListView,
    StaffBookingConfirmView,
    PublicPageBuilderView,
    HotelStatusCheckView,
    PublicPageBootstrapView,
    SectionCreateView,
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

urlpatterns = [
    # Staff bookings endpoints
    # Accessed via: /api/staff/hotels/<slug>/hotel/bookings/
    path(
        "bookings/",
        StaffBookingsListView.as_view(),
        name="hotel-staff-bookings-list"
    ),
    path(
        "bookings/<str:booking_id>/confirm/",
        StaffBookingConfirmView.as_view(),
        name="hotel-staff-booking-confirm"
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
    
    # Availability check endpoint
    path(
        "<slug:slug>/availability/",
        HotelAvailabilityView.as_view(),
        name="hotel-availability"
    ),
    
    # Pricing quote endpoint
    path(
        "<slug:slug>/pricing/quote/",
        HotelPricingQuoteView.as_view(),
        name="hotel-pricing-quote"
    ),
    
    # Booking creation endpoint
    path(
        "<slug:slug>/bookings/",
        HotelBookingCreateView.as_view(),
        name="hotel-booking-create"
    ),
    
    # Payment endpoints - MUST include hotel slug
    path(
        "<slug:slug>/bookings/<str:booking_id>/payment/",
        CreatePaymentSessionView.as_view(),
        name="hotel-booking-payment"
    ),
    path(
        "<slug:slug>/bookings/<str:booking_id>/payment/session/",
        CreatePaymentSessionView.as_view(),
        name="hotel-booking-payment-session"
    ),
    path(
        "<slug:slug>/bookings/<str:booking_id>/payment/verify/",
        VerifyPaymentView.as_view(),
        name="hotel-booking-payment-verify"
    ),
    path(
        "bookings/stripe-webhook/",
        StripeWebhookView.as_view(),
        name="stripe-webhook"
    ),
    
    # Internal/admin endpoints
    path("", include(router.urls)),
    path(
        "<slug:slug>/",
        HotelBySlugView.as_view(),
        name="hotel-by-slug"
    ),
]
