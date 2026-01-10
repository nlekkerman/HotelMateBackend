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


class IsSuperUser(IsAuthenticated):
    """
    Custom permission to only allow superusers to access the view.
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_superuser


class HotelViewSet(viewsets.ModelViewSet):
    """Admin/internal hotel management - Superuser only"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = [IsSuperUser]
    
    def create(self, request, *args, **kwargs):
        """Create hotel with automatic post-creation setup"""
        response = super().create(request, *args, **kwargs)
        
        # Hotel creation is successful, the post_save signal will handle
        # creating default navigation items automatically
        # See hotel/models.py @receiver(post_save, sender=Hotel)
        
        return response


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
