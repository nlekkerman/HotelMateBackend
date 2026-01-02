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


class MissingScopeError(GuestChatAccessError):
    """Token lacks required scopes for the requested action."""
    def __init__(self, message="Token lacks required permissions", required_scopes=None):
        self.required_scopes = required_scopes or []
        super().__init__(message, status_code=403)


def resolve_guest_chat_context(hotel_slug: str, token_str: str, required_scopes=None, action_required: bool = True):
    """
    Resolve guest chat context from token with scope validation.
    
    This is the single source of truth for guest chat authentication.
    All guest chat endpoints must use this function to validate access.
    
    Args:
        hotel_slug: The hotel slug from the URL
        token_str: The raw token string from query params
        required_scopes: List of required scopes (e.g., ["CHAT"]) or None to skip scope check
        action_required: If True, requires in-house status; if False, returns context with allowed_actions
        
    Returns:
        tuple: (booking, room, conversation, allowed_actions, disabled_reason)
        
    Raises:
        InvalidTokenError: Token invalid, expired, or hotel mismatch (404)
        MissingScopeError: Token lacks required scopes (403)
        NotInHouseError: Guest not checked in when action_required=True (403)
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
    
    # Validate token scopes if required
    if required_scopes:
        token_scopes = guest_token.scopes or []
        missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
        if missing_scopes:
            logger.warning(
                f"Token for booking {booking.booking_id} lacks required scopes: {missing_scopes}. "
                f"Token has: {token_scopes}"
            )
            raise MissingScopeError(
                f"Token lacks required permissions: {', '.join(missing_scopes)}",
                required_scopes=missing_scopes
            )
    
    # Initialize allowed actions and disabled reason for UX-friendly responses
    allowed_actions = {"can_chat": False}
    disabled_reason = None
    
    # Check in-house requirement
    is_in_house = booking.checked_in_at and not booking.checked_out_at and booking.assigned_room
    
    if action_required and not is_in_house:
        # For strict actions, enforce in-house requirement
        if not booking.checked_in_at:
            logger.warning(f"Booking {booking.booking_id} not checked in yet")
            raise NotInHouseError("Guest has not checked in yet")
            
        if booking.checked_out_at:
            logger.warning(f"Booking {booking.booking_id} already checked out")
            raise NotInHouseError("Guest has already checked out")
            
        if not booking.assigned_room:
            logger.warning(f"Booking {booking.booking_id} has no assigned room")
            raise NoRoomAssignedError("No room assigned to booking")
    else:
        # For context requests, provide UX-friendly feedback
        if not booking.checked_in_at:
            disabled_reason = "Check-in required to access chat"
        elif booking.checked_out_at:
            disabled_reason = "Chat unavailable after checkout"
        elif not booking.assigned_room:
            disabled_reason = "Room assignment required"
        else:
            # Token has scopes and guest is in-house
            allowed_actions["can_chat"] = True
    
    room = booking.assigned_room
    
    # Get or create conversation for the room (even if not in-house for context)
    conversation = None
    if room:
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
        f"✅ Guest chat context resolved: booking={booking.booking_id}, "
        f"room={room.room_number if room else None}, conversation={conversation.id if conversation else None}, "
        f"can_chat={allowed_actions['can_chat']}, disabled_reason={disabled_reason}"
    )
    
    return booking, room, conversation, allowed_actions, disabled_reason


def validate_guest_conversation_access(hotel_slug: str, token_str: str, conversation_id: int):
    """
    Validate that a guest token has access to a specific conversation.
    
    Args:
        hotel_slug: Hotel slug from URL
        token_str: Guest token string
        conversation_id: Conversation ID to validate access to
        
    Returns:
        tuple: (booking, room, conversation, allowed_actions, disabled_reason)
        
    Raises:
        Same exceptions as resolve_guest_chat_context plus:
        InvalidTokenError: If conversation doesn't match token's room
    """
    # First resolve the guest's context with strict validation
    booking, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
        hotel_slug=hotel_slug,
        token_str=token_str,
        required_scopes=["CHAT"],
        action_required=True
    )
    
    # Ensure the requested conversation matches the token's room
    if conversation.id != conversation_id:
        logger.warning(
            f"Conversation access denied: token conversation={conversation.id}, "
            f"requested conversation={conversation_id}, booking={booking.booking_id}"
        )
        raise InvalidTokenError("Access denied to this conversation")
    
    return booking, room, conversation, allowed_actions, disabled_reason