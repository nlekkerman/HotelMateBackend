"""
Shared guest token authentication utilities.

Centralizes GuestBookingToken extraction and validation logic used by
guest-facing endpoints (chat, room service, portal). Staff auth is not
affected — this module is for guest-token flows only.
"""

import hashlib
import logging

from django.utils import timezone
from rest_framework.throttling import AnonRateThrottle

from hotel.models import GuestBookingToken

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token extraction mixin (single source of truth)
# ---------------------------------------------------------------------------

class TokenAuthenticationMixin:
    """
    Mixin that extracts a GuestBookingToken from the request.

    Supported transports (in priority order):
        1. Authorization: Bearer <token>
        2. Authorization: GuestToken <token>
        3. ?token=<token> query parameter
    """

    def get_token_from_request(self, request):
        """Return the raw token string or empty string."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        if auth_header.startswith('GuestToken '):
            return auth_header[11:]
        return request.GET.get('token', '')


# ---------------------------------------------------------------------------
# Lightweight token → booking resolver (no conversation logic)
# ---------------------------------------------------------------------------

def resolve_guest_token(token_str, hotel_slug, required_scopes=None,
                        require_checked_in=False):
    """
    Validate a raw guest token and return (guest_token_obj, booking, room).

    Raises ValueError with a UI-safe message on any validation failure.
    The caller should translate ValueError into the appropriate HTTP response.

    Args:
        token_str:          Raw token string from the request.
        hotel_slug:         Hotel slug from the URL (for anti-enumeration check).
        required_scopes:    Optional list of scopes the token must carry.
        require_checked_in: If True, booking must be in-house (checked in,
                            not checked out, room assigned).

    Returns:
        (GuestBookingToken, RoomBooking, Room-or-None)
    """
    if not token_str or not token_str.strip():
        raise ValueError("Token is required")

    token_hash = hashlib.sha256(token_str.strip().encode('utf-8')).hexdigest()

    try:
        guest_token = GuestBookingToken.objects.select_related(
            'booking__hotel',
            'booking__assigned_room',
        ).get(token_hash=token_hash, status='ACTIVE')
    except GuestBookingToken.DoesNotExist:
        raise ValueError("Invalid or expired token")

    # Expiration
    if guest_token.expires_at and timezone.now() > guest_token.expires_at:
        raise ValueError("Invalid or expired token")

    booking = guest_token.booking

    # Hotel match (anti-enumeration — always return same message)
    if booking.hotel.slug != hotel_slug:
        raise ValueError("Invalid or expired token")

    # Booking status
    if booking.status in ('CANCELLED', 'CANCELLED_DRAFT', 'DECLINED'):
        raise ValueError("Invalid or expired token")

    # Scopes
    if required_scopes:
        token_scopes = guest_token.scopes or []
        missing = [s for s in required_scopes if s not in token_scopes]
        if missing:
            raise ValueError(f"Token lacks required permissions: {', '.join(missing)}")

    # In-house check
    if require_checked_in:
        if not booking.checked_in_at:
            raise ValueError("Guest has not checked in yet")
        if booking.checked_out_at:
            raise ValueError("Guest has already checked out")
        if not booking.assigned_room:
            raise ValueError("No room assigned to this booking")

    # Touch last_used_at
    guest_token.last_used_at = timezone.now()
    guest_token.save(update_fields=['last_used_at'])

    return guest_token, booking, booking.assigned_room


# ---------------------------------------------------------------------------
# Throttle classes for public / guest endpoints
# ---------------------------------------------------------------------------

class PublicBurstThrottle(AnonRateThrottle):
    """Short-window burst limit for public endpoints."""
    scope = 'public_burst'


class PublicSustainedThrottle(AnonRateThrottle):
    """Longer-window sustained limit for public endpoints."""
    scope = 'public_sustained'


class GuestTokenBurstThrottle(AnonRateThrottle):
    """Burst limit keyed by IP for guest-token endpoints."""
    scope = 'guest_burst'


class GuestTokenSustainedThrottle(AnonRateThrottle):
    """Sustained limit keyed by IP for guest-token endpoints."""
    scope = 'guest_sustained'
