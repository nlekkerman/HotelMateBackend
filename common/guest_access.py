"""
Canonical Guest Access Resolver

THE single source of truth for resolving guest identity from a raw token.
Every guest-facing endpoint MUST use resolve_guest_access() to authenticate.

Supports both token types:
- GuestBookingToken (guest portal tokens with explicit scopes)
- BookingManagementToken (email management tokens, implied scopes)

Both resolve to the same canonical GuestAccessContext.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exception hierarchy — clear, typed, with HTTP status codes
# ---------------------------------------------------------------------------

class GuestAccessError(Exception):
    """Base for all guest access errors."""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class TokenRequiredError(GuestAccessError):
    def __init__(self):
        super().__init__("Token is required", "TOKEN_REQUIRED", 401)


class InvalidTokenError(GuestAccessError):
    """Anti-enumeration: returns 404 for invalid/expired/mismatched tokens."""
    def __init__(self, message="Invalid or expired token"):
        super().__init__(message, "INVALID_TOKEN", 404)


class MissingScopeError(GuestAccessError):
    def __init__(self, missing_scopes: List[str]):
        self.missing_scopes = missing_scopes
        super().__init__(
            f"Token lacks required permissions: {', '.join(missing_scopes)}",
            "MISSING_SCOPE",
            403,
        )


class NotInHouseError(GuestAccessError):
    """Guest is not currently in-house. Catch this to handle both sub-types."""
    def __init__(self, message="Guest is not currently in-house", code="NOT_IN_HOUSE"):
        super().__init__(message, code, 403)


class NotCheckedInError(NotInHouseError):
    def __init__(self):
        super().__init__("Guest has not checked in yet", "NOT_CHECKED_IN")


class AlreadyCheckedOutError(NotInHouseError):
    def __init__(self):
        super().__init__("Guest has already checked out", "ALREADY_CHECKED_OUT")


class NoRoomAssignedError(GuestAccessError):
    def __init__(self):
        super().__init__(
            "No room assigned to this booking yet", "NO_ROOM_ASSIGNED", 409
        )


# ---------------------------------------------------------------------------
# Canonical result object
# ---------------------------------------------------------------------------

# Default scopes implied for BookingManagementToken (email link guests).
_MANAGEMENT_TOKEN_IMPLIED_SCOPES = ["STATUS_READ", "CHAT", "ROOM_SERVICE"]


@dataclass
class GuestAccessContext:
    """Unified result of guest access resolution."""
    booking: object          # RoomBooking
    room: Optional[object]   # Room or None
    scopes: List[str] = field(default_factory=list)
    token_type: str = ""     # 'guest_booking' | 'booking_management'

    @property
    def is_in_house(self) -> bool:
        return bool(
            self.booking.checked_in_at
            and not self.booking.checked_out_at
            and self.booking.assigned_room
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_guest_access(
    token_str: str,
    hotel_slug: str,
    required_scopes: Optional[List[str]] = None,
    require_in_house: bool = False,
) -> GuestAccessContext:
    """
    Canonical guest access resolver.

    Validates a raw token against GuestBookingToken first, then
    BookingManagementToken. Returns a unified GuestAccessContext on
    success; raises a typed GuestAccessError subclass on failure.

    Args:
        token_str:        Raw token string from the request.
        hotel_slug:       Hotel slug from the URL path.
        required_scopes:  Optional list of scopes the token must carry.
        require_in_house: If True, booking must be checked-in with room
                          assigned and not yet checked out.

    Returns:
        GuestAccessContext

    Raises:
        TokenRequiredError  – empty / missing token
        InvalidTokenError   – not found, expired, hotel mismatch, cancelled
        MissingScopeError   – token lacks required scopes
        NotCheckedInError   – require_in_house but not checked in
        AlreadyCheckedOutError – require_in_house but already checked out
        NoRoomAssignedError – require_in_house but no room assigned
    """
    if not token_str or not token_str.strip():
        raise TokenRequiredError()

    token_hash = hashlib.sha256(token_str.strip().encode("utf-8")).hexdigest()

    # --- Lookup: try GuestBookingToken, then BookingManagementToken ---
    ctx = _try_guest_booking_token(token_hash, hotel_slug)
    if ctx is None:
        ctx = _try_booking_management_token(token_hash, hotel_slug)
    if ctx is None:
        raise InvalidTokenError()

    booking = ctx.booking

    # Booking lifecycle gate (anti-enumeration: same 404 as "not found")
    if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
        raise InvalidTokenError()

    # Scope gate
    if required_scopes:
        missing = [s for s in required_scopes if s not in ctx.scopes]
        if missing:
            raise MissingScopeError(missing)

    # In-house gate
    if require_in_house:
        if not booking.checked_in_at:
            raise NotCheckedInError()
        if booking.checked_out_at:
            raise AlreadyCheckedOutError()
        if not booking.assigned_room:
            raise NoRoomAssignedError()

    return ctx


# ---------------------------------------------------------------------------
# Internal lookup helpers
# ---------------------------------------------------------------------------

def _try_guest_booking_token(token_hash: str, hotel_slug: str):
    from hotel.models import GuestBookingToken

    try:
        gt = GuestBookingToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash, status="ACTIVE")
    except GuestBookingToken.DoesNotExist:
        return None

    if gt.expires_at and timezone.now() > gt.expires_at:
        return None

    if gt.booking.hotel.slug != hotel_slug:
        return None

    gt.last_used_at = timezone.now()
    gt.save(update_fields=["last_used_at"])

    return GuestAccessContext(
        booking=gt.booking,
        room=gt.booking.assigned_room,
        scopes=gt.scopes or [],
        token_type="guest_booking",
    )


def _try_booking_management_token(token_hash: str, hotel_slug: str):
    from hotel.models import BookingManagementToken

    try:
        bmt = BookingManagementToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash)
    except BookingManagementToken.DoesNotExist:
        return None

    if not bmt.is_valid:
        return None

    if bmt.booking.hotel.slug != hotel_slug:
        return None

    bmt.record_action("VIEW")

    return GuestAccessContext(
        booking=bmt.booking,
        room=bmt.booking.assigned_room,
        scopes=list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES),
        token_type="booking_management",
    )
