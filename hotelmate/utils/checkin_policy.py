"""
Check-in Policy Schema + Defaults Resolver

Single source of truth for all check-in policy configuration.
Reads from HotelSettings JSON and injects defaults for missing values.
"""
import pytz
from datetime import time
from typing import Dict, Any
from django.utils import timezone


# Default policy values (Europe/Dublin timezone for Ireland-first approach)
DEFAULT_CHECKIN_POLICY = {
    'timezone': 'Europe/Dublin',
    'check_in_time': '15:00',
    'early_checkin_from': '12:00', 
    'late_arrival_cutoff': '02:00'
}


def get_checkin_policy(hotel) -> Dict[str, Any]:
    """
    Returns complete check-in policy with defaults for missing values.
    
    If keys are missing in settings JSON, resolver injects defaults 
    and returns a complete policy object (but doesn't persist it yet).
    
    Args:
        hotel: Hotel model instance
        
    Returns:
        dict: Complete policy configuration with validated format
        
    Schema:
        - timezone: str (pytz timezone name)
        - check_in_time: str (HH:MM format)
        - early_checkin_from: str (HH:MM format)
        - late_arrival_cutoff: str (HH:MM format)
    """
    # Start with default policy
    policy = DEFAULT_CHECKIN_POLICY.copy()
    
    # Try to get hotel-specific settings from JSON
    try:
        # Check if hotel has settings - could be various models/approaches
        hotel_settings = {}
        
        # Option 1: Check for precheckin_config with checkin_policy field
        if hasattr(hotel, 'precheckin_config') and hotel.precheckin_config:
            checkin_settings = getattr(hotel.precheckin_config, 'checkin_policy', {})
            if isinstance(checkin_settings, dict):
                hotel_settings.update(checkin_settings)
        
        # Option 2: Check for direct hotel JSON field (if it exists)
        if hasattr(hotel, 'settings') and hotel.settings:
            checkin_settings = hotel.settings.get('checkin_policy', {})
            if isinstance(checkin_settings, dict):
                hotel_settings.update(checkin_settings)
                
        # Update policy with hotel-specific values
        for key in DEFAULT_CHECKIN_POLICY.keys():
            if key in hotel_settings:
                policy[key] = hotel_settings[key]
                
    except (AttributeError, TypeError, ValueError):
        # Fall back to defaults if any error reading hotel settings
        pass
    
    # Validate and normalize policy values
    policy = _validate_policy_format(policy)
    
    return policy


def _validate_policy_format(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and normalizes policy format.
    Ensures HH:MM time format and valid timezone strings.
    """
    validated_policy = policy.copy()
    
    # Validate timezone
    try:
        pytz.timezone(policy['timezone'])
    except (pytz.exceptions.UnknownTimeZoneError, KeyError):
        validated_policy['timezone'] = DEFAULT_CHECKIN_POLICY['timezone']
    
    # Validate time formats (HH:MM)
    time_fields = ['check_in_time', 'early_checkin_from', 'late_arrival_cutoff']
    
    for field in time_fields:
        try:
            time_str = policy.get(field, DEFAULT_CHECKIN_POLICY[field])
            # Parse to validate format
            time.fromisoformat(time_str)
            validated_policy[field] = time_str
        except (ValueError, TypeError):
            validated_policy[field] = DEFAULT_CHECKIN_POLICY[field]
    
    return validated_policy


def get_hotel_now(hotel):
    """
    Get current time in hotel's local timezone.
    
    Args:
        hotel: Hotel model instance
        
    Returns:
        datetime: Current time in hotel timezone
    """
    policy = get_checkin_policy(hotel)
    hotel_tz = pytz.timezone(policy['timezone'])
    
    # Get current UTC time and convert to hotel timezone
    utc_now = timezone.now()
    return utc_now.astimezone(hotel_tz)
