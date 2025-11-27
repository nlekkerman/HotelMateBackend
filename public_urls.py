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
]
