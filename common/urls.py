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
    # Matches: /api/hotels/{hotel_slug}/theme/
    path(
        "<str:hotel_slug>/theme/",
        hotel_theme,
        name="hotel-theme"
    ),
]
