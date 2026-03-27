"""
Canonical Guest Chat API Views — Grant-Authenticated, Booking-Bound

Guest chat endpoints authenticate via a short-lived signed grant issued
by the bootstrap endpoint (/api/guest/context/). The raw email/booking
token is NEVER used here — it is only consumed at bootstrap time.

Auth flow:
  1. Guest bootstraps with raw token → gets guest_chat_grant
  2. All chat endpoints accept: Authorization: GuestChatGrant <grant>
     or ?chat_grant=<grant>
  3. Grant is validated (signature + expiry + hotel match)
  4. Booking + conversation resolved from grant claims

Conversation is keyed by booking_id. Room is contextual metadata.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
import logging

from bookings.services import resolve_chat_context_from_grant
from common.guest_access import GuestAccessError
from common.guest_chat_grant import (
    validate_guest_chat_grant,
    GuestChatGrantError,
)
from chat.models import RoomMessage
from notifications.notification_manager import NotificationManager
from django.conf import settings
import json
import hmac
import hashlib

from common.guest_auth import (
    ChatGrantAuthenticationMixin,
    GuestTokenBurstThrottle,
    GuestTokenSustainedThrottle,
)

logger = logging.getLogger(__name__)


def _grant_error_response(e):
    """Standard error response for grant validation failures."""
    return Response(
        {'error': e.message, 'code': e.code},
        status=e.status_code,
    )


@method_decorator(never_cache, name='dispatch')
class GuestChatContextView(APIView, ChatGrantAuthenticationMixin):
    """
    GET/POST /api/guest/hotel/{hotel_slug}/chat/context
    Header: Authorization: GuestChatGrant <grant>

    Returns chat context with UX-friendly pre-checkin handling.
    Always returns 200 for valid grants with allowed_actions and disabled_reason.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def get(self, request, hotel_slug):
        return self._get_context(request, hotel_slug)

    def post(self, request, hotel_slug):
        return self._get_context(request, hotel_slug)

    def _get_context(self, request, hotel_slug):
        try:
            grant_str = self.get_chat_grant_from_request(request)
            if not grant_str:
                return Response(
                    {'error': 'Guest chat grant is required', 'code': 'GRANT_REQUIRED'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            grant_ctx = validate_guest_chat_grant(grant_str, hotel_slug)
            booking, room, conversation = resolve_chat_context_from_grant(grant_ctx)

            # Determine chat eligibility from current booking state
            can_chat = bool(
                booking.checked_in_at
                and not booking.checked_out_at
                and booking.assigned_room
            )
            disabled_reason = None
            if not booking.checked_in_at:
                disabled_reason = "Check-in required to access chat"
            elif booking.checked_out_at:
                disabled_reason = "Chat unavailable after checkout"
            elif not booking.assigned_room:
                disabled_reason = "Room assignment required"

            pusher_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"

            response_data = {
                "conversation_id": conversation.id if conversation else None,
                "booking_id": booking.booking_id,
                "room_number": room.room_number if room else None,
                "assigned_room_id": room.id if room else None,
                "allowed_actions": ["chat"] if can_chat else [],
                "pusher": {
                    "channel": pusher_channel,
                    "event": "realtime_event",
                },
            }

            if disabled_reason:
                response_data["disabled_reason"] = disabled_reason

            return Response(response_data, status=status.HTTP_200_OK)

        except GuestChatGrantError as e:
            return _grant_error_response(e)
        except GuestAccessError as e:
            return Response({'error': e.message, 'code': e.code}, status=e.status_code)
        except Exception as e:
            logger.error(f"Chat context error: {str(e)}")
            return Response(
                {'error': 'Unable to retrieve chat context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatSendMessageView(APIView, ChatGrantAuthenticationMixin):
    """
    GET/POST /api/guest/hotel/{hotel_slug}/chat/messages
    Header: Authorization: GuestChatGrant <grant>

    GET: Retrieve chat messages for the guest's conversation
    POST: Send chat message (must be checked-in with room assigned)
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def get(self, request, hotel_slug):
        try:
            grant_str = self.get_chat_grant_from_request(request)
            if not grant_str:
                return Response(
                    {'error': 'Guest chat grant is required', 'code': 'GRANT_REQUIRED'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            grant_ctx = validate_guest_chat_grant(grant_str, hotel_slug)
            booking, room, conversation = resolve_chat_context_from_grant(grant_ctx)

            # Pagination
            limit = int(request.GET.get('limit', 50))
            before_id = request.GET.get('before_id')

            messages_qs = conversation.messages.filter(
                is_deleted=False,
            ).select_related('reply_to').order_by('-timestamp')

            if before_id:
                messages_qs = messages_qs.filter(id__lt=before_id)

            messages = list(messages_qs[:limit])[::-1]

            from chat.serializers import RoomMessageSerializer
            serializer = RoomMessageSerializer(messages, many=True)

            return Response({
                'messages': serializer.data,
                'conversation_id': conversation.id,
                'count': len(messages),
                'has_more': messages_qs.count() > limit,
            })

        except GuestChatGrantError as e:
            return _grant_error_response(e)
        except GuestAccessError as e:
            return Response({'error': e.message, 'code': e.code}, status=e.status_code)
        except Exception as e:
            logger.error(f"Get messages error: {str(e)}")
            return Response(
                {'error': 'Unable to retrieve messages'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, hotel_slug):
        try:
            grant_str = self.get_chat_grant_from_request(request)
            if not grant_str:
                return Response(
                    {'error': 'Guest chat grant is required', 'code': 'GRANT_REQUIRED'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            grant_ctx = validate_guest_chat_grant(grant_str, hotel_slug)
            booking, room, conversation = resolve_chat_context_from_grant(grant_ctx)

            # Enforce in-house for sending messages
            if not booking.checked_in_at:
                return Response(
                    {'error': 'Guest has not checked in yet', 'code': 'NOT_CHECKED_IN'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if booking.checked_out_at:
                return Response(
                    {'error': 'Guest has already checked out', 'code': 'ALREADY_CHECKED_OUT'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not room:
                return Response(
                    {'error': 'No room assigned to this booking yet', 'code': 'NO_ROOM_ASSIGNED'},
                    status=status.HTTP_409_CONFLICT,
                )

            message_text = request.data.get('message', '').strip()
            if not message_text:
                return Response(
                    {'error': 'Message text is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reply_to_id = request.data.get('reply_to')
            reply_to_message = None
            if reply_to_id:
                try:
                    reply_to_message = RoomMessage.objects.get(
                        id=reply_to_id, conversation=conversation,
                    )
                except RoomMessage.DoesNotExist:
                    return Response(
                        {'error': 'Reply message not found'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            message = RoomMessage.objects.create(
                conversation=conversation,
                sender_type='guest',
                message=message_text,
                booking=booking,
                room=room,
                reply_to=reply_to_message,
            )

            notification_manager = NotificationManager()
            notification_manager.realtime_guest_chat_message_created(message)

            logger.info(
                f"Guest message sent: booking={booking.booking_id}, "
                f"room={room.room_number}, message_id={message.id}"
            )

            return Response(
                {
                    'message_id': message.id,
                    'sent_at': message.timestamp.isoformat(),
                    'conversation_id': conversation.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except GuestChatGrantError as e:
            return _grant_error_response(e)
        except GuestAccessError as e:
            return Response({'error': e.message, 'code': e.code}, status=e.status_code)
        except Exception as e:
            logger.error(f"Send message error: {str(e)}")
            return Response(
                {'error': 'Unable to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatPusherAuthView(APIView, ChatGrantAuthenticationMixin):
    """
    POST /api/guest/hotel/{hotel_slug}/chat/pusher/auth
    Header: Authorization: GuestChatGrant <grant>

    Pusher private channel authentication for guest chat.
    Validates grant and ensures channel matches booking.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def post(self, request, hotel_slug):
        try:
            socket_id = request.data.get('socket_id')
            channel_name = request.data.get('channel_name')

            if not socket_id or not channel_name:
                return Response(
                    {'error': 'Missing socket_id or channel_name'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            grant_str = self.get_chat_grant_from_request(request)
            if not grant_str:
                return Response(
                    {'error': 'Guest chat grant is required', 'code': 'GRANT_REQUIRED'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            grant_ctx = validate_guest_chat_grant(grant_str, hotel_slug)
            booking, room, conversation = resolve_chat_context_from_grant(grant_ctx)

            # CRITICAL SECURITY: Validate channel name exactly matches booking
            expected_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"
            if channel_name != expected_channel:
                logger.warning(
                    f"Guest chat Pusher auth rejected: channel mismatch. "
                    f"Expected: {expected_channel}, Requested: {channel_name}, "
                    f"Booking: {booking.booking_id}"
                )
                return Response(
                    {'error': 'Channel name does not match booking'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            channel_data = {
                "user_id": f"guest-{booking.booking_id}",
                "user_info": {
                    "type": "guest",
                    "booking_id": booking.booking_id,
                    "hotel_slug": hotel_slug,
                    "room_number": room.room_number if room else None,
                    "guest_name": booking.primary_guest_name,
                },
            }

            auth_response = self._generate_pusher_auth(socket_id, channel_name, channel_data)

            logger.info(
                f"Guest chat Pusher auth successful: booking={booking.booking_id}, "
                f"channel={channel_name}"
            )

            return Response(auth_response)

        except GuestChatGrantError as e:
            return _grant_error_response(e)
        except GuestAccessError as e:
            return Response({'error': e.message, 'code': e.code}, status=e.status_code)
        except Exception as e:
            logger.error(f"Guest chat Pusher auth error: {str(e)}")
            return Response(
                {'error': 'Unable to authenticate channel'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _generate_pusher_auth(self, socket_id, channel_name, channel_data=None):
        if channel_data:
            channel_data_str = json.dumps(channel_data)
            string_to_sign = f"{socket_id}:{channel_name}:{channel_data_str}"
        else:
            string_to_sign = f"{socket_id}:{channel_name}"

        signature = hmac.new(
            settings.PUSHER_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        auth_string = f"{settings.PUSHER_KEY}:{signature}"

        result = {"auth": auth_string}
        if channel_data:
            result["channel_data"] = channel_data_str

        return result
