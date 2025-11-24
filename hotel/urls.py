from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HotelViewSet,
    HotelBySlugView,
    HotelPublicListView,
    HotelPublicDetailView,
    HotelPublicPageView,
    HotelAvailabilityView,
    HotelPricingQuoteView,
    HotelBookingCreateView,
)
from .payment_views import (
    CreatePaymentSessionView,
    StripeWebhookView,
    VerifyPaymentView,
)

# Default router for the main HotelViewSet
router = DefaultRouter()
router.register(r'hotels', HotelViewSet)

urlpatterns = [
    # Public API endpoints for hotel discovery
    path(
        "public/",
        HotelPublicListView.as_view(),
        name="hotel-public-list"
    ),
    path(
        "public/<slug:slug>/",
        HotelPublicDetailView.as_view(),
        name="hotel-public-detail"
    ),
    path(
        "public/page/<slug:slug>/",
        HotelPublicPageView.as_view(),
        name="hotel-public-page"
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
    
    # Payment endpoint under hotel slug (for frontend compatibility)
    path(
        "<slug:slug>/bookings/<str:booking_id>/payment/session/",
        CreatePaymentSessionView.as_view(),
        name="hotel-booking-payment-session"
    ),
    
    # Payment endpoints (generic namespace)
    path(
        "bookings/<str:booking_id>/payment/session/",
        CreatePaymentSessionView.as_view(),
        name="booking-payment-session"
    ),
    path(
        "bookings/<str:booking_id>/payment/verify/",
        VerifyPaymentView.as_view(),
        name="booking-payment-verify"
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
