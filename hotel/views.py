from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models
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


class HotelPricingQuoteView(APIView):
    """
    Calculate pricing quote for a specific room type and dates.
    Phase 1 implementation: Basic pricing calculation based on
    room type base price.
    
    POST body:
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults
    - children: number of children
    - promo_code: optional promo code
    """
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        from decimal import Decimal
        import uuid
        from django.utils import timezone
        
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse request data
        room_type_code = request.data.get('room_type_code')
        check_in_str = request.data.get('check_in')
        check_out_str = request.data.get('check_out')
        adults = int(request.data.get('adults', 2))
        children = int(request.data.get('children', 0))
        promo_code = request.data.get('promo_code', '')
        
        # Validate required fields
        if not all([room_type_code, check_in_str, check_out_str]):
            return Response(
                {
                    "detail": "room_type_code, check_in, and check_out "
                    "are required"
                },
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
        
        # Find room type
        room_type = hotel.room_types.filter(
            is_active=True
        ).filter(
            models.Q(code=room_type_code) | models.Q(name=room_type_code)
        ).first()
        
        if not room_type:
            return Response(
                {"detail": f"Room type '{room_type_code}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate pricing
        nights = (check_out - check_in).days
        base_price = Decimal(str(room_type.starting_price_from))
        subtotal = base_price * nights
        
        # Calculate taxes (9% VAT for Ireland)
        tax_rate = Decimal('0.09')
        taxes = subtotal * tax_rate
        
        # Apply promo code if provided
        discount = Decimal('0')
        applied_promo = None
        
        if promo_code:
            # Simple promo code logic (can be expanded later)
            promo_code_upper = promo_code.upper()
            if promo_code_upper == 'WINTER20':
                discount = subtotal * Decimal('0.20')
                applied_promo = {
                    "code": "WINTER20",
                    "description": "20% off winter bookings",
                    "discount_percentage": "20.00"
                }
            elif promo_code_upper == 'SAVE10':
                discount = subtotal * Decimal('0.10')
                applied_promo = {
                    "code": "SAVE10",
                    "description": "10% off your stay",
                    "discount_percentage": "10.00"
                }
        
        # Calculate total
        fees = Decimal('0')
        total = subtotal + taxes + fees - discount
        
        # Generate quote ID
        quote_id = f"QT-{timezone.now().year}-{uuid.uuid4().hex[:6].upper()}"
        
        # Quote valid for 30 minutes
        valid_until = timezone.now() + timezone.timedelta(minutes=30)
        
        response_data = {
            "quote_id": quote_id,
            "valid_until": valid_until.isoformat(),
            "currency": room_type.currency,
            "room_type": {
                "code": room_type.code or room_type.name,
                "name": room_type.name,
                "photo": room_type.photo.url if room_type.photo else None
            },
            "dates": {
                "check_in": check_in_str,
                "check_out": check_out_str,
                "nights": nights
            },
            "guests": {
                "adults": adults,
                "children": children,
                "total": adults + children
            },
            "breakdown": {
                "base_price_per_night": f"{base_price:.2f}",
                "number_of_nights": nights,
                "subtotal": f"{subtotal:.2f}",
                "taxes": f"{taxes:.2f}",
                "fees": f"{fees:.2f}",
                "discount": f"-{discount:.2f}" if discount > 0 else "0.00",
                "total": f"{total:.2f}"
            },
            "applied_promo": applied_promo
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
