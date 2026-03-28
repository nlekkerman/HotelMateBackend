"""
Canonical Guest Booking Token Service

PRODUCT RULE: ONE stable identity token per booking.
    - Created once at booking creation.
    - NEVER rotated, regenerated, or mutated by any workflow.
    - Valid until booking reaches COMPLETED/CANCELLED/DECLINED.
    - Plaintext is available ONLY at creation time.

This is the SINGLE issuance path for GuestBookingToken. All code that needs
a guest token for a booking MUST go through get_or_create_guest_token().
Direct calls to GuestBookingToken.generate_token() or .objects.create()
are reserved for tests and seed scripts only.

FORBIDDEN PATTERNS:
    - rotate=True (removed)
    - needs_plaintext=True causing regeneration (removed)
    - Any workflow code that revokes/replaces a GBT
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

# Canonical scopes for booking-wide guest access.
DEFAULT_GUEST_SCOPES = ['STATUS_READ', 'CHAT', 'ROOM_SERVICE']


def _get_active_token(booking):
    """
    Return the single active, non-expired GuestBookingToken for a booking,
    or None.

    If legacy data left multiple active tokens, revoke all but the newest
    and return that one.
    """
    from hotel.models import GuestBookingToken

    active_qs = GuestBookingToken.objects.filter(
        booking=booking,
        status='ACTIVE',
    ).order_by('-created_at')

    active_tokens = list(active_qs[:2])  # Fetch at most 2 to detect duplicates

    if not active_tokens:
        return None

    token = active_tokens[0]

    # Check expiry
    if token.expires_at and timezone.now() > token.expires_at:
        logger.warning(
            "GBT expired for booking %s, expires_at=%s",
            booking.booking_id, token.expires_at,
        )
        return None

    # Legacy cleanup: if more than one active token exists, revoke extras.
    if len(active_tokens) > 1:
        extra_ids = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE',
        ).exclude(pk=token.pk).values_list('pk', flat=True)
        if extra_ids:
            GuestBookingToken.objects.filter(pk__in=list(extra_ids)).update(
                status='REVOKED',
                revoked_at=timezone.now(),
                revoked_reason='LEGACY_CLEANUP',
            )
            logger.info(
                "Legacy cleanup: revoked %d extra active tokens for booking %s",
                len(extra_ids), booking.booking_id,
            )

    return token


def _calculate_expiry(booking):
    """Default expiry: check_out + 30 days."""
    return timezone.make_aware(
        datetime.combine(booking.check_out, datetime.min.time())
    ) + timedelta(days=30)


def _create_new_token(booking):
    """
    Create a new GuestBookingToken inside an already-held atomic block.
    Returns (token_obj, raw_plaintext).
    """
    from hotel.models import GuestBookingToken

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token_obj = GuestBookingToken.objects.create(
        token_hash=token_hash,
        booking=booking,
        hotel=booking.hotel,
        expires_at=_calculate_expiry(booking),
        purpose='FULL_ACCESS',
        scopes=list(DEFAULT_GUEST_SCOPES),
    )
    return token_obj, raw_token


def get_or_create_guest_token(booking):
    """
    Canonical issuance / retrieval of a guest booking token.

    IDENTITY TOKEN RULES:
        - If an ACTIVE, non-expired token exists → return it (no plaintext).
        - If no usable token exists → create one and return plaintext.
        - NEVER rotate, regenerate, or replace an existing active token.
        - Plaintext is only available at initial creation time.

    Args:
        booking: RoomBooking instance.

    Returns:
        (token_obj, raw_token_or_none)
            raw_token is the plaintext string ONLY when a new token was
            created (first call for this booking). None when returning
            an existing token whose plaintext is unrecoverable.
    """
    from hotel.models import GuestBookingToken

    with transaction.atomic():
        existing = _get_active_token(booking)
        if existing is not None:
            logger.info(
                "Reusing existing GBT for booking %s (pk=%s)",
                booking.booking_id, existing.pk,
            )
            return existing, None

        # No active token — create the identity token.
        token_obj, raw_token = _create_new_token(booking)

    logger.info(
        "Created GBT identity token for booking %s (pk=%s)",
        booking.booking_id, token_obj.pk,
    )
    return token_obj, raw_token
