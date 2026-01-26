"""
Booking deadline computation service for approval SLA management.

Handles calculation of approval deadlines for bookings in PENDING_APPROVAL status,
ensuring staff have clear SLAs for processing paid bookings.
"""
from datetime import timedelta, time
from django.utils import timezone
from typing import Optional


def compute_approval_deadline(booking, *, base_dt: Optional[timezone.datetime] = None) -> timezone.datetime:
    """
    Compute the approval deadline for a booking based on hotel SLA settings.
    
    Args:
        booking: RoomBooking instance
        base_dt: Base datetime for deadline calculation (defaults to paid_at or created_at)
    
    Returns:
        Timezone-aware datetime when approval deadline expires
    """
    if base_dt is None:
        # Use payment timestamp if available, otherwise creation timestamp
        base_dt = booking.paid_at if booking.paid_at else booking.created_at
    
    # Get hotel's approval SLA configuration
    hotel_config = getattr(booking.hotel, 'access_config', None)
    if hotel_config:
        sla_minutes = hotel_config.approval_sla_minutes
    else:
        # Default SLA if no configuration exists
        sla_minutes = 30
    
    return base_dt + timedelta(minutes=sla_minutes)


def compute_approval_cutoff(booking) -> timezone.datetime:
    """
    Compute the approval cutoff (hard expiry time) for a booking.
    
    Rule: Uses hotel-configured cutoff time and day offset relative to check-in.
    After this time, bookings are auto-expired with refund.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Timezone-aware datetime when booking expires (UTC)
    """
    # Get hotel configuration
    hotel_config = booking.hotel.access_config
    
    # Use hotel-configured cutoff time and day offset
    cutoff_time = hotel_config.approval_cutoff_time
    day_offset = hotel_config.approval_cutoff_day_offset
    
    # Compute cutoff date (check-in + offset)
    cutoff_date = booking.check_in + timedelta(days=day_offset)
    
    # Create timezone-aware datetime
    hotel_tz = booking.hotel.timezone_obj
    cutoff_local = hotel_tz.localize(
        timezone.datetime.combine(cutoff_date, cutoff_time)
    )
    
    # Convert to UTC for consistent storage/comparison
    return cutoff_local.astimezone(timezone.utc)


def should_set_approval_deadline(booking) -> bool:
    """
    Check if a booking should have an approval deadline set.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        True if booking needs approval deadline tracking
    """
    return (
        booking.status == 'PENDING_APPROVAL' and
        booking.paid_at is not None and
        booking.approval_deadline_at is None
    )


def is_approval_overdue(booking) -> bool:
    """
    Check if a booking's approval deadline has passed.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        True if approval deadline has passed
    """
    if not booking.approval_deadline_at:
        return False
    
    return timezone.now() > booking.approval_deadline_at


def get_approval_overdue_minutes(booking) -> int:
    """
    Get how many minutes a booking approval is overdue.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Minutes overdue (0 if not overdue or no deadline)
    """
    if not booking.approval_deadline_at or not is_approval_overdue(booking):
        return 0
    
    delta = timezone.now() - booking.approval_deadline_at
    return int(delta.total_seconds() / 60)


def get_approval_risk_level(booking) -> str:
    """
    Determine approval risk level for staff warnings.
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        Risk level: 'OK', 'DUE_SOON', 'OVERDUE', 'CRITICAL'
    """
    if not booking.approval_deadline_at:
        return 'OK'
    
    now = timezone.now()
    deadline = booking.approval_deadline_at
    
    if now > deadline:
        # Already overdue - check how long
        overdue_minutes = get_approval_overdue_minutes(booking)
        if overdue_minutes > 60:
            return 'CRITICAL'
        return 'OVERDUE'
    
    # Not yet overdue - check how soon
    minutes_until_deadline = int((deadline - now).total_seconds() / 60)
    if minutes_until_deadline <= 10:
        return 'DUE_SOON'
    
    return 'OK'