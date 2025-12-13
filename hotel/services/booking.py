"""
Booking Service

Room booking creation with integrated pricing engine.
Reuses pricing service logic for consistent calculations.

No DRF dependencies - pure business logic.
"""
from datetime import date
from decimal import Decimal
from typing import Dict

from hotel.models import Hotel, RoomBooking
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
    guest_data: Dict,
    special_requests: str,
    promo_code: str
) -> RoomBooking:
    """
    Create a RoomBooking with proper pricing calculation.
    
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
        guest_data: Dict with keys: first_name, last_name, email, phone
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
    
    # Create RoomBooking instance with Phase 2 primary_* fields
    # Uses existing auto-generation logic for booking_id and confirmation_number
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        # Phase 2: Use primary_* fields instead of guest_*
        primary_first_name=guest_data['first_name'],
        primary_last_name=guest_data['last_name'],
        primary_email=guest_data['email'],
        primary_phone=guest_data['phone'],
        booker_type='SELF',  # Default to self-booking for public API
        adults=adults,
        children=children,
        total_amount=total,
        currency=room_type.currency,
        status='PENDING_PAYMENT',
        special_requests=special_requests,
        promo_code=promo_code if promo_code else ''
    )
    
    # Phase 3: The PRIMARY BookingGuest will be auto-created by the save() method
    # Additional party members can be added separately via staff API
    
    return booking
