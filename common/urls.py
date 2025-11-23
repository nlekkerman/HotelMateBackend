# common/urls.py
from django.urls import path
from common.views import ThemePreferenceViewSet

# Map GET→retrieve (and auto‐create), POST→create (if you want),
# PATCH→partial_update, PUT→update on one URL:
hotel_theme = ThemePreferenceViewSet.as_view({
    "get":    "retrieve",
    "post":   "create",
    "patch":  "partial_update",
    "put":    "update",
})

urlpatterns = [
    # Matches: /api/staff/hotels/{hotel_slug}/common/theme/
    # hotel_slug is already captured by staff_urls.py
    path(
        "theme/",
        hotel_theme,
        name="hotel-theme"
    ),
]
