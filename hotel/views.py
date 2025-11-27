"""
Hotel Views - Base/Admin views only.

Public, booking, and staff views are separated:
- public_views.py: Public-facing hotel views
- booking_views.py: Booking and availability views
- staff_views.py: Staff management views
"""
from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from .models import Hotel
from .serializers import HotelSerializer


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
