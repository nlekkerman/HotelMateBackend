"""
Shared guest token authentication utilities.

Centralizes token extraction and throttle classes used by
guest-facing endpoints (chat, room service, portal).

All token validation is delegated to common.guest_access.resolve_guest_access().
This module provides only the extraction mixin and throttle classes.
"""

import logging

from rest_framework.throttling import AnonRateThrottle

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token extraction mixin (single source of truth)
# ---------------------------------------------------------------------------

class TokenAuthenticationMixin:
    """
    Mixin that extracts a guest token from the request.

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
