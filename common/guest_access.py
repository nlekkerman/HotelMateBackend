"""
Canonical Guest Access Resolver

THE single source of truth for resolving guest identity from a raw token.
Every guest-facing endpoint MUST use resolve_guest_access() to authenticate.

TWO token models are accepted (checked in order):
1. BookingManagementToken — issued via email management links.
2. GuestBookingToken      — issued at booking creation time (returned in API response).

Both use SHA-256 hashed storage. The lookup checks BookingManagementToken first,
then falls back to GuestBookingToken.
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
    """Returns 401 for invalid/expired/mismatched tokens."""
    def __init__(self, message="Invalid or expired token"):
        super().__init__(message, "INVALID_TOKEN", 401)


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
# Canonical token hashing — single source of truth
# ---------------------------------------------------------------------------

def hash_token(raw_token: str) -> str:
    """Canonical SHA-256 hash of a raw token string.

    Always strips whitespace before hashing so that tokens copied
    from emails or URLs with trailing spaces still resolve.
    Every piece of code that hashes a BookingManagementToken MUST
    use this function.
    """
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Canonical result object
# ---------------------------------------------------------------------------

# Implied scopes for BookingManagementToken (the only token type).
_MANAGEMENT_TOKEN_IMPLIED_SCOPES = ["STATUS_READ", "CHAT", "ROOM_SERVICE"]


@dataclass
class GuestAccessContext:
    """Unified result of guest access resolution."""
    booking: object          # RoomBooking
    room: Optional[object]   # Room or None
    scopes: List[str] = field(default_factory=list)
    token_type: str = "booking_management"
    token_obj: Optional[object] = None  # BookingManagementToken instance

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

    Validates a raw token against BookingManagementToken ONLY.
    Returns a GuestAccessContext on success; raises a typed
    GuestAccessError subclass on failure.

    Uses the EXACT same validation logic as BookingStatusView:
    SHA-256 hash lookup → is_valid check → hotel_slug match.

    Args:
        token_str:        Raw token string from the request.
        hotel_slug:       Hotel slug from the URL path.
        required_scopes:  Optional list of scopes the token must carry.
        require_in_house: If True, booking must be checked-in with room
                          assigned and not yet checked out.

    Returns:
        GuestAccessContext

    Raises:
        TokenRequiredError     – empty / missing token
        InvalidTokenError      – not found, expired, hotel mismatch, cancelled
        MissingScopeError      – token lacks required scopes
        NotCheckedInError      – require_in_house but not checked in
        AlreadyCheckedOutError – require_in_house but already checked out
        NoRoomAssignedError    – require_in_house but no room assigned
    """
    if not token_str or not token_str.strip():
        raise TokenRequiredError()

    token_hash = hash_token(token_str)

    logger.warning(
        "guest_access resolve: requested_slug=%s token_len=%d "
        "token_prefix=%s token_suffix=%s hash_prefix=%s",
        hotel_slug,
        len(token_str),
        token_str[:4] if token_str else "",
        token_str[-4:] if token_str else "",
        token_hash[:8],
    )

    # --- Lookup: BookingManagementToken first, then GuestBookingToken ---
    ctx = _try_booking_management_token(token_hash, hotel_slug)
    if ctx is None:
        ctx = _try_guest_booking_token(token_hash, hotel_slug)
    if ctx is None:
        logger.warning(
            "guest_access resolve: REJECTED — both _try_bmt and _try_gbt "
            "returned None for slug=%s hash_prefix=%s",
            hotel_slug,
            token_hash[:8],
        )
        raise InvalidTokenError()

    booking = ctx.booking

    # Booking lifecycle gate (anti-enumeration: same error as "not found")
    if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
        logger.warning(
            "guest_access resolve: REJECTED — booking lifecycle "
            "booking_id=%s status=%s slug=%s",
            booking.booking_id,
            booking.status,
            hotel_slug,
        )
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

    logger.warning(
        "guest_access resolve: SUCCESS booking_id=%s slug=%s status=%s "
        "checked_in=%s checked_out=%s room=%s",
        booking.booking_id,
        hotel_slug,
        booking.status,
        bool(booking.checked_in_at),
        bool(booking.checked_out_at),
        getattr(booking.assigned_room, "room_number", None),
    )

    return ctx


def resolve_guest_access_without_slug(
    token_str: str,
    required_scopes: Optional[List[str]] = None,
    require_in_house: bool = False,
) -> GuestAccessContext:
    """
    Resolve a guest token when no hotel_slug is available in the URL.

    ⚠️  RESTRICTED USE — bootstrap only.
    The ONLY legitimate caller is GuestContextView (/api/guest/context/),
    which is the bootstrap endpoint where the guest doesn't know the slug yet.
    Every other guest endpoint MUST use resolve_guest_access(hotel_slug=...)
    so the slug from the URL is cross-validated against the token's booking.

    If you are adding a new guest endpoint, use resolve_guest_access() instead.
    If your endpoint doesn't have a slug in the URL, you are probably creating
    a duplicate — ask whether the canonical slug-scoped endpoint already exists.
    """
    if not token_str or not token_str.strip():
        raise TokenRequiredError()

    from hotel.models import BookingManagementToken, GuestBookingToken

    token_hash = hash_token(token_str)

    logger.warning(
        "guest_access resolve_without_slug: token_len=%d "
        "token_prefix=%s token_suffix=%s hash_prefix=%s",
        len(token_str),
        token_str[:4] if token_str else "",
        token_str[-4:] if token_str else "",
        token_hash[:8],
    )

    # --- Try BookingManagementToken first ---
    bmt = None
    gbt = None
    try:
        bmt = BookingManagementToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash)
    except BookingManagementToken.DoesNotExist:
        logger.warning(
            "guest_access resolve_without_slug: BMT NOT FOUND hash_prefix=%s, "
            "falling back to GuestBookingToken",
            token_hash[:8],
        )

    if bmt is not None:
        if not bmt.is_valid:
            logger.warning(
                "guest_access resolve_without_slug: BMT INVALID "
                "booking_id=%s revoked=%s status=%s",
                bmt.booking.booking_id,
                bmt.revoked_at is not None,
                bmt.booking.status,
            )
            raise InvalidTokenError()

        booking = bmt.booking

        if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
            raise InvalidTokenError()

        bmt.record_action("VIEW")

        ctx = GuestAccessContext(
            booking=booking,
            room=booking.assigned_room,
            scopes=list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES),
            token_type="booking_management",
            token_obj=bmt,
        )
    else:
        # --- Fallback: GuestBookingToken ---
        try:
            gbt = GuestBookingToken.objects.select_related(
                "booking__hotel",
                "booking__assigned_room",
            ).get(token_hash=token_hash, status="ACTIVE")
        except GuestBookingToken.DoesNotExist:
            logger.warning(
                "guest_access resolve_without_slug: GBT NOT FOUND (or not ACTIVE) "
                "hash_prefix=%s — token does not exist in either model",
                token_hash[:8],
            )
            raise InvalidTokenError()

        if gbt.expires_at and timezone.now() > gbt.expires_at:
            logger.warning(
                "guest_access resolve_without_slug: GBT EXPIRED "
                "booking_id=%s expires_at=%s",
                gbt.booking.booking_id,
                gbt.expires_at,
            )
            raise InvalidTokenError()

        booking = gbt.booking

        if booking.status in ("CANCELLED", "CANCELLED_DRAFT", "DECLINED"):
            raise InvalidTokenError()

        gbt.last_used_at = timezone.now()
        gbt.save(update_fields=["last_used_at"])

        scopes = gbt.scopes if gbt.scopes else list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES)

        ctx = GuestAccessContext(
            booking=booking,
            room=booking.assigned_room,
            scopes=scopes,
            token_type="guest_booking",
            token_obj=gbt,
        )

    logger.warning(
        "guest_access resolve_without_slug: SUCCESS booking_id=%s "
        "slug=%s status=%s token_type=%s",
        ctx.booking.booking_id,
        ctx.booking.hotel.slug,
        ctx.booking.status,
        ctx.token_type,
    )

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
# Internal lookup helper
# ---------------------------------------------------------------------------

def _try_booking_management_token(token_hash: str, hotel_slug: str):
    from hotel.models import BookingManagementToken

    try:
        bmt = BookingManagementToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash)
    except BookingManagementToken.DoesNotExist:
        logger.warning(
            "guest_access _try_bmt: token NOT FOUND in DB hash_prefix=%s",
            token_hash[:8],
        )
        return None

    booking = bmt.booking
    booking_slug = getattr(getattr(booking, "hotel", None), "slug", None)

    if not bmt.is_valid:
        logger.warning(
            "guest_access _try_bmt: token INVALID "
            "booking_id=%s revoked=%s cancelled=%s status=%s "
            "requested_slug=%s booking_slug=%s",
            booking.booking_id,
            bmt.revoked_at is not None,
            booking.cancelled_at is not None if hasattr(booking, "cancelled_at") else "N/A",
            booking.status,
            hotel_slug,
            booking_slug,
        )
        return None

    if booking_slug != hotel_slug:
        logger.warning(
            "guest_access _try_bmt: SLUG MISMATCH "
            "booking_id=%s requested_slug=%r booking_slug=%r",
            booking.booking_id,
            hotel_slug,
            booking_slug,
        )
        return None

    bmt.record_action("VIEW")

    return GuestAccessContext(
        booking=bmt.booking,
        room=bmt.booking.assigned_room,
        scopes=list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES),
        token_type="booking_management",
        token_obj=bmt,
    )


def _try_guest_booking_token(token_hash: str, hotel_slug: str):
    """Fallback lookup in GuestBookingToken (issued at booking creation)."""
    from hotel.models import GuestBookingToken

    try:
        gbt = GuestBookingToken.objects.select_related(
            "booking__hotel",
            "booking__assigned_room",
        ).get(token_hash=token_hash, status="ACTIVE")
    except GuestBookingToken.DoesNotExist:
        logger.warning(
            "guest_access _try_gbt: token NOT FOUND (or not ACTIVE) "
            "hash_prefix=%s",
            token_hash[:8],
        )
        return None

    booking = gbt.booking
    booking_slug = getattr(getattr(booking, "hotel", None), "slug", None)

    # Time-based expiry check
    if gbt.expires_at and timezone.now() > gbt.expires_at:
        logger.warning(
            "guest_access _try_gbt: token EXPIRED "
            "booking_id=%s expires_at=%s requested_slug=%s",
            booking.booking_id,
            gbt.expires_at,
            hotel_slug,
        )
        return None

    if booking_slug != hotel_slug:
        logger.warning(
            "guest_access _try_gbt: SLUG MISMATCH "
            "booking_id=%s requested_slug=%r booking_slug=%r",
            booking.booking_id,
            hotel_slug,
            booking_slug,
        )
        return None

    gbt.last_used_at = timezone.now()
    gbt.save(update_fields=["last_used_at"])

    scopes = gbt.scopes if gbt.scopes else list(_MANAGEMENT_TOKEN_IMPLIED_SCOPES)

    return GuestAccessContext(
        booking=gbt.booking,
        room=gbt.booking.assigned_room,
        scopes=scopes,
        token_type="guest_booking",
        token_obj=gbt,
    )
