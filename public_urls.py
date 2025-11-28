"""
Public API URLs - No authentication required
Landing page hotel listing, filters, and individual hotel public pages.
"""
from django.urls import path
from hotel.public_views import (
    HotelPublicListView,
    HotelFilterOptionsView,
    HotelPublicPageView,
)
from hotel.booking_views import (
    HotelAvailabilityView,
    HotelPricingQuoteView,
    HotelBookingCreateView,
)

urlpatterns = [
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
        "hotel/<slug:slug>/page/",
        HotelPublicPageView.as_view(),
        name="public-hotel-page"
    ),
    # Public booking endpoints (availability, pricing, booking)
    # These mirror the hotel endpoints but are exposed under the public namespace
    path(
        "hotel/<slug:slug>/availability/",
        HotelAvailabilityView.as_view(),
        name="public-hotel-availability",
    ),
    path(
        "hotel/<slug:slug>/pricing/quote/",
        HotelPricingQuoteView.as_view(),
        name="public-hotel-pricing-quote",
    ),
    path(
        "hotel/<slug:slug>/bookings/",
        HotelBookingCreateView.as_view(),
        name="public-hotel-booking-create",
    ),
]
