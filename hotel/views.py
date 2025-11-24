from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import datetime

from .models import Hotel
from .serializers import (
    HotelSerializer,
    HotelPublicSerializer,
    HotelPublicDetailSerializer
)


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


class HotelPublicPageView(generics.RetrieveAPIView):
    """
    Public API endpoint for complete hotel page content.
    Returns full hotel details including booking options,
    room types, offers, and leisure activities.
    For non-authenticated public users browsing hotels.
    """
    serializer_class = HotelPublicDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        """Optimized query with all related objects"""
        return Hotel.objects.filter(
            is_active=True
        ).select_related(
            'booking_options'
        ).prefetch_related(
            'room_types',
            'offers',
            'leisure_activities'
        )


class HotelAvailabilityView(APIView):
    """
    Check room availability for specific dates.
    Phase 1 implementation: Returns all room types with basic
    availability info.
    
    Query params:
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults (default 2)
    - children: number of children (default 0)
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse query parameters
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        adults = int(request.query_params.get('adults', 2))
        children = int(request.query_params.get('children', 0))
        
        # Validate required parameters
        if not check_in_str or not check_out_str:
            return Response(
                {"detail": "check_in and check_out dates are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate dates
        if check_out <= check_in:
            return Response(
                {"detail": "check_out must be after check_in"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate nights
        nights = (check_out - check_in).days
        
        # Get active room types for this hotel
        room_types = hotel.room_types.filter(
            is_active=True
        ).order_by('sort_order', 'name')
        
        # Build response
        available_rooms = []
        total_guests = adults + children
        
        for room_type in room_types:
            # Check if room can accommodate guests
            can_accommodate = room_type.max_occupancy >= total_guests
            
            # Build room data
            room_data = {
                "room_type_code": room_type.code or room_type.name,
                "room_type_name": room_type.name,
                "is_available": can_accommodate,
                "max_occupancy": room_type.max_occupancy,
                "bed_setup": room_type.bed_setup,
                "short_description": room_type.short_description,
                "photo": room_type.photo.url if room_type.photo else None,
                "starting_price_from": str(room_type.starting_price_from),
                "currency": room_type.currency,
                "availability_message": room_type.availability_message,
                "note": None
            }
            
            # Add note for capacity issues
            if not can_accommodate:
                room_data["note"] = (
                    f"Maximum occupancy is {room_type.max_occupancy} "
                    f"guests"
                )
            
            available_rooms.append(room_data)
        
        response_data = {
            "hotel": hotel.slug,
            "hotel_name": hotel.name,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights,
            "adults": adults,
            "children": children,
            "total_guests": total_guests,
            "available_rooms": available_rooms
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
