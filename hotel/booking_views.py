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
from django.conf import settings
import logging

from .models import Hotel, BookerType, BookingGuest, RoomBooking

# Import service layer functions
from hotel.services.availability import (
    validate_dates, get_room_type_availability
)
from hotel.services.pricing import build_pricing_quote_data
from hotel.services.booking import create_room_booking_from_request

# Import email service
from notifications.email_service import send_booking_confirmation_email, send_booking_received_email

logger = logging.getLogger(__name__)


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
        
        # Handle companions-only party creation
        try:
            from django.db import transaction
            
            with transaction.atomic():
                if party_data:
                    # ✅ NEW CANONICAL RULE: Reject PRIMARY in party payload
                    primary_count = sum(
                        1 for p in party_data if p.get('role') == 'PRIMARY'
                    )
                    if primary_count > 0:
                        return Response(
                            {
                                "detail": "Do not include PRIMARY in party; "
                                "primary guest is inferred from primary_* fields."
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Validate companions (first_name/last_name required, email/phone optional)
                    for party_member in party_data:
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
                        
                        # Create COMPANION BookingGuest records only
                        # PRIMARY is automatically created/synced by RoomBooking.save()
                        BookingGuest.objects.create(
                            booking=booking,
                            role='COMPANION',  # Force all party payload items to COMPANION
                            first_name=first_name,
                            last_name=last_name,
                            email=party_member.get('email', ''),
                            phone=party_member.get('phone', ''),
                            is_staying=True,
                        )
                
                # PRIMARY BookingGuest is automatically created/synced by RoomBooking.save()
                # No manual creation needed here
                        
        except Exception as e:
            return Response(
                {"detail": f"Failed to create party: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Count party members (1 PRIMARY + companions)
        party_count = 1 + len(party_data)  # 1 PRIMARY + companions
        
        # Generate secure guest booking token
        from .models import GuestBookingToken
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=booking,
            purpose='STATUS'
        )
        
        # Send "Booking Received" email with status page link (NOT confirmation)
        try:
            # Create FRONTEND status page URL with guest token (not API endpoint)
            frontend_domain = getattr(settings, 'FRONTEND_DOMAIN', 'http://localhost:5173')
            status_url = f"{frontend_domain}/booking-status/{booking.booking_id}?token={raw_token}"
            
            # Send booking received email (pending approval, not confirmed)
            send_booking_received_email(booking, status_url, raw_token)
            logger.info(f"Booking received email sent for booking {booking.booking_id}")
        except ImportError:
            logger.warning(f"Email service not available for booking received notification")
        except Exception as e:
            logger.error(f"Failed to send booking received email for {booking.booking_id}: {e}")
        
        # Return public-safe response payload with guest token
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
                "party_count": party_count,
                "guest_token": raw_token,  # Secure token for guest realtime access
                "token_expires": token_obj.expires_at.isoformat() if token_obj.expires_at else None
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class PublicRoomBookingDetailView(APIView):
    """
    Get booking details by booking ID for external booking system.
    Queries the actual RoomBooking model and returns public-safe fields.
    
    GET /api/public/hotel/<hotel_slug>/room-bookings/<booking_id>/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug, booking_id):
        # Get hotel first to verify it exists and is active
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
        # Get booking by ID, scoped to this hotel
        booking = get_object_or_404(
            RoomBooking,
            booking_id=booking_id,
            hotel=hotel
        )
        
        # Import the public serializer
        from .booking_serializers import PublicRoomBookingDetailSerializer
        
        # Serialize using public-safe serializer
        serializer = PublicRoomBookingDetailSerializer(
            booking, 
            context={'request': request}
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)
