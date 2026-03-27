"""
Canonical Guest Chat API Views — Session-Authenticated, Booking-Bound

Guest chat endpoints authenticate via a short-lived signed session
issued by the bootstrap endpoint (/api/guest/context/). The raw
email/booking token is NEVER accepted here.

Auth header (single transport, no fallback):
    X-Guest-Chat-Session: <session>

Session is validated for signature, expiry, scope, and hotel match.
Conversation is keyed by booking_id. Room is contextual metadata.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.utils import timezone
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
    ChatSessionAuthenticationMixin,
    GuestTokenBurstThrottle,
    GuestTokenSustainedThrottle,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Shared helpers
# -------------------------------------------------------------------

def _session_error_response(e):
    """Standard error response for session validation failures."""
    return Response(
        {'error': e.message, 'code': e.code},
        status=e.status_code,
    )


def _missing_session_response():
    return Response(
        {
            'error': 'Guest chat session is required',
            'code': 'SESSION_REQUIRED',
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


def _resolve_from_request(mixin, request, hotel_slug):
    """
    Extract session header, validate, resolve booking+conversation.

    Returns (grant_ctx, booking, room, conversation) on success.
    Returns (None, None, None, Response) with error Response on failure.
    """
    session_str = mixin.get_chat_session_from_request(request)
    if not session_str:
        return None, None, None, _missing_session_response()

    try:
        grant_ctx = validate_guest_chat_grant(session_str, hotel_slug)
        booking, room, conversation = (
            resolve_chat_context_from_grant(grant_ctx)
        )
        return grant_ctx, booking, room, conversation
    except GuestChatGrantError as e:
        return None, None, None, _session_error_response(e)
    except GuestAccessError as e:
        return None, None, None, Response(
            {'error': e.message, 'code': e.code},
            status=e.status_code,
        )


# -------------------------------------------------------------------
# Views
# -------------------------------------------------------------------

@method_decorator(never_cache, name='dispatch')
class GuestChatContextView(APIView, ChatSessionAuthenticationMixin):
    """
    GET /api/guest/hotel/{slug}/chat/context
    Header: X-Guest-Chat-Session: <session>

    Returns conversation context and Pusher channel info.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def get(self, request, hotel_slug):
        grant_ctx, booking, room, result = _resolve_from_request(
            self, request, hotel_slug,
        )
        if isinstance(result, Response):
            return result
        conversation = result

        try:
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

            pusher_channel = (
                f"private-hotel-{hotel_slug}"
                f"-guest-chat-booking-{booking.booking_id}"
            )

            data = {
                "conversation_id": (
                    conversation.id if conversation else None
                ),
                "booking_id": booking.booking_id,
                "room_number": (
                    room.room_number if room else None
                ),
                "assigned_room_id": room.id if room else None,
                "allowed_actions": (
                    ["chat"] if can_chat else []
                ),
                "pusher": {
                    "channel": pusher_channel,
                    "event": "realtime_event",
                },
            }

            if disabled_reason:
                data["disabled_reason"] = disabled_reason

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Chat context error: {e}")
            return Response(
                {'error': 'Unable to retrieve chat context'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatSendMessageView(
    APIView, ChatSessionAuthenticationMixin,
):
    """
    GET  /api/guest/hotel/{slug}/chat/messages
    POST /api/guest/hotel/{slug}/chat/messages
    Header: X-Guest-Chat-Session: <session>
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def get(self, request, hotel_slug):
        grant_ctx, booking, room, result = _resolve_from_request(
            self, request, hotel_slug,
        )
        if isinstance(result, Response):
            return result
        conversation = result

        try:
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

        except Exception as e:
            logger.error(f"Get messages error: {e}")
            return Response(
                {'error': 'Unable to retrieve messages'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, hotel_slug):
        grant_ctx, booking, room, result = _resolve_from_request(
            self, request, hotel_slug,
        )
        if isinstance(result, Response):
            return result
        conversation = result

        try:
            # Enforce in-house for sending messages
            if not booking.checked_in_at:
                return Response(
                    {
                        'error': 'Guest has not checked in yet',
                        'code': 'NOT_CHECKED_IN',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            if booking.checked_out_at:
                return Response(
                    {
                        'error': 'Guest has already checked out',
                        'code': 'ALREADY_CHECKED_OUT',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not room:
                return Response(
                    {
                        'error': 'No room assigned to this booking',
                        'code': 'NO_ROOM_ASSIGNED',
                    },
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
                        id=reply_to_id,
                        conversation=conversation,
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
            notification_manager.realtime_guest_chat_message_created(
                message,
            )

            logger.info(
                "Guest message sent: booking=%s room=%s msg=%s",
                booking.booking_id,
                room.room_number,
                message.id,
            )

            return Response(
                {
                    'message_id': message.id,
                    'sent_at': message.timestamp.isoformat(),
                    'conversation_id': conversation.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Send message error: {e}")
            return Response(
                {'error': 'Unable to send message'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatMarkReadView(
    APIView, ChatSessionAuthenticationMixin,
):
    """
    POST /api/guest/hotel/{slug}/chat/conversations/{id}/mark_read/
    Header: X-Guest-Chat-Session: <session>

    Marks all messages in the conversation as read by guest.
    Validates conversation belongs to the session's booking.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def post(self, request, hotel_slug, conversation_id):
        grant_ctx, booking, room, result = _resolve_from_request(
            self, request, hotel_slug,
        )
        if isinstance(result, Response):
            return result
        conversation = result

        try:
            # Verify the conversation_id matches the booking's
            if conversation.id != conversation_id:
                logger.warning(
                    "mark_read rejected: session conv=%s "
                    "requested conv=%s booking=%s",
                    conversation.id,
                    conversation_id,
                    booking.booking_id,
                )
                return Response(
                    {
                        'error': 'Conversation does not match booking',
                        'code': 'CONVERSATION_MISMATCH',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            now = timezone.now()
            updated = conversation.messages.filter(
                read_by_guest=False,
                sender_type__in=['staff', 'system'],
            ).update(
                read_by_guest=True,
                guest_read_at=now,
                status='read',
            )

            if updated:
                conversation.has_unread = False
                conversation.save(update_fields=['has_unread'])

            return Response(
                {'marked_read': updated},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Mark read error: {e}")
            return Response(
                {'error': 'Unable to mark messages read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(never_cache, name='dispatch')
class GuestChatPusherAuthView(
    APIView, ChatSessionAuthenticationMixin,
):
    """
    POST /api/guest/hotel/{slug}/chat/pusher/auth
    Header: X-Guest-Chat-Session: <session>

    Pusher private channel auth. Session-only, no raw token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    def post(self, request, hotel_slug):
        socket_id = request.data.get('socket_id')
        channel_name = request.data.get('channel_name')

        if not socket_id or not channel_name:
            return Response(
                {'error': 'Missing socket_id or channel_name'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grant_ctx, booking, room, result = _resolve_from_request(
            self, request, hotel_slug,
        )
        if isinstance(result, Response):
            return result
        conversation = result

        try:
            expected_channel = (
                f"private-hotel-{hotel_slug}"
                f"-guest-chat-booking-{booking.booking_id}"
            )
            if channel_name != expected_channel:
                logger.warning(
                    "Pusher auth rejected: expected=%s "
                    "requested=%s booking=%s",
                    expected_channel,
                    channel_name,
                    booking.booking_id,
                )
                return Response(
                    {
                        'error': 'Channel does not match booking',
                        'code': 'CHANNEL_MISMATCH',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            channel_data = {
                "user_id": f"guest-{booking.booking_id}",
                "user_info": {
                    "type": "guest",
                    "booking_id": booking.booking_id,
                    "hotel_slug": hotel_slug,
                    "room_number": (
                        room.room_number if room else None
                    ),
                    "guest_name": booking.primary_guest_name,
                },
            }

            auth_response = self._generate_pusher_auth(
                socket_id, channel_name, channel_data,
            )

            logger.info(
                "Pusher auth ok: booking=%s channel=%s",
                booking.booking_id, channel_name,
            )

            return Response(auth_response)

        except Exception as e:
            logger.error(f"Pusher auth error: {e}")
            return Response(
                {'error': 'Unable to authenticate channel'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _generate_pusher_auth(
        self, socket_id, channel_name, channel_data=None,
    ):
        if channel_data:
            channel_data_str = json.dumps(channel_data)
            string_to_sign = (
                f"{socket_id}:{channel_name}:{channel_data_str}"
            )
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
