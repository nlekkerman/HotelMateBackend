"""
Guest Portal Views - Token-Authenticated Endpoints

Endpoints for guests to access their booking context, chat, and room services
using BookingManagementToken authentication. Uses assigned_room as room source of truth.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import logging

from common.guest_access import (
    resolve_guest_access_without_slug,
    GuestAccessError,
    InvalidTokenError,
)
from common.guest_auth import (
    TokenAuthenticationMixin,
    GuestTokenBurstThrottle,
    GuestTokenSustainedThrottle,
)
from common.guest_chat_grant import issue_guest_chat_grant

logger = logging.getLogger(__name__)


@method_decorator(never_cache, name='dispatch')
class GuestContextView(APIView, TokenAuthenticationMixin):
    """
    Get guest booking context using token authentication.
    
    Returns booking details with assigned_room as room source of truth.
    No hotel slug required - token contains all context.
    
    Authentication: GuestBookingToken via Authorization header or ?token= param
    Rate limit: 60 requests/minute per token
    
    Response format:
    {
        "booking_id": "BK-2025-0003",
        "hotel_slug": "test-hotel",
        "assigned_room": {
            "room_number": "101",
            "room_type_name": "Standard Room"
        },
        "guest_name": "John Doe", 
        "check_in": "2025-01-15",
        "check_out": "2025-01-17",
        "status": "CHECKED_IN",
        "party_size": 2,
        "is_checked_in": true,
        "is_checked_out": false,
        "allowed_actions": ["chat", "room_service", "view_booking"]
    }
    """
    authentication_classes = []  # Disable DRF's default TokenAuthentication — we do our own token validation
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]
    
    def get(self, request):
        """Get booking context for authenticated guest"""
        try:
            # Extract and validate token
            raw_token = self.get_token_from_request(request)
            if not raw_token:
                return Response(
                    {'error': 'MISSING_TOKEN', 'detail': 'Token required for guest access'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Resolve via canonical guest access (hotel_slug extracted from booking)
            # GuestContextView doesn't have hotel_slug in URL, so we need a
            # two-step approach: first try without slug constraint.
            ctx = resolve_guest_access_without_slug(raw_token)
            
            booking = ctx.booking
            room_info = None
            if booking.assigned_room:
                room_info = {
                    'room_number': booking.assigned_room.room_number,
                    'room_type_name': booking.assigned_room.room_type.name,
                }

            # Determine allowed actions
            allowed_actions = []
            if 'STATUS_READ' in ctx.scopes:
                allowed_actions.append('view_booking')
            if 'CHAT' in ctx.scopes and booking.status in ('CONFIRMED', 'CHECKED_IN'):
                allowed_actions.append('chat')
            if ('ROOM_SERVICE' in ctx.scopes
                    and booking.status == 'CHECKED_IN'
                    and booking.assigned_room):
                allowed_actions.append('room_service')

            # Issue guest chat grant if chat is allowed
            guest_chat_grant = None
            chat_eligible = 'chat' in allowed_actions
            if chat_eligible:
                guest_chat_grant = issue_guest_chat_grant(booking, booking.assigned_room)

            context = {
                'booking_id': booking.booking_id,
                'hotel_slug': booking.hotel.slug,
                'assigned_room': room_info,
                'guest_name': booking.primary_guest_name,
                'check_in': booking.check_in,
                'check_out': booking.check_out,
                'status': booking.status,
                'party_size': booking.adults + booking.children,
                'is_checked_in': booking.status == 'CHECKED_IN',
                'is_checked_out': booking.status == 'CHECKED_OUT',
                'allowed_actions': allowed_actions,
                'chat_available': chat_eligible,
                'guest_chat_grant': guest_chat_grant,
            }

            logger.info(
                f"Guest context accessed: booking_id={booking.booking_id}, "
                f"room={room_info['room_number'] if room_info else 'unassigned'}"
            )
            return Response(context, status=status.HTTP_200_OK)

        except GuestAccessError as e:
            logger.warning(f"Guest context access failed: {e.message}")
            return Response(
                {'error': e.code, 'detail': e.message},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Guest context error: {str(e)}")
            return Response(
                {'error': 'SERVER_ERROR', 'detail': 'Unable to retrieve booking context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )