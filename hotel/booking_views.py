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
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

from .models import Hotel, RoomBooking, PricingQuote

# Import service layer functions
from hotel.services.availability import validate_dates, get_room_type_availability
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
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(check_in_str, check_out_str)
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
    
    def post(self, request, slug):
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
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(check_in_str, check_out_str)
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
    Create a new room booking.
    Uses service layer for consistent pricing calculation.
    
    POST body:
    - quote_id: optional quote reference
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults
    - children: number of children
    - guest: {first_name, last_name, email, phone}
    - special_requests: optional text
    - promo_code: optional promo code
    """
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse request data
        quote_id = request.data.get('quote_id', '')
        room_type_code = request.data.get('room_type_code')
        check_in_str = request.data.get('check_in')
        check_out_str = request.data.get('check_out')
        adults = int(request.data.get('adults', 2))
        children = int(request.data.get('children', 0))
        guest_data = request.data.get('guest', {})
        special_requests = request.data.get('special_requests', '')
        promo_code = request.data.get('promo_code', '')
        # Phase 3: Optional party list
        party_data = request.data.get('party', [])
        
        # Validate required fields
        required_fields = [room_type_code, check_in_str, check_out_str]
        if not all(required_fields):
            return Response(
                {
                    "detail": "room_type_code, check_in, and check_out "
                    "are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate guest data
        required_guest = ['first_name', 'last_name', 'email', 'phone']
        if not all(guest_data.get(field) for field in required_guest):
            return Response(
                {
                    "detail": "Guest first_name, last_name, email, and "
                    "phone are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and parse dates using service layer
        try:
            check_in, check_out, nights = validate_dates(check_in_str, check_out_str)
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
        
        # Create booking using service layer
        booking = create_room_booking_from_request(
            hotel=hotel,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            guest_data=guest_data,
            special_requests=special_requests,
            promo_code=promo_code
        )
        
        # Phase 3: Handle optional party list
        if party_data:
            try:
                from django.db import transaction
                from .models import BookingGuest
                
                with transaction.atomic():
                    # Validate party list
                    primary_count = sum(1 for p in party_data if p.get('role') == 'PRIMARY')
                    if primary_count != 1:
                        return Response(
                            {"detail": "Party must include exactly one PRIMARY guest"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Create party members
                    for party_member in party_data:
                        role = party_member.get('role', 'COMPANION')
                        first_name = party_member.get('first_name', '').strip()
                        last_name = party_member.get('last_name', '').strip()
                        
                        if not first_name or not last_name:
                            return Response(
                                {"detail": "All party members must have first_name and last_name"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        # For PRIMARY, ensure it matches booking primary_* fields
                        if role == 'PRIMARY':
                            if (first_name != booking.primary_first_name or 
                                last_name != booking.primary_last_name):
                                # Auto-normalize: update booking to match party PRIMARY
                                booking.primary_first_name = first_name
                                booking.primary_last_name = last_name
                                booking.primary_email = party_member.get('email', '')
                                booking.primary_phone = party_member.get('phone', '')
                                booking.save()
                        
                        # Create BookingGuest (PRIMARY will be updated by save() method)
                        BookingGuest.objects.get_or_create(
                            booking=booking,
                            role=role,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': party_member.get('email', ''),
                                'phone': party_member.get('phone', ''),
                                'is_staying': True,
                            }
                        )
                        
            except Exception as e:
                return Response(
                    {"detail": f"Failed to create party: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Calculate pricing breakdown for response (reuse service logic)
        from hotel.services.pricing import (
            get_or_create_default_rate_plan,
            get_nightly_base_rates,
            apply_promotion,
            apply_taxes
        )
        
        rate_plan = get_or_create_default_rate_plan(hotel)
        nightly_rates = get_nightly_base_rates(room_type, check_in, check_out, rate_plan)
        subtotal = sum(price for _, price in nightly_rates)
        subtotal_after_promo, discount, promotion = apply_promotion(
            hotel, room_type, rate_plan, check_in, check_out, subtotal, promo_code
        )
        total, taxes = apply_taxes(subtotal_after_promo)
        
        # Return response using booking data
        booking_data = {
            "booking_id": booking.booking_id,
            "confirmation_number": booking.confirmation_number,
            "status": booking.status,
            "created_at": booking.created_at.isoformat(),
            "hotel": {
                "name": hotel.name,
                "slug": hotel.slug,
                "phone": hotel.phone,
                "email": hotel.email
            },
            "room": {
                "type": room_type.name,
                "code": room_type.code or room_type.name,
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
            "guest": {
                "name": booking.guest_name,
                "email": booking.guest_email,
                "phone": booking.guest_phone
            },
            "special_requests": special_requests,
            "pricing": {
                "subtotal": f"{subtotal:.2f}",
                "taxes": f"{taxes:.2f}",
                "discount": f"{discount:.2f}",
                "total": f"{total:.2f}",
                "currency": room_type.currency
            },
            "promo_code": promo_code if promo_code else None,
            "quote_id": quote_id if quote_id else None,
            "payment_required": True,
            "payment_url": (
                f"/api/hotel/{hotel.slug}/bookings/{booking.booking_id}/payment/session/"
            )
        }
        
        return Response(booking_data, status=status.HTTP_201_CREATED)
