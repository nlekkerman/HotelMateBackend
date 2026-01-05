"""
Canonical Guest Chat API Views - Token-only, No Legacy

Clean token-only guest chat endpoints with centralized validation, 
UX-friendly pre-checkin handling, booking-scoped channels, and 
complete legacy elimination. All business rules live in the service layer.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import logging

from bookings.services import (
    resolve_guest_chat_context, 
    InvalidTokenError, 
    NotInHouseError, 
    NoRoomAssignedError,
    MissingScopeError
)
from chat.models import RoomMessage, Conversation
from staff.models import Staff
from notifications.notification_manager import NotificationManager

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
class GuestChatContextView(APIView, TokenAuthenticationMixin):
    """
    GET/POST /api/guest/hotel/{hotel_slug}/chat/context?token=...
    
    Returns chat context with UX-friendly pre-checkin handling.
    Always returns 200 for valid tokens with allowed_actions and disabled_reason.
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        """Get chat context for guest token"""
        return self._get_context(request, hotel_slug)
    
    def post(self, request, hotel_slug):
        """Post method for compatibility - same as GET"""
        return self._get_context(request, hotel_slug)
    
    def _get_context(self, request, hotel_slug):
    def _get_context(self, request, hotel_slug):
        """Get chat context for guest token"""
        try:
            # Extract token
            token_str = self.get_token_from_request(request)
            if not token_str:
                return Response(
                    {'error': 'Token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Resolve context with UX-friendly mode (action_required=False)
            booking, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                hotel_slug=hotel_slug,
                token_str=token_str,
                required_scopes=["CHAT"],
                action_required=False
            )
            
            # Get current staff handler if available
            current_staff_handler = None
            if conversation:
                # Get the latest staff participant
                latest_staff_participant = conversation.guest_participants.filter(
                ).select_related('staff').order_by('-joined_at').first()
                
                if latest_staff_participant:
                    staff = latest_staff_participant.staff
                    current_staff_handler = {
                        "name": staff.get_full_name(),
                        "role": staff.role or "Staff"
                    }
            
            # Build booking-scoped pusher channel
            pusher_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"
            
            response_data = {
                "conversation_id": conversation.id if conversation else None,
                "booking_id": booking.booking_id,
                "room_number": room.room_number if room else None,
                "assigned_room_id": room.id if room else None,
                "allowed_actions": ["chat"] if allowed_actions["can_chat"] else [],
                "pusher": {
                    "channel": pusher_channel,
                    "event": "realtime_event"
                },
                "current_staff_handler": current_staff_handler
            }
            
            # Add disabled_reason if chat is not available
            if disabled_reason:
                response_data["disabled_reason"] = disabled_reason
            
            logger.info(
                f"✅ Chat context provided: booking={booking.booking_id}, "
                f"can_chat={allowed_actions['can_chat']}, reason={disabled_reason}"
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except InvalidTokenError as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        except MissingScopeError as e:
            return Response(
                {'error': f'Token lacks required permissions: {", ".join(e.required_scopes)}'},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            logger.error(f"Chat context error: {str(e)}")
            return Response(
                {'error': 'Unable to retrieve chat context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatSendMessageView(APIView, TokenAuthenticationMixin):
    """
    POST /api/guest/hotel/{hotel_slug}/chat/messages?token=...
    
    Sends chat message with strict validation (action_required=True).
    Returns 403 for pre-checkin guests, 409 for missing room assignment.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, hotel_slug):
        """Send chat message from guest"""
        try:
            # Extract token
            token_str = self.get_token_from_request(request)
            if not token_str:
                return Response(
                    {'error': 'Token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Resolve context with strict validation (action_required=True)
            booking, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                hotel_slug=hotel_slug,
                token_str=token_str,
                required_scopes=["CHAT"],
                action_required=True
            )
            
            # Validate request data
            message_text = request.data.get('message', '').strip()
            if not message_text:
                return Response(
                    {'error': 'Message text is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            reply_to_id = request.data.get('reply_to')
            reply_to_message = None
            if reply_to_id:
                try:
                    reply_to_message = RoomMessage.objects.get(
                        id=reply_to_id,
                        conversation=conversation
                    )
                except RoomMessage.DoesNotExist:
                    return Response(
                        {'error': 'Reply message not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create message with room snapshot
            message = RoomMessage.objects.create(
                conversation=conversation,
                sender_type='guest',
                message=message_text,
                booking=booking,
                room=room,  # Room snapshot at time of message
                reply_to=reply_to_message
            )
            
            # Fire realtime event using existing NotificationManager
            notification_manager = NotificationManager()
            notification_manager.realtime_guest_chat_message_created(message)
            
            logger.info(
                f"✅ Guest message sent: booking={booking.booking_id}, "
                f"room={room.room_number}, message_id={message.id}"
            )
            
            return Response(
                {
                    'message_id': message.id,
                    'sent_at': message.timestamp.isoformat(),
                    'conversation_id': conversation.id
                },
                status=status.HTTP_201_CREATED
            )
            
        except InvalidTokenError as e:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_404_NOT_FOUND
            )
        except MissingScopeError as e:
            return Response(
                {'error': f'Token lacks required permissions: {", ".join(e.required_scopes)}'},
                status=status.HTTP_403_FORBIDDEN
            )
        except NotInHouseError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except NoRoomAssignedError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            logger.error(f"Send message error: {str(e)}")
            return Response(
                {'error': 'Unable to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )