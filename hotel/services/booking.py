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
        cancellation_policy=rate_plan.cancellation_policy if rate_plan.cancellation_policy else None
    )
    
    # Phase 3: The PRIMARY BookingGuest will be auto-created by the save() method
    # Additional party members can be added separately via staff API
    
    return booking
