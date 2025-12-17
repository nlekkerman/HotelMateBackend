"""
Public API URLs - No authentication required
Landing page hotel listing, filters, and individual hotel public pages.
"""
from django.urls import path, include
from hotel.public_views import (
    HotelPublicListView,
    HotelFilterOptionsView,
    HotelPublicPageView,
    PublicPresetsView,
)

from hotel.booking_views import (
    HotelAvailabilityView,
    HotelPricingQuoteView,
    HotelBookingCreateView,
    PublicRoomBookingDetailView,
)
from hotel.payment_views import (
    CreatePaymentSessionView,
    VerifyPaymentView,
    StripeWebhookView,
)

app_name = "public"

urlpatterns = [
    # Presets for frontend styling (no auth required)
    path(
        "presets/",
        PublicPresetsView.as_view(),
        name="public-presets"
    ),
    
    # Hotel listing for landing page
    path(
        "hotels/",
        HotelPublicListView.as_view(),
        name="public-hotel-list"
    ),
    
    # Filter options (tags, types, locations)
    path(
        "hotels/filters/",
        HotelFilterOptionsView.as_view(),
        name="public-hotel-filters"
    ),
    
    # Individual hotel public page structure
    path(
        "hotel/<str:hotel_slug>/page/",
        HotelPublicPageView.as_view(),
        name="public-hotel-page"
    ),
    
    # Public booking endpoints (availability, pricing, booking)
    path(
        "hotel/<str:hotel_slug>/availability/",
        HotelAvailabilityView.as_view(),
        name="public-hotel-availability",
    ),
    path(
        "hotel/<str:hotel_slug>/pricing/quote/",
        HotelPricingQuoteView.as_view(),
        name="public-hotel-pricing-quote",
    ),
    path(
        "hotel/<str:hotel_slug>/bookings/",
        HotelBookingCreateView.as_view(),
        name="public-hotel-booking-create",
    ),
    
    # Room booking detail (external booking system lookup)
    path(
        "hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/",
        PublicRoomBookingDetailView.as_view(),
        name="public-room-booking-detail",
    ),
    
    # Payment endpoints
    path(
        "hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/",
        CreatePaymentSessionView.as_view(),
        name="public-hotel-booking-payment"
    ),
    path(
        "hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/session/",
        CreatePaymentSessionView.as_view(),
        name="public-hotel-booking-payment-session"
    ),
    path(
        "hotel/<str:hotel_slug>/room-bookings/<str:booking_id>/payment/verify/",
        VerifyPaymentView.as_view(),
        name="public-hotel-booking-payment-verify"
    ),
    
    # Stripe webhook (no hotel slug needed)
    path(
        "hotel/room-bookings/stripe-webhook/",
        StripeWebhookView.as_view(),
        name="public-stripe-webhook"
    ),
    
    # Include hotel public URLs (pre-check-in endpoints)
    path("", include("hotel.public_urls")),
]
