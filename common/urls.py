# common/urls.py
from django.urls import path
from common.views import ThemePreferenceViewSet, HotelThemeView

# Map GET→retrieve (and auto‐create), POST→create (if you want),
# PATCH→partial_update, PUT→update on one URL:
hotel_theme = ThemePreferenceViewSet.as_view({
    "get":    "retrieve",
    "post":   "create",
    "patch":  "partial_update",
    "put":    "update",
})

urlpatterns = [
    # Public theme endpoint
    # Matches: /api/common/{hotel_slug}/theme/
    path(
        "<slug:hotel_slug>/theme/",
        HotelThemeView.as_view(),
        name="public-hotel-theme"
    ),
    
    # Staff theme endpoint (legacy)
    # Matches: /api/staff/hotels/{hotel_slug}/common/theme/
    # hotel_slug is already captured by staff_urls.py
    path(
        "theme/",
        hotel_theme,
        name="hotel-theme"
    ),
]
