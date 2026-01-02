"""
Booking Service

Room booking creation with integrated pricing engine.
Reuses pricing service logic for consistent calculations.

No DRF dependencies - pure business logic.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.utils import timezone
from django.http import Http404

from hotel.models import Hotel, RoomBooking, GuestBookingToken
from rooms.models import RoomType

# Import from pricing service to reuse logic
from hotel.services.pricing import (
    get_or_create_default_rate_plan,
    get_nightly_base_rates,
    apply_promotion,
    apply_taxes
)


def create_room_booking_from_request(
    hotel: Hotel,
    room_type: RoomType,
    check_in: date,
    check_out: date,
    adults: int,
    children: int,
    primary_first_name: str,
    primary_last_name: str,
    primary_email: str,
    primary_phone: str,
    booker_type: str,
    booker_first_name: str = '',
    booker_last_name: str = '',
    booker_email: str = '',
    booker_phone: str = '',
    booker_company: str = '',
    special_requests: str = '',
    promo_code: str = ''
) -> RoomBooking:
    """
    Create a RoomBooking with proper pricing calculation using NEW field structure.
    
    Reuses pricing service logic to ensure:
    - Consistent nightly rate calculation
    - Proper promotion application
    - Correct tax calculation
    
    Args:
        hotel: Hotel instance
        room_type: RoomType instance
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adults
        children: Number of children
        primary_first_name: Primary staying guest first name
        primary_last_name: Primary staying guest last name
        primary_email: Primary staying guest email
        primary_phone: Primary staying guest phone
        booker_type: SELF, THIRD_PARTY, or COMPANY
        booker_first_name: Booker first name (if different from primary)
        booker_last_name: Booker last name (if different from primary)
        booker_email: Booker email (if different from primary)
        booker_phone: Booker phone (if different from primary)
        booker_company: Company name (for COMPANY bookings)
        special_requests: Guest special requests text
        promo_code: Optional promo code
    
    Returns:
        Newly created RoomBooking instance with status='PENDING_PAYMENT'
    
    Note:
        This does NOT modify any existing bookings.
        Only new bookings use the new pricing engine.
        Historical data is preserved as audit trail.
    """
    # Get rate plan
    rate_plan = get_or_create_default_rate_plan(hotel)
    
    # Calculate nightly rates using pricing service
    nightly_rates = get_nightly_base_rates(room_type, check_in, check_out, rate_plan)
    nights = len(nightly_rates)
    
    # Calculate subtotal
    subtotal = sum(price for _, price in nightly_rates)
    
    # Apply promotion using pricing service
    subtotal_after_promo, discount, promotion = apply_promotion(
        hotel, room_type, rate_plan, check_in, check_out, subtotal, promo_code
    )
    
    # Apply taxes using pricing service
    total, taxes = apply_taxes(subtotal_after_promo)
    
    # Create RoomBooking instance using NEW canonical fields
    # Uses existing auto-generation logic for booking_id and confirmation_number
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        # Primary staying guest (ALWAYS required)
        primary_first_name=primary_first_name,
        primary_last_name=primary_last_name,
        primary_email=primary_email,
        primary_phone=primary_phone,
        # Booker information (may differ from primary)
        booker_type=booker_type,
        booker_first_name=booker_first_name,
        booker_last_name=booker_last_name,
        booker_email=booker_email,
        booker_phone=booker_phone,
        booker_company=booker_company,
        # Occupancy and pricing
        adults=adults,
        children=children,
        total_amount=total,
        currency=room_type.currency,
        status='PENDING_PAYMENT',
        special_requests=special_requests,
        promo_code=promo_code if promo_code else '',
        # Policy snapshotting: snapshot cancellation policy from rate plan at creation time
        rate_plan=rate_plan,  # Store rate plan reference for debugging
        cancellation_policy=(
            rate_plan.cancellation_policy or 
            hotel.default_cancellation_policy
        ),
        # Booking expiration: Set 15-minute expiration for unpaid bookings
        expires_at=timezone.now() + timedelta(minutes=15)
    )
    
    # Phase 3: The PRIMARY BookingGuest will be auto-created by the save() method
    # Additional party members can be added separately via staff API
    
    # Booking created successfully - email will be sent after payment completion
    print(f"✅ Booking {booking.booking_id} created, management email will be sent after payment")
    
    return booking


def resolve_token_context(raw_token: str) -> Dict:
    """
    Validate guest booking token and return booking context.
    
    Args:
        raw_token: The raw token string from request
        
    Returns:
        Dict containing booking context with assigned_room as room source
        
    Raises:
        Http404: If token is invalid, expired, or booking not found
        
    Context structure:
    {
        'booking_id': str,
        'hotel_slug': str,
        'assigned_room': {
            'room_number': str,
            'room_type_name': str
        } or None,
        'guest_name': str,
        'check_in': date,
        'check_out': date,
        'status': str,
        'party_size': int,
        'is_checked_in': bool,
        'is_checked_out': bool,
        'allowed_actions': list[str]
    }
    """
    # Validate token and get token object
    token = GuestBookingToken.validate_token(raw_token)
    booking = token.booking
    
    # Build context using assigned_room as room source of truth
    room_info = None
    if booking.assigned_room:
        room_info = {
            'room_number': booking.assigned_room.room_number,
            'room_type_name': booking.assigned_room.room_type.name
        }
    
    # Determine allowed actions based on token scopes and booking state
    allowed_actions = []
    
    # Always check token scopes first
    token_scopes = getattr(token, 'scopes', [])
    
    # Status read access
    if 'STATUS_READ' in token_scopes:
        allowed_actions.append('view_booking')
    
    # Chat access - requires CHAT scope + confirmed/checked-in status
    if ('CHAT' in token_scopes and 
        booking.status in ['CONFIRMED', 'CHECKED_IN']):
        allowed_actions.append('chat')
    
    # Room service - requires ROOM_SERVICE scope + checked in + assigned room
    if ('ROOM_SERVICE' in token_scopes and 
        booking.status == 'CHECKED_IN' and booking.assigned_room):
        allowed_actions.append('room_service')
    
    return {
        'booking_id': booking.booking_id,
        'hotel_slug': booking.hotel.slug,
        'assigned_room': room_info,
        'guest_name': booking.primary_guest_name,
        'check_in': booking.check_in,
        'check_out': booking.check_out,
        'status': booking.status,
        'party_size': booking.adults + booking.children,
        'is_checked_in': booking.status == 'CHECKED_IN',
        'is_checked_out': booking.status == 'CHECKED_OUT',
        'allowed_actions': allowed_actions
    }


def resolve_in_house_context(raw_token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Check if guest is currently in-house and return room context.
    
    Uses assigned_room and check-in/out status as source of truth.
    No dependency on RoomOccupancy model.
    
    Args:
        raw_token: The raw token string from request
        
    Returns:
        Tuple of (is_in_house: bool, room_context: Dict or None)
        
    Raises:
        Http404: If token is invalid, expired, or booking not found
        
    Room context structure when in-house:
    {
        'room_number': str,
        'room_type_name': str,
        'floor': str or None,
        'amenities': list[str],
        'check_in_time': datetime,
        'expected_checkout': date
    }
    """
    # Validate token and get booking
    token = GuestBookingToken.validate_token(raw_token)
    booking = token.booking
    
    # Guest is in-house if:
    # 1. Status is CHECKED_IN
    # 2. Has assigned room
    # 3. Current date is within stay period
    current_date = timezone.now().date()
    is_in_house = (
        booking.status == 'CHECKED_IN' and
        booking.assigned_room is not None and
        booking.check_in <= current_date <= booking.check_out
    )
    
    if not is_in_house:
        return False, None
    
    # Build room context
    room = booking.assigned_room
    room_context = {
        'room_number': room.room_number,
        'room_type_name': room.room_type.name,
        'floor': room.floor,
        'amenities': room.room_type.amenities or [],
        'check_in_time': booking.actual_check_in_time,
        'expected_checkout': booking.check_out_date
    }
    
    return True, room_context
