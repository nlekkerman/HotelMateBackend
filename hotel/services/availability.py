"""
Availability Service

Real inventory checking using:
- Physical Room counts
- RoomTypeInventory overrides (stop-sell, inventory adjustments)
- RoomBooking overlap analysis

No DRF dependencies - pure business logic.
"""
from datetime import date, timedelta
from typing import List, Dict, Tuple

from hotel.models import Hotel
from rooms.models import Room, RoomType, RoomTypeInventory


def validate_dates(check_in_str: str, check_out_str: str) -> Tuple[date, date, int]:
    """
    Parse and validate check_in / check_out strings.
    
    Args:
        check_in_str: Date string in YYYY-MM-DD format
        check_out_str: Date string in YYYY-MM-DD format
    
    Returns:
        Tuple of (check_in, check_out, nights)
    
    Raises:
        ValueError: If dates are invalid or check_out <= check_in
    """
    from datetime import datetime
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")
    
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")
    
    nights = (check_out - check_in).days
    return check_in, check_out, nights


def _inventory_for_date(room_type: RoomType, day: date) -> int:
    """
    Internal helper: Calculate available inventory for a room type on a specific date.
    
    Priority:
    1. If RoomTypeInventory exists for this date:
       - If stop_sell=True -> return 0
       - If total_rooms is set -> return total_rooms
       - Otherwise fall through to physical count
    2. Count physical Room instances for this hotel and room type where is_active=True
    
    Args:
        room_type: RoomType instance
        day: Date to check inventory for
    
    Returns:
        Number of available rooms
    """
    try:
        inventory = RoomTypeInventory.objects.get(room_type=room_type, date=day)
        
        # Stop-sell takes priority
        if inventory.stop_sell:
            return 0
        
        # If total_rooms override is set, use it
        if inventory.total_rooms is not None:
            return inventory.total_rooms
    except RoomTypeInventory.DoesNotExist:
        pass
    
    # Fallback: count physical rooms for this specific room type that are bookable
    # Updated for Room Turnover Workflow - only count bookable rooms
    # Fix: Filter by room_type, not just hotel
    bookable_rooms = Room.objects.filter(
        room_type=room_type  # This is the fix - filter by specific room type
    )
    
    # Apply is_bookable() logic inline since we can't call method in QuerySet
    # is_bookable() checks: room_status in {'AVAILABLE', 'READY_FOR_GUEST'} 
    # and is_active and not maintenance_required and not is_out_of_order
    room_count = bookable_rooms.filter(
        room_status__in=['READY_FOR_GUEST'],
        is_active=True,
        maintenance_required=False,
        is_out_of_order=False
    ).count()
    
    return room_count


def _booked_for_date(room_type: RoomType, day: date) -> int:
    """
    Internal helper: Count bookings overlapping a specific date.
    
    Counts RoomBooking records where:
    - room_type matches
    - status is PENDING_PAYMENT or CONFIRMED
    - check_in <= day < check_out (overnight hotel logic)
    - PENDING_PAYMENT bookings are only counted if not expired
    
    Args:
        room_type: RoomType instance
        day: Date to check bookings for
    
    Returns:
        Number of rooms booked for this date
    """
    # Import here to avoid circular imports
    from hotel.models import RoomBooking
    from django.db.models import Q
    from django.utils import timezone
    
    now = timezone.now()
    
    # Bookings overlap this date if: check_in <= day < check_out
    # CONFIRMED always blocks inventory
    # PENDING_PAYMENT only blocks if expires_at > now (not expired)
    overlapping_bookings = RoomBooking.objects.filter(
        room_type=room_type,
        check_in__lte=day,
        check_out__gt=day
    ).filter(
        Q(status='CONFIRMED') |  # CONFIRMED always blocks
        (
            Q(status='PENDING_PAYMENT') & 
            (Q(expires_at__isnull=True) | Q(expires_at__gt=now))  # Not expired
        )
    ).count()
    
    return overlapping_bookings


def is_room_type_available(
    room_type: RoomType,
    check_in: date,
    check_out: date,
    required_units: int = 1
) -> bool:
    """
    Check if a RoomType has at least required_units available rooms
    for every night in [check_in, check_out).
    
    Args:
        room_type: RoomType instance
        check_in: Check-in date
        check_out: Check-out date
        required_units: Number of rooms required (default 1)
    
    Returns:
        True if available for all nights, False otherwise
    """
    current_date = check_in
    
    while current_date < check_out:
        inventory = _inventory_for_date(room_type, current_date)
        booked = _booked_for_date(room_type, current_date)
        available = inventory - booked
        
        if available < required_units:
            return False
        
        current_date += timedelta(days=1)
    
    return True


def get_room_type_availability(
    hotel: Hotel,
    check_in: date,
    check_out: date,
    adults: int,
    children: int
) -> List[Dict]:
    """
    For a given hotel and date range, return a list of room types with availability info.
    
    Each returned dict includes:
    - room_type_code: str
    - room_type_name: str
    - can_accommodate: bool (based on max_occupancy)
    - is_available: bool (based on real inventory)
    - max_occupancy: int
    - bed_setup: str
    - short_description: str
    - photo: str (URL or None)
    - starting_price_from: str
    - currency: str
    - availability_message: str
    - note: str or None (capacity issue message)
    
    Args:
        hotel: Hotel instance
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adults
        children: Number of children
    
    Returns:
        List of availability dicts
    """
    room_types = hotel.room_types.filter(
        is_active=True
    ).select_related('hotel').order_by('sort_order', 'name')
    
    available_rooms = []
    total_guests = adults + children
    
    for room_type in room_types:
        # Check capacity
        can_accommodate = room_type.max_occupancy >= total_guests
        
        # Check real availability (inventory vs bookings)
        is_available = can_accommodate and is_room_type_available(
            room_type, check_in, check_out, required_units=1
        )
        
        # Build room data dict
        room_data = {
            "room_type_code": room_type.code or room_type.name,
            "room_type_name": room_type.name,
            "is_available": is_available,
            "can_accommodate": can_accommodate,
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
                f"Maximum occupancy is {room_type.max_occupancy} guests"
            )
        elif not is_available:
            room_data["note"] = "No availability for selected dates"
        
        available_rooms.append(room_data)
    
    return available_rooms
