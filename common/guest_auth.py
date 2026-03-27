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
        1. ?token=<token> query parameter  (canonical — used by email links)
        2. Authorization: GuestToken <token>  (programmatic clients)

    Bearer is intentionally NOT supported to avoid collision with
    DRF's staff TokenAuthentication on requests that carry both.
    """

    def get_token_from_request(self, request):
        """Return the raw token string or empty string."""
        # 1. Query parameter — preferred, always unambiguous
        qp_token = request.GET.get('token', '')
        if qp_token:
            return qp_token
        # 2. GuestToken header — explicit guest namespace
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('GuestToken '):
            return auth_header[11:]
        return ''


class ChatGrantAuthenticationMixin:
    """
    Mixin that extracts a guest chat grant from the request.

    The grant is a short-lived signed token issued by the bootstrap
    endpoint after successful raw-token resolution. Chat endpoints
    use this instead of the raw email/booking token.

    Supported transports (in priority order):
        1. Authorization: GuestChatGrant <grant>  (programmatic — preferred)
        2. ?chat_grant=<grant> query parameter      (fallback)
    """

    def get_chat_grant_from_request(self, request):
        """Return the raw grant string or empty string."""
        # 1. Header — preferred for POST bodies
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('GuestChatGrant '):
            return auth_header[15:]
        # 2. Query parameter fallback
        qp_grant = request.GET.get('chat_grant', '')
        if qp_grant:
            return qp_grant
        return ''


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
