"""
Payment cache utilities for idempotency and session management.

Provides functions to:
- Store and retrieve booking payment sessions
- Track processed webhook events
- Generate idempotency keys
- Prevent duplicate payments
"""

from django.core.cache import cache
from datetime import datetime, timedelta
import hashlib
import json


def generate_idempotency_key(booking_id, primary_email, total_amount=None, currency=None):
    """
    Generate a stable idempotency key for a booking (no date rotation).
    
    Args:
        booking_id: The booking ID
        primary_email: Primary guest email address
        total_amount: Total booking amount (optional, for extra stability)
        currency: Currency code (optional, for extra stability)
        
    Returns:
        Idempotency key string
    """
    # Stable key based on booking fundamentals (no date rotation)
    data_parts = [booking_id, primary_email]
    if total_amount:
        data_parts.append(str(total_amount))
    if currency:
        data_parts.append(str(currency))
    
    data = ":".join(data_parts)
    return f"booking_{hashlib.sha256(data.encode()).hexdigest()[:16]}"


def store_payment_session(booking_id, session_data, timeout=1800):
    """
    Store payment session data in cache.
    
    Args:
        booking_id: The booking ID
        session_data: Dictionary containing session information
        timeout: Cache timeout in seconds (default 30 minutes)
        
    Returns:
        True if stored successfully
    """
    cache_key = f"booking_session:{booking_id}"
    session_data['cached_at'] = datetime.utcnow().isoformat()
    session_data['expires_at'] = (datetime.utcnow() + timedelta(seconds=timeout)).isoformat()
    
    return cache.set(cache_key, session_data, timeout)


def get_payment_session(booking_id):
    """
    Retrieve payment session data from cache.
    
    Args:
        booking_id: The booking ID
        
    Returns:
        Session data dictionary or None if not found
    """
    cache_key = f"booking_session:{booking_id}"
    return cache.get(cache_key)


def get_or_create_payment_session(booking_id, create_func):
    """
    Get existing payment session or create new one.
    
    Args:
        booking_id: The booking ID
        create_func: Function to call if session doesn't exist
        
    Returns:
        Session data dictionary
    """
    existing_session = get_payment_session(booking_id)
    
    if existing_session:
        return existing_session, False  # False = not created
    
    # Create new session
    new_session = create_func()
    store_payment_session(booking_id, new_session)
    return new_session, True  # True = created


def delete_payment_session(booking_id):
    """
    Delete payment session from cache.
    
    Args:
        booking_id: The booking ID
        
    Returns:
        True if deleted successfully
    """
    cache_key = f"booking_session:{booking_id}"
    cache.delete(cache_key)
    return True


def is_webhook_processed(event_id):
    """
    Check if a webhook event has already been processed.
    
    Args:
        event_id: Stripe event ID
        
    Returns:
        True if already processed, False otherwise
    """
    cache_key = f"webhook_event:{event_id}"
    return cache.get(cache_key) is not None


def mark_webhook_processed(event_id, timeout=86400):
    """
    Mark a webhook event as processed.
    
    Args:
        event_id: Stripe event ID
        timeout: How long to remember (default 24 hours)
        
    Returns:
        True if marked successfully
    """
    cache_key = f"webhook_event:{event_id}"
    event_data = {
        'processed_at': datetime.utcnow().isoformat(),
        'event_id': event_id
    }
    return cache.set(cache_key, event_data, timeout)


def store_booking_metadata(booking_id, metadata, timeout=1800):
    """
    Store booking metadata for retrieval in webhook.
    
    Args:
        booking_id: The booking ID
        metadata: Dictionary of booking metadata
        timeout: Cache timeout in seconds (default 30 minutes)
        
    Returns:
        True if stored successfully
    """
    cache_key = f"booking_metadata:{booking_id}"
    return cache.set(cache_key, metadata, timeout)


def get_booking_metadata(booking_id):
    """
    Retrieve booking metadata from cache.
    
    Args:
        booking_id: The booking ID
        
    Returns:
        Metadata dictionary or None if not found
    """
    cache_key = f"booking_metadata:{booking_id}"
    return cache.get(cache_key)


def get_idempotency_session(idempotency_key):
    """
    Get Stripe session ID for an idempotency key.
    
    Args:
        idempotency_key: The idempotency key
        
    Returns:
        Session ID or None if not found
    """
    cache_key = f"idempotency:{idempotency_key}"
    return cache.get(cache_key)


def store_idempotency_session(idempotency_key, session_id, timeout=1800):
    """
    Store Stripe session ID with idempotency key.
    
    Args:
        idempotency_key: The idempotency key
        session_id: Stripe session ID
        timeout: Cache timeout in seconds (default 30 minutes)
        
    Returns:
        True if stored successfully
    """
    cache_key = f"idempotency:{idempotency_key}"
    return cache.set(cache_key, session_id, timeout)