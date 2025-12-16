"""
Booking-related views for availability, pricing quotes, and booking creation.
Public endpoints - no authentication required.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models

from .models import Hotel, BookerType, BookingGuest

# Import service layer functions
from hotel.services.availability import (
    validate_dates, get_room_type_availability
)
from hotel.services.pricing import build_pricing_quote_data
from hotel.services.booking import create_room_booking_from_request


class HotelAvailabilityView(APIView):
    """
    Check room availability for specific dates.
    Uses service layer for real inventory checking.
    
    Query params:
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults (default 2)
    - children: number of children (default 0)
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
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
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(
                check_in_str, check_out_str
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get availability using service layer
        available_rooms = get_room_type_availability(
            hotel, check_in, check_out, adults, children
        )
        
        # Build response
        total_guests = adults + children
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
    Uses service layer for advanced pricing with rate plans and promotions.
    
    POST body:
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults
    - children: number of children
    - promo_code: optional promo code
    """
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
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
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(
                check_in_str, check_out_str
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
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
        
        # Build pricing quote using service layer
        response_data = build_pricing_quote_data(
            hotel=hotel,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            promo_code=promo_code
        )
        
        return Response(response_data, status=status.HTTP_200_OK)


class HotelBookingCreateView(APIView):
    """
    Create a new room booking using NEW canonical fields only.
    NO LEGACY SUPPORT - fails fast if old guest{} payload is used.
    
    POST body (REQUIRED):
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - primary_first_name, primary_last_name, primary_email, primary_phone
    - booker_type: SELF | THIRD_PARTY | COMPANY
    
    POST body (CONDITIONAL):
    - If booker_type != SELF: booker_first_name, booker_last_name,
      booker_email, booker_phone
    - If booker_type == COMPANY: booker_company
    
    POST body (OPTIONAL):
    - adults, children (defaults to 2, 0)
    - special_requests, promo_code
    - party: [{role, first_name, last_name, email?, phone?}]
    """
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
        # ❌ HARD RULE: Reject legacy guest{} payload
        if 'guest' in request.data:
            return Response(
                {
                    "detail": "Legacy guest payload is not supported. "
                    "Use primary_* fields."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse REQUIRED fields
        room_type_code = request.data.get('room_type_code')
        check_in_str = request.data.get('check_in')
        check_out_str = request.data.get('check_out')
        
        primary_first_name = request.data.get('primary_first_name')
        primary_last_name = request.data.get('primary_last_name')
        primary_email = request.data.get('primary_email')
        primary_phone = request.data.get('primary_phone')
        
        booker_type = request.data.get('booker_type')
        
        # Validate REQUIRED fields
        required_fields = [
            room_type_code, check_in_str, check_out_str,
            primary_first_name, primary_last_name, primary_email,
            primary_phone, booker_type
        ]
        if not all(field for field in required_fields):
            return Response(
                {
                    "detail": "Required fields: room_type_code, check_in, "
                    "check_out, primary_first_name, primary_last_name, "
                    "primary_email, primary_phone, booker_type"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate booker_type
        if booker_type not in BookerType.values():
            return Response(
                {
                    "detail": f"booker_type must be one of: "
                    f"{BookerType.values()}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse CONDITIONAL booker fields
        booker_first_name = request.data.get('booker_first_name', '')
        booker_last_name = request.data.get('booker_last_name', '')
        booker_email = request.data.get('booker_email', '')
        booker_phone = request.data.get('booker_phone', '')
        booker_company = request.data.get('booker_company', '')
        
        # Validate CONDITIONAL fields based on booker_type
        if booker_type != BookerType.SELF:
            required_booker = [
                booker_first_name, booker_last_name, booker_email, booker_phone
            ]
            if not all(required_booker):
                return Response(
                    {
                        "detail": "For THIRD_PARTY or COMPANY bookings, "
                        "booker_first_name, booker_last_name, booker_email, "
                        "and booker_phone are required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if booker_type == BookerType.COMPANY:
            if not booker_company:
                return Response(
                    {
                        "detail": "booker_company is required for "
                        "COMPANY bookings"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parse OPTIONAL fields
        adults = int(request.data.get('adults', 2))
        children = int(request.data.get('children', 0))
        special_requests = request.data.get('special_requests', '')
        promo_code = request.data.get('promo_code', '')
        party_data = request.data.get('party', [])
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(
                check_in_str, check_out_str
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
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
        
        # Create booking using NEW field structure (NO LEGACY!)
        booking = create_room_booking_from_request(
            hotel=hotel,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            primary_first_name=primary_first_name,
            primary_last_name=primary_last_name,
            primary_email=primary_email,
            primary_phone=primary_phone,
            booker_type=booker_type,
            booker_first_name=booker_first_name,
            booker_last_name=booker_last_name,
            booker_email=booker_email,
            booker_phone=booker_phone,
            booker_company=booker_company,
            special_requests=special_requests,
            promo_code=promo_code
        )
        
        # Handle party creation with MANDATORY alignment
        try:
            from django.db import transaction
            
            with transaction.atomic():
                if party_data:
                    # Validate party list structure
                    primary_count = sum(
                        1 for p in party_data if p.get('role') == 'PRIMARY'
                    )
                    if primary_count != 1:
                        return Response(
                            {
                                "detail": "Party must include exactly one "
                                "PRIMARY guest"
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Validate PRIMARY guest matches primary_* fields
                    primary_party = next(
                        p for p in party_data if p.get('role') == 'PRIMARY'
                    )
                    first_name_match = (
                        primary_party.get('first_name') == primary_first_name
                    )
                    last_name_match = (
                        primary_party.get('last_name') == primary_last_name
                    )
                    if not (first_name_match and last_name_match):
                        return Response(
                            {
                                "detail": "PRIMARY party member must match "
                                "primary_first_name and primary_last_name"
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Create party members
                    for party_member in party_data:
                        role = party_member.get('role', 'COMPANION')
                        first_name = party_member.get('first_name', '').strip()
                        last_name = party_member.get('last_name', '').strip()
                        
                        if not first_name or not last_name:
                            return Response(
                                {
                                    "detail": "All party members must have "
                                    "first_name and last_name"
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # Create BookingGuest record (only for COMPANION roles)
                        # PRIMARY is automatically created by RoomBooking.save()
                        if role != 'PRIMARY':
                            BookingGuest.objects.create(
                                booking=booking,
                                role=role,
                                first_name=first_name,
                                last_name=last_name,
                                email=party_member.get('email', ''),
                                phone=party_member.get('phone', ''),
                                is_staying=True,
                            )
                
                # PRIMARY BookingGuest is automatically created by RoomBooking.save()
                # No manual creation needed here
                        
        except Exception as e:
            return Response(
                {"detail": f"Failed to create party: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Count party members
        party_count = len(party_data) if party_data else 1
        
        # Return public-safe response payload
        response_data = {
            "success": True,
            "data": {
                "booking_id": booking.booking_id,
                "status": booking.status,
                "primary_guest_name": (
                    f"{booking.primary_first_name} "
                    f"{booking.primary_last_name}"
                ),
                "booker_type": booking.booker_type,
                "party_count": party_count
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class PublicRoomBookingDetailView(APIView):
    """
    Get booking details by booking ID for external booking system.
    Phase 1: Returns mock data based on booking ID format.
    
    GET /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug, booking_id):
        # Phase 1: Return placeholder booking data
        # In Phase 2, this would query the database
        
        # Extract info from booking_id format: BK-YYYY-XXXXXX
        try:
            parts = booking_id.split('-')
            if len(parts) != 3 or parts[0] != 'BK':
                return Response(
                    {"detail": "Invalid booking ID format"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            year = parts[1]
            code = parts[2]
            
        except (IndexError, ValueError):
            return Response(
                {"detail": "Invalid booking ID format"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return mock booking data
        booking_data = {
            "booking_id": booking_id,
            "confirmation_number": f"HOT-{year}-{code[:4]}",
            "status": "PENDING_PAYMENT",
            "created_at": f"{year}-11-24T15:30:00Z",
            "hotel": {
                "name": "Hotel Killarney",
                "slug": hotel_slug,
                "phone": "+353 64 663 1555",
                "email": "info@hotelkillarney.ie"
            },
            "room": {
                "type": "Deluxe King Room",
                "code": "DLX-KING",
                "photo": None
            },
            "dates": {
                "check_in": "2025-12-20",
                "check_out": "2025-12-22",
                "nights": 2
            },
            "guests": {
                "adults": 2,
                "children": 0,
                "total": 2
            },
            "guest": {
                "name": "Guest Name",
                "email": "guest@example.com",
                "phone": "+353 87 123 4567"
            },
            "special_requests": "",
            "pricing": {
                "subtotal": "300.00",
                "taxes": "27.00",
                "discount": "0.00",
                "total": "327.00",
                "currency": "EUR"
            },
            "promo_code": None,
            "payment_required": True,
            "payment_url": f"/api/public/hotel/{hotel_slug}/room-bookings/{booking_id}/payment/session/"
        }
        
        return Response(booking_data, status=status.HTTP_200_OK)
