# common/views.py
from rest_framework import viewsets, permissions
from .models import ThemePreference
from .serializers import ThemePreferenceSerializer
from django.shortcuts import get_object_or_404
from hotel.models import Hotel


class ThemePreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = ThemePreferenceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Look up by hotel slug instead of PK:
    lookup_field = "hotel__slug"
    lookup_url_kwarg = "hotel_slug"

    def get_queryset(self):
        return ThemePreference.objects.select_related("hotel")

    def get_object(self):
        # Override to get-or-create the ThemePreference for this hotel slug
        hotel = get_object_or_404(Hotel, slug=self.kwargs["hotel_slug"])
        theme, _ = ThemePreference.objects.get_or_create(hotel=hotel)
        return theme
