"""
Guest Portal Views - Token-Authenticated Endpoints

Endpoints for guests to access their booking context, chat, and room services
using GuestBookingToken authentication. Uses assigned_room as room source of truth.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import logging

from hotel.services.booking import resolve_token_context, resolve_in_house_context
from hotel.models import GuestBookingToken

logger = logging.getLogger(__name__)


class TokenAuthenticationMixin:
    """
    Mixin for token-based authentication using GuestBookingToken.
    Extracts token from Authorization header or query parameter.
    """
    
    def get_token_from_request(self, request):
        """Extract token from request headers or query params"""
        # Try Authorization header first
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.replace('Bearer ', '')
        elif auth_header.startswith('GuestToken '):
            return auth_header.replace('GuestToken ', '')
        
        # Fall back to query parameter
        return request.GET.get('token', '')


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
            
            # Get booking context via service
            context = resolve_token_context(raw_token)
            
            logger.info(f"Guest context accessed: booking_id={context['booking_id']}, "
                       f"room={context.get('assigned_room', {}).get('room_number', 'unassigned')}")
            
            return Response(context, status=status.HTTP_200_OK)
            
        except Http404 as e:
            logger.warning(f"Guest context access failed: {str(e)}")
            return Response(
                {'error': 'INVALID_TOKEN', 'detail': 'Token is invalid or expired'},
                status=status.HTTP_404_NOT_FOUND
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
            
            # Get booking context
            context = resolve_token_context(raw_token)
            
            # Check if chat is allowed
            if 'chat' not in context['allowed_actions']:
                return Response(
                    {'error': 'CHAT_NOT_AVAILABLE', 'detail': 'Chat not available for current booking status'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Build chat context
            chat_context = {
                'chat_enabled': True,
                'channel_name': f"private-guest-booking.{context['booking_id']}",
                'booking_context': {
                    'booking_id': context['booking_id'],
                    'hotel_name': context.get('hotel_slug', '').replace('-', ' ').title(),
                    'guest_name': context['guest_name'],
                    'room_number': context.get('assigned_room', {}).get('room_number', 'Unassigned')
                },
                'recent_messages': []  # TODO: Implement message history retrieval
            }
            
            logger.info(f"Guest chat context accessed: booking_id={context['booking_id']}")
            
            return Response(chat_context, status=status.HTTP_200_OK)
            
        except Http404 as e:
            logger.warning(f"Guest chat access failed: {str(e)}")
            return Response(
                {'error': 'INVALID_TOKEN', 'detail': 'Token is invalid or expired'},
                status=status.HTTP_404_NOT_FOUND
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
    
    Response format:
    {
        "room_service_enabled": true,
        "in_house": true,
        "room_context": {
            "room_number": "101",
            "room_type_name": "Standard Room", 
            "floor": "1",
            "amenities": ["WiFi", "TV"],
            "check_in_time": "2025-01-15T15:30:00Z",
            "expected_checkout": "2025-01-17"
        },
        "menu_categories": [...], // Available service categories
        "order_history": [...] // Recent orders
    }
    """
    
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
            
            # Check if guest is in-house
            is_in_house, room_context = resolve_in_house_context(raw_token)
            
            if not is_in_house:
                # Get basic context for better error message
                basic_context = resolve_token_context(raw_token)
                return Response(
                    {
                        'error': 'NOT_IN_HOUSE',
                        'detail': 'Room service only available for checked-in guests',
                        'booking_status': basic_context['status'],
                        'room_service_enabled': False
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Build room service context
            service_context = {
                'room_service_enabled': True,
                'in_house': True,
                'room_context': room_context,
                'menu_categories': [],  # TODO: Implement menu retrieval
                'order_history': []     # TODO: Implement order history
            }
            
            logger.info(f"Guest room service accessed: room={room_context['room_number']}")
            
            return Response(service_context, status=status.HTTP_200_OK)
            
        except Http404 as e:
            logger.warning(f"Guest room service access failed: {str(e)}")
            return Response(
                {'error': 'INVALID_TOKEN', 'detail': 'Token is invalid or expired'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Guest room service error: {str(e)}")
            return Response(
                {'error': 'SERVER_ERROR', 'detail': 'Unable to retrieve room service context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )