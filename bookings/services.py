"""
Guest portal services for token-based authentication and access control.

Delegates all token validation to the canonical resolver in
common.guest_access. This module adds chat-specific logic (conversation
lookup, allowed_actions / disabled_reason UX hints) on top.
"""

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from chat.models import Conversation
import hashlib
import logging

from common.guest_access import (                       # canonical resolver
    resolve_guest_access,
    GuestAccessContext,
    GuestAccessError,
    TokenRequiredError,
    InvalidTokenError,
    MissingScopeError,
    NotInHouseError,
    NotCheckedInError,
    AlreadyCheckedOutError,
    NoRoomAssignedError,
)

logger = logging.getLogger(__name__)


# Re-export canonical exceptions so existing imports still work:
#   from bookings.services import InvalidTokenError, ...
# Also keep the legacy alias for callers that used GuestChatAccessError.
GuestChatAccessError = GuestAccessError


def hash_token(token_str: str) -> str:
    """Generate SHA-256 hash of token string for database lookup."""
    return hashlib.sha256(token_str.encode('utf-8')).hexdigest()


def resolve_guest_chat_context(hotel_slug: str, token_str: str, required_scopes=None, action_required: bool = True):
    """
    Resolve guest chat context from token with scope validation.

    Delegates token validation to the canonical resolver in
    common.guest_access (BookingManagementToken only).
    Adds chat-specific conversation lookup and UX hints on top.

    Args:
        hotel_slug:      Hotel slug from the URL.
        token_str:       Raw token string.
        required_scopes: e.g. ["CHAT"]. None to skip scope check.
        action_required: True → reject pre-checkin / post-checkout guests.
                         False → return context with disabled_reason hint.

    Returns:
        (booking, room, conversation, allowed_actions, disabled_reason)

    Raises:
        InvalidTokenError / MissingScopeError / NotInHouseError /
        NoRoomAssignedError  (all from common.guest_access)
    """
    # --- canonical token validation (both token types) ---
    if action_required:
        ctx = resolve_guest_access(
            token_str=token_str,
            hotel_slug=hotel_slug,
            required_scopes=required_scopes,
            require_in_house=True,
        )
    else:
        # Soft mode: validate token + scopes, but not in-house status.
        ctx = resolve_guest_access(
            token_str=token_str,
            hotel_slug=hotel_slug,
            required_scopes=required_scopes,
            require_in_house=False,
        )

    booking = ctx.booking
    room = ctx.room

    # --- UX hints for soft mode ---
    allowed_actions = {"can_chat": False}
    disabled_reason = None

    if action_required:
        # Strict mode succeeded → guest is in-house
        allowed_actions["can_chat"] = True
    else:
        if not booking.checked_in_at:
            disabled_reason = "Check-in required to access chat"
        elif booking.checked_out_at:
            disabled_reason = "Chat unavailable after checkout"
        elif not booking.assigned_room:
            disabled_reason = "Room assignment required"
        else:
            allowed_actions["can_chat"] = True

    # --- conversation lookup ---
    conversation = None
    if room:
        conversation, created = Conversation.objects.get_or_create(
            room=room,
            defaults={},
        )
        if created:
            logger.info(f"Created new conversation for room {room.room_number}")

    logger.info(
        f"✅ Guest chat context resolved: booking={booking.booking_id}, "
        f"room={room.room_number if room else None}, "
        f"conversation={conversation.id if conversation else None}, "
        f"can_chat={allowed_actions['can_chat']}, disabled_reason={disabled_reason}"
    )

    return booking, room, conversation, allowed_actions, disabled_reason


def validate_guest_conversation_access(hotel_slug: str, token_str: str, conversation_id: int):
    """
    Validate that a guest token has access to a specific conversation.

    Delegates to resolve_guest_chat_context (which delegates to
    resolve_guest_access) and verifies the conversation belongs to the
    token's booking room.
    """
    booking, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
        hotel_slug=hotel_slug,
        token_str=token_str,
        required_scopes=["CHAT"],
        action_required=True,
    )

    if conversation.id != conversation_id:
        logger.warning(
            f"Conversation access denied: token conversation={conversation.id}, "
            f"requested conversation={conversation_id}, booking={booking.booking_id}"
        )
        raise InvalidTokenError("Access denied to this conversation")

    return booking, room, conversation, allowed_actions, disabled_reason