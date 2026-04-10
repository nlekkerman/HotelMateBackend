"""
Hotel Views - Base/Admin views only.

Public, booking, and staff views are separated:
- public_views.py: Public-facing hotel views
- booking_views.py: Booking and availability views
- staff_views.py: Staff management views
"""
from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Hotel
from .base_serializers import HotelSerializer
from staff.permissions import IsAdminTier


class HotelViewSet(viewsets.ModelViewSet):
    """Admin/internal hotel management - staff_admin tier and above"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [IsAdminTier]
    
    def create(self, request, *args, **kwargs):
        """
        Hotel creation via this endpoint is disabled.
        Use POST /api/hotel/hotels/provision/ instead.
        """
        return Response(
            {"detail": "Hotel creation is only available through /api/hotel/hotels/provision/"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


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
