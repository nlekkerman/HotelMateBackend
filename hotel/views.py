from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Hotel
from .serializers import HotelSerializer, HotelPublicSerializer


class HotelViewSet(viewsets.ModelViewSet):
    """Admin/internal hotel management"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = []  # You can add IsAdminUser, etc.


class HotelBySlugView(generics.RetrieveAPIView):
    """Get hotel by slug - internal use"""
    queryset = Hotel.objects.all()
    permission_classes = [AllowAny]
    serializer_class = HotelSerializer
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get("slug")
        hotel = get_object_or_404(Hotel, slug=slug)
        return hotel


class HotelPublicListView(generics.ListAPIView):
    """
    Public API endpoint for hotel discovery.
    Returns active hotels with branding and portal configuration.
    """
    serializer_class = HotelPublicSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Only return active hotels with access_config"""
        return Hotel.objects.filter(
            is_active=True
        ).select_related(
            'access_config'
        ).order_by('sort_order', 'name')


class HotelPublicDetailView(generics.RetrieveAPIView):
    """
    Public API endpoint for single hotel details by slug.
    Returns hotel with branding and portal configuration.
    """
    serializer_class = HotelPublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        """Only return active hotels with access_config"""
        return Hotel.objects.filter(
            is_active=True
        ).select_related('access_config')
