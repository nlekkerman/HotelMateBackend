"""
Guest Portal Views - Token-Authenticated Endpoints

Endpoints for guests to access their booking context, chat, and room services
using BookingManagementToken authentication. Uses assigned_room as room source of truth.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
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
    permission_classes = []
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


@method_decorator(never_cache, name='dispatch') 
class GuestChatContextView(APIView, TokenAuthenticationMixin):
    """
    Get chat context for guest using token authentication.
    
    Returns chat channel information and recent messages for the booking.
    Only available for CONFIRMED and CHECKED_IN bookings.
    
    Authentication: GuestBookingToken via Authorization header or ?token= param
    
    Response format:
    {
        "chat_enabled": true,
        "channel_name": "private-guest-booking.BK-2025-0003",
        "booking_context": {
            "booking_id": "BK-2025-0003",
            "hotel_name": "Test Hotel",
            "guest_name": "John Doe",
            "room_number": "101"
        },
        "recent_messages": [...] // Last 50 messages
    }
    """
    permission_classes = []
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]
    
    def get(self, request):
        """Get chat context for authenticated guest"""
        try:
            # Extract and validate token
            raw_token = self.get_token_from_request(request)
            if not raw_token:
                return Response(
                    {'error': 'MISSING_TOKEN', 'detail': 'Token required for chat access'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            ctx = resolve_guest_access_without_slug(raw_token)
            booking = ctx.booking

            # Check if chat is allowed
            chat_allowed = (
                'CHAT' in ctx.scopes
                and booking.status in ('CONFIRMED', 'CHECKED_IN')
            )
            if not chat_allowed:
                return Response(
                    {'error': 'CHAT_NOT_AVAILABLE', 'detail': 'Chat not available for current booking status'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            room_number = (
                booking.assigned_room.room_number
                if booking.assigned_room else 'Unassigned'
            )

            chat_context = {
                'chat_enabled': True,
                'channel_name': f"private-guest-booking.{booking.booking_id}",
                'booking_context': {
                    'booking_id': booking.booking_id,
                    'hotel_name': booking.hotel.name,
                    'guest_name': booking.primary_guest_name,
                    'room_number': room_number,
                },
                'recent_messages': [],
            }
            
            logger.info(f"Guest chat context accessed: booking_id={booking.booking_id}")
            return Response(chat_context, status=status.HTTP_200_OK)
            
        except GuestAccessError as e:
            logger.warning(f"Guest chat access failed: {e.message}")
            return Response(
                {'error': e.code, 'detail': e.message},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Guest chat error: {str(e)}")
            return Response(
                {'error': 'SERVER_ERROR', 'detail': 'Unable to retrieve chat context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(never_cache, name='dispatch')
class GuestRoomServiceView(APIView, TokenAuthenticationMixin):
    """
    Get room service context for in-house guests using token authentication.
    
    Returns room service menu and ordering context.
    Only available for CHECKED_IN guests with assigned rooms.
    
    Authentication: GuestBookingToken via Authorization header or ?token= param
    """
    permission_classes = []
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]
    
    def get(self, request):
        """Get room service context for authenticated in-house guest"""
        try:
            # Extract and validate token  
            raw_token = self.get_token_from_request(request)
            if not raw_token:
                return Response(
                    {'error': 'MISSING_TOKEN', 'detail': 'Token required for room service access'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            ctx = resolve_guest_access_without_slug(raw_token)
            booking = ctx.booking

            is_in_house = ctx.is_in_house
            if not is_in_house:
                return Response(
                    {
                        'error': 'NOT_IN_HOUSE',
                        'detail': 'Room service only available for checked-in guests',
                        'booking_status': booking.status,
                        'room_service_enabled': False,
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            room = booking.assigned_room
            room_context = {
                'room_number': room.room_number,
                'room_type_name': room.room_type.name,
                'floor': room.floor,
                'amenities': room.room_type.amenities or [],
                'check_in_time': booking.checked_in_at,
                'expected_checkout': booking.check_out,
            }

            service_context = {
                'room_service_enabled': True,
                'in_house': True,
                'room_context': room_context,
                'menu_categories': [],
                'order_history': [],
            }
            
            logger.info(f"Guest room service accessed: room={room.room_number}")
            return Response(service_context, status=status.HTTP_200_OK)
            
        except GuestAccessError as e:
            logger.warning(f"Guest room service access failed: {e.message}")
            return Response(
                {'error': e.code, 'detail': e.message},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Guest room service error: {str(e)}")
            return Response(
                {'error': 'SERVER_ERROR', 'detail': 'Unable to retrieve room service context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )