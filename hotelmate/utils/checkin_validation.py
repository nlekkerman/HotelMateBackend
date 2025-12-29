"""
Check-in Validation - Single Gatekeeper Function

Single responsibility for all check-in business rule validation.
Prevents rule sprawl across multiple views.
"""
from datetime import datetime, time
from typing import Tuple
from .checkin_policy import get_checkin_policy, get_hotel_now


# Error codes as API contract
CHECKIN_ERROR_CODES = {
    'CHECKIN_TOO_EARLY': 'Check-in not allowed before {time}',
    'CHECKIN_WRONG_DATE': 'Check-in only allowed on arrival date {date}',
    'CHECKIN_TOO_LATE': 'Late arrival cutoff exceeded at {cutoff}',
    'ROOM_NOT_READY': 'Room {room} not ready for guest occupancy',
    'BOOKING_NOT_ELIGIBLE': 'Booking not eligible for check-in: {reason}'
}


def validate_checkin(booking, room, policy, now_local) -> Tuple[bool, str, str]:
    """
    Single gatekeeper for all check-in business rules.
    
    Args:
        booking: RoomBooking model instance
        room: Room model instance (booking.assigned_room)
        policy: Policy dict from get_checkin_policy()
        now_local: Current time in hotel timezone
        
    Returns:
        tuple: (ok: bool, code: str, detail: str)
        
    Validates:
    - Booking status (CONFIRMED/APPROVED only)
    - Room assignment and readiness (READY_FOR_GUEST required)
    - Arrival window + early/late policy (exact window rules below)
    - Already checked-in → returns ok=True (idempotent success)
    """
    
    # 1. Booking eligibility (status, assigned room, idempotency)
    if booking.checked_in_at:
        # Already checked in - return idempotent success
        return True, '', 'Already checked in'
    
    # Check booking status
    eligible_statuses = ['CONFIRMED', 'APPROVED']
    if booking.status not in eligible_statuses:
        return False, 'BOOKING_NOT_ELIGIBLE', f'Status {booking.status} not eligible for check-in'
    
    # Check room assignment
    if not room:
        return False, 'BOOKING_NOT_ELIGIBLE', 'No room assigned to booking'
    
    # 2. Room readiness (READY_FOR_GUEST, not OUT_OF_ORDER/MAINTENANCE_REQUIRED)
    if not hasattr(room, 'room_status'):
        return False, 'ROOM_NOT_READY', f'Room {room.room_number} status unknown'
    
    if room.room_status != 'READY_FOR_GUEST':
        if room.room_status in ['OUT_OF_ORDER', 'MAINTENANCE_REQUIRED']:
            return False, 'ROOM_NOT_READY', f'Room {room.room_number} is {room.room_status.lower().replace("_", " ")}'
        else:
            return False, 'ROOM_NOT_READY', f'Room {room.room_number} not ready (status: {room.room_status})'
    
    # 3. Arrival window + early/late policy (exact rules)
    arrival_valid, arrival_code, arrival_detail = _validate_arrival_window(
        booking, policy, now_local
    )
    
    if not arrival_valid:
        return False, arrival_code, arrival_detail
    
    # All validations passed
    return True, '', 'Check-in validation passed'


def _validate_arrival_window(booking, policy, now_local) -> Tuple[bool, str, str]:
    """
    Validate arrival date and time window with early/late policies.
    
    Exact rules:
    - local_date == check_in_date AND local_time >= check_in_time
    - OR local_date == check_in_date + 1 AND local_time <= late_arrival_cutoff
    """
    local_date = now_local.date()
    local_time = now_local.time()
    
    check_in_date = booking.check_in
    
    # Parse policy times
    check_in_time = time.fromisoformat(policy['check_in_time'])
    early_checkin_from = time.fromisoformat(policy['early_checkin_from'])
    late_arrival_cutoff = time.fromisoformat(policy['late_arrival_cutoff'])
    
    # Check if it's the correct arrival date
    if local_date == check_in_date:
        # Same day check-in
        
        # Check if before early check-in window
        if local_time < early_checkin_from:
            return False, 'CHECKIN_TOO_EARLY', f'Check-in not allowed before {policy["early_checkin_from"]}'
        
        # Check if in early check-in window (between early_checkin_from and check_in_time)
        if early_checkin_from <= local_time < check_in_time:
            # Early check-in is allowed by default between 12:00-15:00
            # Future: could add hotel-specific early check-in policies here
            return True, '', 'Early check-in allowed'
        
        # Normal check-in time (after check_in_time)
        if local_time >= check_in_time:
            return True, '', 'Normal check-in time'
            
    elif local_date == check_in_date + timedelta(days=1):
        # Next day (late arrival)
        if local_time <= late_arrival_cutoff:
            return True, '', 'Late arrival allowed'
        else:
            return False, 'CHECKIN_TOO_LATE', f'Late arrival cutoff exceeded at {policy["late_arrival_cutoff"]}'
    
    # Wrong date (too early or too late)
    if local_date < check_in_date:
        return False, 'CHECKIN_WRONG_DATE', f'Check-in not allowed before arrival date {check_in_date}'
    else:
        return False, 'CHECKIN_TOO_LATE', f'Check-in window closed for booking date {check_in_date}'


# Import timedelta for date calculations
from datetime import timedelta
