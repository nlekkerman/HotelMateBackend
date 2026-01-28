"""
Hotel timezone utilities for date/time handling.

Provides timezone-aware date and datetime operations scoped to hotel's local timezone.
Prevents UTC "today" bugs in operational filtering.
"""
from datetime import date, datetime, time, timedelta
from typing import Tuple
import pytz
from django.utils import timezone


def hotel_today(hotel) -> date:
    """
    Get today's date in the hotel's timezone.
    
    Args:
        hotel: Hotel instance with timezone field
        
    Returns:
        date: Today's date in hotel timezone
    """
    hotel_tz = pytz.timezone(hotel.timezone)
    now_hotel = timezone.now().astimezone(hotel_tz)
    return now_hotel.date()


def hotel_day_range_utc(hotel, target_date: date) -> Tuple[datetime, datetime]:
    """
    Convert a hotel-local date to UTC datetime range (start of day to end of day).
    
    Args:
        hotel: Hotel instance with timezone field
        target_date: Date in hotel's timezone
        
    Returns:
        Tuple[datetime, datetime]: (start_utc_dt, end_utc_dt)
        
    Example:
        For hotel in EST and target_date=2026-01-28:
        Returns (2026-01-28 05:00:00+00:00, 2026-01-29 04:59:59.999999+00:00)
    """
    hotel_tz = pytz.timezone(hotel.timezone)
    
    # Start of day in hotel timezone
    start_hotel = hotel_tz.localize(datetime.combine(target_date, time.min))
    
    # End of day in hotel timezone (23:59:59.999999)
    end_hotel = hotel_tz.localize(
        datetime.combine(target_date, time.max)
    )
    
    # Convert to UTC
    start_utc = start_hotel.astimezone(pytz.UTC)
    end_utc = end_hotel.astimezone(pytz.UTC)
    
    return start_utc, end_utc


def hotel_date_range_utc(hotel, date_from: date, date_to: date) -> Tuple[datetime, datetime]:
    """
    Convert hotel-local date range to UTC datetime range.
    
    Args:
        hotel: Hotel instance with timezone field
        date_from: Start date in hotel timezone
        date_to: End date in hotel timezone (inclusive)
        
    Returns:
        Tuple[datetime, datetime]: (start_utc_dt, end_utc_dt)
        
    Example:
        For hotel in EST, date_from=2026-01-28, date_to=2026-01-30:
        Returns (2026-01-28 05:00:00+00:00, 2026-01-31 04:59:59.999999+00:00)
    """
    hotel_tz = pytz.timezone(hotel.timezone)
    
    # Start of first day in hotel timezone
    start_hotel = hotel_tz.localize(datetime.combine(date_from, time.min))
    
    # End of last day in hotel timezone
    end_hotel = hotel_tz.localize(
        datetime.combine(date_to, time.max)
    )
    
    # Convert to UTC
    start_utc = start_hotel.astimezone(pytz.UTC)
    end_utc = end_hotel.astimezone(pytz.UTC)
    
    return start_utc, end_utc


def hotel_checkout_deadline_utc(hotel, check_out_date: date) -> datetime:
    """
    Calculate checkout deadline in UTC for overdue detection.
    
    Uses hotel's checkout_time setting (default 11:00 AM hotel time).
    
    Args:
        hotel: Hotel instance with timezone and checkout_time fields
        check_out_date: Check-out date in hotel timezone
        
    Returns:
        datetime: Checkout deadline in UTC
    """
    hotel_tz = pytz.timezone(hotel.timezone)
    
    # Get hotel's checkout time (default to 11:00 if not set)
    checkout_time = getattr(hotel, 'checkout_time', time(11, 0))
    
    # Checkout deadline in hotel timezone
    deadline_hotel = hotel_tz.localize(
        datetime.combine(check_out_date, checkout_time)
    )
    
    # Convert to UTC
    deadline_utc = deadline_hotel.astimezone(pytz.UTC)
    
    return deadline_utc


def hotel_now_utc(hotel) -> datetime:
    """
    Get current UTC datetime for hotel timezone calculations.
    
    Args:
        hotel: Hotel instance (for consistency, though not used)
        
    Returns:
        datetime: Current UTC datetime
    """
    return timezone.now()


def is_overdue_checkout(hotel, check_out_date: date, checked_out_at: datetime = None) -> bool:
    """
    Check if a booking is overdue for checkout.
    
    Args:
        hotel: Hotel instance
        check_out_date: Scheduled checkout date
        checked_out_at: Actual checkout datetime (None if not checked out)
        
    Returns:
        bool: True if overdue (past deadline and not checked out)
    """
    if checked_out_at is not None:
        return False  # Already checked out
    
    deadline_utc = hotel_checkout_deadline_utc(hotel, check_out_date)
    now_utc = hotel_now_utc(hotel)
    
    return now_utc > deadline_utc