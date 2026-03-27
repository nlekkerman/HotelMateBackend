"""
Guest Chat Session Grant — Signed, Short-Lived, Booking-Bound

Issues and validates a signed grant token after successful bootstrap
resolution. All guest chat endpoints authenticate via this grant
instead of re-validating the raw email/booking token.

Uses django.core.signing (HMAC-SHA256 via SECRET_KEY) — zero external
dependencies. The grant is a URL-safe base64-encoded signed payload.

Claims:
    booking_id  — canonical booking identifier (e.g. "BK-2025-0003")
    hotel_slug  — hotel this grant is scoped to
    room_id     — assigned room PK (nullable)
    room_number — assigned room number string (nullable)
    scope       — "guest_chat"
    iat         — issued-at epoch timestamp

Max age: settings.GUEST_CHAT_GRANT_MAX_AGE_SECONDS (default 4 hours).
"""

import logging
import time

from django.conf import settings
from django.core import signing

logger = logging.getLogger(__name__)

# Default: 4 hours
GRANT_MAX_AGE = getattr(settings, "GUEST_CHAT_GRANT_MAX_AGE_SECONDS", 4 * 60 * 60)

_GRANT_SALT = "guest-chat-grant-v1"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GuestChatGrantError(Exception):
    """Base for grant-related errors."""
    def __init__(self, message: str, code: str, status_code: int = 401):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class GrantRequiredError(GuestChatGrantError):
    def __init__(self):
        super().__init__("Guest chat grant is required", "GRANT_REQUIRED", 401)


class GrantExpiredError(GuestChatGrantError):
    def __init__(self):
        super().__init__("Guest chat grant has expired — re-bootstrap required", "GRANT_EXPIRED", 401)


class GrantInvalidError(GuestChatGrantError):
    def __init__(self, detail="Invalid guest chat grant"):
        super().__init__(detail, "GRANT_INVALID", 401)


class GrantScopeMismatchError(GuestChatGrantError):
    def __init__(self):
        super().__init__("Grant scope mismatch", "GRANT_SCOPE_MISMATCH", 403)


class GrantHotelMismatchError(GuestChatGrantError):
    def __init__(self):
        super().__init__("Grant does not match this hotel", "GRANT_HOTEL_MISMATCH", 403)


# ---------------------------------------------------------------------------
# Dataclass for decoded grant
# ---------------------------------------------------------------------------

class GuestChatGrantContext:
    """Decoded, validated grant payload."""
    __slots__ = ("booking_id", "hotel_slug", "room_id", "room_number", "scope", "issued_at")

    def __init__(self, booking_id, hotel_slug, room_id, room_number, scope, issued_at):
        self.booking_id = booking_id
        self.hotel_slug = hotel_slug
        self.room_id = room_id
        self.room_number = room_number
        self.scope = scope
        self.issued_at = issued_at


# ---------------------------------------------------------------------------
# Issue
# ---------------------------------------------------------------------------

def issue_guest_chat_grant(booking, room=None) -> str:
    """
    Issue a signed guest chat grant for a resolved booking.

    Args:
        booking: RoomBooking instance (must have booking_id, hotel.slug)
        room:    Room instance or None

    Returns:
        URL-safe signed grant string.
    """
    payload = {
        "bid": booking.booking_id,
        "hs": booking.hotel.slug,
        "rid": room.id if room else None,
        "rn": room.room_number if room else None,
        "sc": "guest_chat",
        "iat": int(time.time()),
    }
    grant = signing.dumps(payload, salt=_GRANT_SALT)
    logger.info(
        "guest_chat_grant issued: booking=%s hotel=%s room=%s",
        booking.booking_id, booking.hotel.slug,
        room.room_number if room else None,
    )
    return grant


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate_guest_chat_grant(grant_str: str, hotel_slug: str) -> GuestChatGrantContext:
    """
    Validate and decode a guest chat grant.

    Args:
        grant_str:  The raw grant string from the request.
        hotel_slug: The hotel_slug from the URL path (cross-validated).

    Returns:
        GuestChatGrantContext

    Raises:
        GrantRequiredError       — empty/missing grant
        GrantExpiredError        — grant older than max age
        GrantInvalidError        — tampered or malformed
        GrantScopeMismatchError  — wrong scope
        GrantHotelMismatchError  — grant hotel != URL hotel
    """
    if not grant_str or not grant_str.strip():
        raise GrantRequiredError()

    try:
        payload = signing.loads(
            grant_str.strip(),
            salt=_GRANT_SALT,
            max_age=GRANT_MAX_AGE,
        )
    except signing.SignatureExpired:
        raise GrantExpiredError()
    except signing.BadSignature:
        raise GrantInvalidError()

    # Validate required fields
    booking_id = payload.get("bid")
    grant_hotel = payload.get("hs")
    scope = payload.get("sc")
    if not booking_id or not grant_hotel or not scope:
        raise GrantInvalidError("Malformed grant payload")

    # Scope check
    if scope != "guest_chat":
        raise GrantScopeMismatchError()

    # Hotel cross-validation
    if grant_hotel != hotel_slug:
        logger.warning(
            "guest_chat_grant hotel mismatch: grant_hotel=%s url_hotel=%s booking=%s",
            grant_hotel, hotel_slug, booking_id,
        )
        raise GrantHotelMismatchError()

    return GuestChatGrantContext(
        booking_id=booking_id,
        hotel_slug=grant_hotel,
        room_id=payload.get("rid"),
        room_number=payload.get("rn"),
        scope=scope,
        issued_at=payload.get("iat"),
    )
