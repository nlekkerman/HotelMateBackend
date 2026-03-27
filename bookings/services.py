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
    """Generate SHA-256 hash of token string for database lookup.
    
    Delegates to the canonical hash_token in common.guest_access
    to ensure consistent .strip() handling across all endpoints.
    """
    from common.guest_access import hash_token as _canonical_hash
    return _canonical_hash(token_str)


def resolve_guest_chat_context(hotel_slug: str, token_str: str, required_scopes=None, action_required: bool = True):
    """
    Resolve guest chat context from token with scope validation.

    Delegates token validation to the canonical resolver in
    common.guest_access (BookingManagementToken only).
    Adds chat-specific conversation lookup and UX hints on top.

    Conversation is keyed by booking (booking is the owner).
    Room is attached as contextual metadata and updated on each call
    so room changes don't break conversation identity.

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

    # --- conversation lookup: keyed by booking, room is contextual ---
    conversation = None
    if booking:
        conversation, created = Conversation.objects.get_or_create(
            booking=booking,
            defaults={"room": room},
        )
        if created:
            logger.info(f"Created new conversation for booking {booking.booking_id}")
        elif room and conversation.room_id != getattr(room, 'id', None):
            # Room changed (e.g. room swap) — update contextual metadata
            conversation.room = room
            conversation.save(update_fields=["room"])
            logger.info(
                f"Updated conversation room context: booking={booking.booking_id}, "
                f"new_room={room.room_number}"
            )

    logger.info(
        f"✅ Guest chat context resolved: booking={booking.booking_id}, "
        f"room={room.room_number if room else None}, "
        f"conversation={conversation.id if conversation else None}, "
        f"can_chat={allowed_actions['can_chat']}, disabled_reason={disabled_reason}"
    )

    return booking, room, conversation, allowed_actions, disabled_reason


def resolve_chat_context_from_grant(grant_ctx):
    """
    Resolve chat context from an already-validated GuestChatGrantContext.

    Looks up booking + conversation by booking_id (from grant claims).
    Room metadata is refreshed from the current booking state.

    This is the primary path for all chat endpoints after bootstrap.

    Args:
        grant_ctx: GuestChatGrantContext (from validate_guest_chat_grant)

    Returns:
        (booking, room, conversation)

    Raises:
        InvalidTokenError — if booking not found or lifecycle-rejected
        NoRoomAssignedError — if booking has no room (and one is needed)
    """
    from hotel.models import RoomBooking

    try:
        booking = RoomBooking.objects.select_related(
            "hotel", "assigned_room"
        ).get(booking_id=grant_ctx.booking_id)
    except RoomBooking.DoesNotExist:
        raise InvalidTokenError("Booking not found")

    if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
        raise InvalidTokenError("Booking is no longer active")

    room = booking.assigned_room

    # Conversation lookup: keyed by booking, room is contextual metadata
    conversation, created = Conversation.objects.get_or_create(
        booking=booking,
        defaults={"room": room},
    )
    if created:
        logger.info(f"Created new conversation for booking {booking.booking_id}")
    elif room and conversation.room_id != getattr(room, 'id', None):
        conversation.room = room
        conversation.save(update_fields=["room"])
        logger.info(
            f"Updated conversation room context: booking={booking.booking_id}, "
            f"new_room={room.room_number}"
        )

    return booking, room, conversation


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