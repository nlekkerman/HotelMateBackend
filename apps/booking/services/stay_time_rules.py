"""
Stay time rules service for checkout deadline and overstay management.

Handles computation of checkout deadlines and overstay detection for IN_HOUSE bookings,
ensuring guests cannot remain checked-in indefinitely without staff awareness.
"""
from datetime import datetime, time, timedelta
from django.utils import timezone
from typing import Optional


def compute_checkout_deadline(booking) -> timezone.datetime:
    """
    Compute the checkout deadline for a booking based on hotel checkout time + grace.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Timezone-aware datetime when checkout deadline expires
    """
    # Get hotel checkout time configuration
    hotel_config = getattr(booking.hotel, 'access_config', None)
    if hotel_config:
        checkout_time = hotel_config.standard_checkout_time
        grace_minutes = hotel_config.late_checkout_grace_minutes
    else:
        # Default settings if no configuration exists
        checkout_time = time(11, 0)  # 11:00 AM
        grace_minutes = 30
    
    # Combine checkout date with hotel's checkout time
    checkout_datetime = timezone.make_aware(
        datetime.combine(booking.check_out, checkout_time)
    )
    
    # Add grace period
    return checkout_datetime + timedelta(minutes=grace_minutes)


def is_overstay(booking) -> bool:
    """
    Check if a booking is currently in overstay (past checkout deadline).
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        True if booking is past checkout deadline and still checked in
    """
    # Must be checked in and not yet checked out
    if not booking.checked_in_at or booking.checked_out_at:
        return False
    
    checkout_deadline = compute_checkout_deadline(booking)
    return timezone.now() > checkout_deadline


def get_overstay_minutes(booking) -> int:
    """
    Get how many minutes a booking is in overstay.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Minutes in overstay (0 if not in overstay)
    """
    if not is_overstay(booking):
        return 0
    
    checkout_deadline = compute_checkout_deadline(booking)
    delta = timezone.now() - checkout_deadline
    return int(delta.total_seconds() / 60)


def get_overstay_risk_level(booking) -> str:
    """
    Determine overstay risk level for staff warnings.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Risk level: 'OK', 'GRACE', 'OVERDUE', 'CRITICAL'
    """
    if not booking.checked_in_at or booking.checked_out_at:
        return 'OK'
    
    now = timezone.now()
    checkout_deadline = compute_checkout_deadline(booking)
    
    if now > checkout_deadline:
        # In overstay - check severity
        overstay_minutes = get_overstay_minutes(booking)
        if overstay_minutes > 120:  # More than 2 hours
            return 'CRITICAL'
        return 'OVERDUE'
    
    # Still within grace - check how close
    minutes_until_deadline = int((checkout_deadline - now).total_seconds() / 60)
    
    # Get grace period to determine if in grace window
    hotel_config = getattr(booking.hotel, 'access_config', None)
    grace_minutes = hotel_config.late_checkout_grace_minutes if hotel_config else 30
    
    # If within grace period of standard checkout time, show as GRACE
    standard_checkout = timezone.make_aware(
        datetime.combine(booking.check_out, 
                        hotel_config.standard_checkout_time if hotel_config else time(11, 0))
    )
    
    if now > standard_checkout:
        return 'GRACE'
    
    return 'OK'


def should_flag_overstay(booking) -> bool:
    """
    Check if a booking should be flagged for overstay (for background job).
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        True if booking should be flagged for overstay
    """
    return (
        is_overstay(booking) and
        booking.overstay_flagged_at is None
    )


def can_extend_stay(booking, new_check_out) -> tuple[bool, str]:
    """
    Check if a stay can be extended to a new checkout date.
    
    Args:
        booking: RoomBooking instance
        new_check_out: New checkout date
    
    Returns:
        Tuple of (can_extend: bool, reason: str)
    """
    if not booking.checked_in_at and booking.status != 'CONFIRMED':
        return False, "Booking must be checked-in or CONFIRMED to extend"
    
    if booking.checked_out_at:
        return False, "Cannot extend stay for already checked-out booking"
    
    if new_check_out <= booking.check_out:
        return False, "New checkout date must be after current checkout date"
    
    # TODO: Add availability checking logic here
    # For now, allow extensions (to be implemented later with room availability service)
    
    return True, "Extension allowed"


def clear_overstay_flags_if_resolved(booking, new_check_out) -> bool:
    """
    Check if extending checkout date resolves overstay situation.
    
    Args:
        booking: RoomBooking instance
        new_check_out: New checkout date
    
    Returns:
        True if overstay flags should be cleared
    """
    if not booking.overstay_flagged_at:
        return False
    
    # Create a temporary booking copy to test new deadline
    temp_booking = type(booking)(
        **{field.name: getattr(booking, field.name) 
           for field in booking._meta.fields if hasattr(booking, field.name)}
    )
    temp_booking.check_out = new_check_out
    
    # If new deadline is in the future, overstay is resolved
    new_deadline = compute_checkout_deadline(temp_booking)
    return timezone.now() <= new_deadline