"""
Guest portal services for token-based authentication and access control.
This module provides the core authentication and authorization logic for
guest portal features including chat, room service, and other guest-facing APIs.
"""

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from hotel.models import GuestBookingToken, RoomBooking
from chat.models import Conversation
import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_token(token_str: str) -> str:
    """Generate SHA-256 hash of token string for database lookup."""
    return hashlib.sha256(token_str.encode('utf-8')).hexdigest()


class GuestChatAccessError(Exception):
    """Base exception for guest chat access errors."""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class InvalidTokenError(GuestChatAccessError):
    """Token is invalid, expired, or hotel mismatch."""
    def __init__(self, message="Invalid or expired token"):
        super().__init__(message, status_code=404)  # Anti-enumeration


class NotInHouseError(GuestChatAccessError):
    """Guest is not checked in or booking is not active."""
    def __init__(self, message="Guest is not currently checked in"):
        super().__init__(message, status_code=403)


class NoRoomAssignedError(GuestChatAccessError):
    """Booking exists but no room is assigned."""
    def __init__(self, message="No room assigned to this booking"):
        super().__init__(message, status_code=409)


def resolve_guest_chat_context(hotel_slug: str, token_str: str, require_in_house: bool = True):
    """
    Resolve guest chat context from token.
    
    This is the single source of truth for guest chat authentication.
    All guest chat endpoints must use this function to validate access.
    
    Args:
        hotel_slug: The hotel slug from the URL
        token_str: The raw token string from query params
        require_in_house: Whether to require guest to be checked in
        
    Returns:
        tuple: (booking, room, conversation)
        
    Raises:
        InvalidTokenError: Token invalid, expired, or hotel mismatch (404)
        NotInHouseError: Guest not checked in (403)  
        NoRoomAssignedError: No room assigned (409)
    """
    if not token_str or not token_str.strip():
        logger.warning(f"Empty token provided for hotel {hotel_slug}")
        raise InvalidTokenError("Token is required")
    
    # Hash the token for database lookup
    token_hash = hash_token(token_str.strip())
    
    try:
        # Get token with related booking and hotel data
        guest_token = GuestBookingToken.objects.select_related(
            'booking__hotel', 
            'booking__assigned_room'
        ).get(
            token_hash=token_hash,
            status='ACTIVE'
        )
        
        logger.info(f"Found active token for booking {guest_token.booking.booking_id}")
        
    except GuestBookingToken.DoesNotExist:
        logger.warning(f"Invalid token hash for hotel {hotel_slug}")
        raise InvalidTokenError("Invalid or expired token")
    
    # Validate token expiration
    if guest_token.expires_at and timezone.now() > guest_token.expires_at:
        logger.warning(f"Expired token for booking {guest_token.booking.booking_id}")
        raise InvalidTokenError("Token has expired")
    
    booking = guest_token.booking
    
    # Validate hotel match (anti-enumeration - return 404 for mismatches)
    if booking.hotel.slug != hotel_slug:
        logger.warning(
            f"Hotel mismatch: token hotel={booking.hotel.slug}, "
            f"requested hotel={hotel_slug}, booking={booking.booking_id}"
        )
        raise InvalidTokenError("Invalid token for this hotel")
    
    # Validate booking status - must not be cancelled
    if booking.status in ['CANCELLED', 'CANCELLED_DRAFT', 'DECLINED']:
        logger.warning(f"Cancelled booking {booking.booking_id} attempted chat access")
        raise InvalidTokenError("Booking is not active")
    
    # Check in-house requirement
    if require_in_house:
        # Must be checked in and not checked out
        if not booking.checked_in_at:
            logger.warning(f"Booking {booking.booking_id} not checked in yet")
            raise NotInHouseError("Guest has not checked in yet")
            
        if booking.checked_out_at:
            logger.warning(f"Booking {booking.booking_id} already checked out")
            raise NotInHouseError("Guest has already checked out")
    
    # Must have assigned room
    if not booking.assigned_room:
        logger.warning(f"Booking {booking.booking_id} has no assigned room")
        raise NoRoomAssignedError("No room assigned to booking")
    
    room = booking.assigned_room
    
    # Get or create conversation for the room
    conversation, created = Conversation.objects.get_or_create(
        room=room,
        defaults={}
    )
    
    if created:
        logger.info(f"Created new conversation for room {room.room_number}")
    
    # Update token last used timestamp
    guest_token.last_used_at = timezone.now()
    guest_token.save(update_fields=['last_used_at'])
    
    logger.info(
        f"✅ Guest chat access granted: booking={booking.booking_id}, "
        f"room={room.room_number}, conversation={conversation.id}"
    )
    
    return booking, room, conversation


def validate_guest_conversation_access(hotel_slug: str, token_str: str, conversation_id: int):
    """
    Validate that a guest token has access to a specific conversation.
    
    Args:
        hotel_slug: Hotel slug from URL
        token_str: Guest token string
        conversation_id: Conversation ID to validate access to
        
    Returns:
        tuple: (booking, room, conversation)
        
    Raises:
        Same exceptions as resolve_guest_chat_context plus:
        InvalidTokenError: If conversation doesn't match token's room
    """
    # First resolve the guest's context
    booking, room, conversation = resolve_guest_chat_context(
        hotel_slug=hotel_slug,
        token_str=token_str,
        require_in_house=True
    )
    
    # Ensure the requested conversation matches the token's room
    if conversation.id != conversation_id:
        logger.warning(
            f"Conversation access denied: token conversation={conversation.id}, "
            f"requested conversation={conversation_id}, booking={booking.booking_id}"
        )
        raise InvalidTokenError("Access denied to this conversation")
    
    return booking, room, conversation