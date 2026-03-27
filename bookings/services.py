"""
Guest portal services — booking-bound chat context resolution.

Token-based bootstrap is handled by common.guest_access.
Post-bootstrap chat context is resolved from a signed session/grant
via resolve_chat_context_from_grant().
"""

from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from chat.models import Conversation
import logging

from common.guest_access import (
    GuestAccessError,
    InvalidTokenError,
    NoRoomAssignedError,
)

logger = logging.getLogger(__name__)


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
    """
    from hotel.models import RoomBooking

    try:
        booking = RoomBooking.objects.select_related(
            "hotel", "assigned_room",
        ).get(booking_id=grant_ctx.booking_id)
    except RoomBooking.DoesNotExist:
        raise InvalidTokenError("Booking not found")

    if booking.status in (
        "CANCELLED", "CANCELLED_DRAFT", "DECLINED",
    ):
        raise InvalidTokenError("Booking is no longer active")

    room = booking.assigned_room

    # Conversation: keyed by booking, room is contextual metadata
    conversation, created = Conversation.objects.get_or_create(
        booking=booking,
        defaults={"room": room},
    )
    if created:
        logger.info(
            "Created conversation for booking %s",
            booking.booking_id,
        )
    elif room and conversation.room_id != getattr(room, 'id', None):
        conversation.room = room
        conversation.save(update_fields=["room"])
        logger.info(
            "Updated conversation room: booking=%s room=%s",
            booking.booking_id, room.room_number,
        )

    return booking, room, conversation