"""
Canonical Guest Booking Token Service

One active reusable guest token per booking. Rotate only when explicitly
requested or when no active usable token exists.

This is the SINGLE issuance path for GuestBookingToken. All code that needs
a guest token for a booking MUST go through get_or_create_guest_token().
Direct calls to GuestBookingToken.generate_token() or .objects.create()
are reserved for tests and seed scripts only.

Plaintext recovery:
    The DB stores only SHA-256 hashes. Plaintext is available ONLY at
    creation time. Callers that need plaintext for links/emails should
    pass needs_plaintext=True. If an active token exists but plaintext
    is unrecoverable, the service rotates to produce a fresh plaintext.
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
        # Expired — not usable. Don't revoke here; let caller rotate.
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


def get_or_create_guest_token(booking, *, rotate=False, needs_plaintext=False):
    """
    Canonical issuance / retrieval of a guest booking token.

    Policy:
        - One active reusable guest token per booking.
        - Reuse the existing active token when possible.
        - Rotate only when: no usable token exists, token is expired/revoked,
          or rotate=True is explicitly passed.
        - When needs_plaintext=True and plaintext is unrecoverable (hash-only
          storage), rotate to produce a fresh plaintext token.

    Args:
        booking:          RoomBooking instance.
        rotate:           Force-rotate even if an active token exists.
        needs_plaintext:  Caller requires the raw token string (e.g. for
                          email links). If True and an active token exists
                          but plaintext cannot be recovered, a rotation is
                          performed.

    Returns:
        (token_obj, raw_token_or_none)
            raw_token is the plaintext string when a new token was created
            or when rotation occurred; None when reusing an existing token
            whose plaintext is unrecoverable.
    """
    from hotel.models import GuestBookingToken

    with transaction.atomic():
        if not rotate:
            existing = _get_active_token(booking)
            if existing is not None:
                if needs_plaintext:
                    # Plaintext is not stored — must rotate to get one.
                    # Fall through to rotation below.
                    pass
                else:
                    # Reuse: active token object returned, no plaintext.
                    return existing, None

        # Revoke any active tokens before creating a new one.
        GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE',
        ).update(
            status='REVOKED',
            revoked_at=timezone.now(),
            revoked_reason='TOKEN_REPLACED',
        )

        token_obj, raw_token = _create_new_token(booking)

    logger.info(
        "Issued guest token for booking %s (rotate=%s, needs_plaintext=%s)",
        booking.booking_id, rotate, needs_plaintext,
    )
    return token_obj, raw_token
