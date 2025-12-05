from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from rooms.models import Room
from hotel.models import Hotel
from staff.models import Staff
from .models import Conversation, RoomMessage, GuestChatSession
from .serializers import ConversationSerializer, RoomMessageSerializer
from .utils import pusher_client
from notifications.fcm_service import send_fcm_notification
from notifications.notification_manager import notification_manager
import json
from django.core.serializers.json import DjangoJSONEncoder
import logging

logger = logging.getLogger(__name__)

# Fetch all conversations (rooms with messages) for a hotel
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_conversations(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    conversations = Conversation.objects.filter(
        room__hotel=hotel
    ).select_related('room').prefetch_related('room__guests', 'messages').order_by('-updated_at')

    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


# Fetch all messages for a conversation
@api_view(['GET'])
@permission_classes([AllowAny])
def get_conversation_messages(request, hotel_slug, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if conversation.room.hotel.slug != hotel_slug:
        return Response({"error": "Conversation does not belong to this hotel"}, status=400)

    limit = int(request.GET.get("limit", 10))  # load 20 messages at a time
    before_id = request.GET.get("before_id")  # load messages older than this

    messages_qs = conversation.messages.order_by('-timestamp')  # newest first

    if before_id:
        messages_qs = messages_qs.filter(id__lt=before_id)

    messages = messages_qs[:limit][::-1]  # reverse to show oldest at top
    
    # Optimize: prefetch reply_to messages
    messages = list(messages)  # Evaluate queryset
    serializer = RoomMessageSerializer(messages, many=True)
    return Response(serializer.data)


# Send (or start) a conversation message
@api_view(['POST'])
@permission_classes([AllowAny])
def send_conversation_message(request, hotel_slug, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    room = conversation.room
    hotel = room.hotel

    # Validate message text
    message_text = request.data.get("message", "").strip()
    if not message_text:
        logger.warning("Empty message attempted to send")
        return Response({"error": "Message cannot be empty"}, status=400)

    # Get reply_to field (if this is a reply)
    reply_to_id = request.data.get("reply_to")
    reply_to_message = None
    
    if reply_to_id:
        try:
            reply_to_message = RoomMessage.objects.get(
                id=reply_to_id,
                conversation=conversation
            )
            logger.info(f"Message is replying to message ID: {reply_to_id}")
        except RoomMessage.DoesNotExist:
            logger.warning(f"Reply target message {reply_to_id} not found")
            # Continue without reply - don't fail the whole request

    # Determine sender
    staff_instance = getattr(request.user, "staff_profile", None)
    sender_type = "staff" if staff_instance else "guest"
    
    logger.info(
        f"🔵 NEW MESSAGE | Type: {sender_type} | "
        f"Hotel: {hotel.slug} | Room: {room.room_number} | "
        f"Conversation: {conversation.id} | "
        f"Reply to: {reply_to_id if reply_to_id else 'None'}"
    )

    # Create the message
    message = RoomMessage.objects.create(
        conversation=conversation,
        room=room,
        staff=staff_instance if staff_instance else None,
        message=message_text,
        sender_type=sender_type,
        reply_to=reply_to_message,
    )
    
    # DEBUG: Log what was saved
    logger.info(
        f"📝 Message saved to DB | ID: {message.id} | "
        f"reply_to ID: {message.reply_to_id} | "
        f"reply_to object: {message.reply_to}"
    )

    # Update session handler when staff replies
    # This supports conversation handoff - any staff who sends a message
    # becomes the current handler
    if sender_type == "staff":
        # Check if staff handler is changing before updating
        active_sessions = GuestChatSession.objects.filter(
            conversation=conversation,
            is_active=True
        )
        
        # Get current handler (if any)
        current_handler = None
        if active_sessions.exists():
            current_handler = active_sessions.first().current_staff_handler
        
        # Only update and notify if staff handler is changing
        staff_changed = current_handler != staff_instance
        
        if staff_changed:
            sessions_updated = active_sessions.update(
                current_staff_handler=staff_instance
            )
            
            logger.info(
                f"Staff handler changed from {current_handler} to {staff_instance} "
                f"for conversation {conversation.id}. Updated {sessions_updated} session(s)"
            )
            
            # Notify guest that a NEW staff member is now handling their chat
            guest_channel = f"{hotel.slug}-room-{room.room_number}-chat"
            try:
                pusher_client.trigger(
                    guest_channel,
                    "staff-assigned",
                    {
                        "staff_name": f"{staff_instance.first_name} {staff_instance.last_name}".strip(),
                        "staff_role": staff_instance.role.name if staff_instance.role else "Staff",
                        "conversation_id": conversation.id
                    }
                )
                logger.info(
                    f"Pusher triggered: staff-assigned event for "
                    f"{staff_instance} on channel {guest_channel}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to trigger Pusher for staff-assigned: {e}"
                )
        else:
            logger.debug(
                f"Staff handler unchanged ({staff_instance}), "
                f"skipping staff-assigned event for conversation {conversation.id}"
            )

    serializer = RoomMessageSerializer(message)
    logger.info(f"Message created with ID: {message.id}")
    
    # Convert serializer data to JSON-safe format (handles datetime objects)
    message_data = json.loads(
        json.dumps(serializer.data, cls=DjangoJSONEncoder)
    )
    
    # DEBUG: Log serialized data
    logger.info(
        f"📤 Serialized data | "
        f"reply_to: {message_data.get('reply_to')} | "
        f"reply_to_message: {message_data.get('reply_to_message')}"
    )

    # Trigger message-delivered event using NotificationManager
    try:
        # Use guest chat message created for delivered status updates
        notification_manager.realtime_guest_chat_message_created(message)
        logger.info(
            f"NotificationManager triggered for message delivered: "
            f"message_id={message.id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to trigger NotificationManager for message-delivered: {e}"
        )

    # Update conversation unread status if guest sends a message
    if sender_type == "guest":
        if not conversation.has_unread:
            conversation.has_unread = True
            conversation.save()
            logger.info(f"Conversation {conversation.id} marked as unread")

        # CRITICAL: Send message back to guest's channel so they see it!
        guest_channel = f"{hotel.slug}-room-{room.room_number}-chat"
        try:
            pusher_client.trigger(
                guest_channel,
                "new-message",
                message_data
            )
            logger.info(
                f"✅ Pusher sent to GUEST channel: {guest_channel}, "
                f"message_id={message.id}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to send Pusher to guest channel "
                f"{guest_channel}: {e}"
            )

        # Trigger unread update using NotificationManager
        try:
            notification_manager.realtime_guest_chat_unread_updated(room, 1)  # Assume 1 new unread
            logger.info(f"NotificationManager triggered unread update for room {room.room_number}")
        except Exception as e:
            logger.error(f"NotificationManager failed for unread update: {e}")
            
            # NotificationManager handles unread updates via realtime_guest_chat_unread_updated
            # No fallback needed - unified architecture manages this automatically
            logger.info(f"Unread count update handled by NotificationManager for room {room.room_number}")

        # Prefer Receptionists, fallback to Front Office
        reception_staff = Staff.objects.filter(
            hotel=hotel,
            role__slug="receptionist"
        )

        print(f"🔍 Looking for staff to notify. Reception staff count: {reception_staff.count()}")

        if reception_staff.exists():
            target_staff = reception_staff
            print(f"✅ Targeting reception staff: {reception_staff.count()}")
            logger.info(f"Targeting reception staff for notifications: count={reception_staff.count()}")
        else:
            target_staff = Staff.objects.filter(
                hotel=hotel,
                department__slug="front-office"
            )
            print(f"⚠️ No reception staff. Targeting front-office: {target_staff.count()}")
            logger.info(f"No reception staff found. Targeting front-office staff: count={target_staff.count()}")

        print(f"📬 Using NotificationManager for guest message to {target_staff.count()} staff members")
        
        # Use NotificationManager for unified guest chat event
        try:
            # Set assigned_staff for FCM notification targeting
            if target_staff.exists():
                message.assigned_staff = target_staff.first()  # Use first staff for FCM
            
            notification_manager.realtime_guest_chat_message_created(message)
            print(f"✅ NotificationManager sent guest chat event for message {message.id}")
            logger.info(f"NotificationManager triggered realtime_guest_chat_message_created: message_id={message.id}")
        except Exception as e:
            print(f"❌ NotificationManager FAILED: {e}")
            logger.error(f"Failed to trigger NotificationManager for guest message: {e}")
            
            # Log NotificationManager failure - unified architecture handles staff notifications
            logger.error(f"NotificationManager failed for guest message - unified realtime architecture should handle staff notifications automatically")
            
        # FCM notifications are now handled by NotificationManager in realtime_guest_chat_message_created
        print(f"📱 FCM notifications handled by NotificationManager for {target_staff.count()} staff members")

    else:
        # Staff sent a message - use NotificationManager for unified handling
        try:
            notification_manager.realtime_guest_chat_message_created(message)
            logger.info(
                f"NotificationManager triggered for staff message: "
                f"message_id={message.id}, room={room.room_number}"
            )
        except Exception as e:
            logger.error(
                f"NotificationManager failed for staff message {message.id}: {e}"
            )
            
            # Log NotificationManager failure - no fallback needed for unified architecture
            logger.error(f"NotificationManager failed for staff message - unified realtime architecture expects this method to work")

    # NotificationManager already handles the new message event in realtime_guest_chat_message_created
    # No additional Pusher call needed - unified architecture provides this automatically
    logger.info(
        f"Message handling completed via NotificationManager: "
        f"message_id={message.id}, room={room.room_number}"
    )

    # Prepare response with staff info
    response_data = {
        "conversation_id": conversation.id,
        "message": message_data
    }
    
    # Add conversation_id to message_data for consistency
    message_data["conversation_id"] = conversation.id

    if sender_type == "staff":
        response_data["staff_info"] = get_staff_info(staff_instance)

    logger.info(
        f"✅ MESSAGE COMPLETE | ID: {message.id} | "
        f"Type: {sender_type} | "
        f"Guest Channel: {hotel.slug}-room-{room.room_number}-chat | "
        f"FCM Sent: {bool(room.guest_fcm_token if sender_type == 'staff' else None)}"
    )

    return Response(response_data)

# Keep validation unchanged
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_chat_pin(request, hotel_slug, room_number):
    """
    Validates the PIN for accessing a chat room.
    Also saves guest FCM token if provided.
    Returns complete session data for the frontend.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    
    pin = request.data.get('pin')
    fcm_token = request.data.get('fcm_token')  # Optional FCM token
    
    if pin == room.guest_id_pin:
        # Save FCM token if provided
        if fcm_token:
            room.guest_fcm_token = fcm_token
            room.save()
            logger.info(
                f"FCM token saved for room {room_number} "
                f"during chat PIN validation at {hotel.name}"
            )
        
        # Get or create conversation for this room
        conversation, created = Conversation.objects.get_or_create(room=room)
        
        # Get or create guest session (conversation is required)
        guest_session, session_created = GuestChatSession.objects.get_or_create(
            room=room,
            defaults={
                'conversation': conversation,
                'is_active': True
            }
        )
        
        if not guest_session.is_active:
            guest_session.is_active = True
            guest_session.save()
        
        print(f"✅ Guest PIN validated for room {room_number}, session ID: {guest_session.id}")
        
        return Response({
            'valid': True,
            'fcm_token_saved': bool(fcm_token),
            'session_data': {
                'session_id': str(guest_session.id),
                'room_number': room.room_number,
                'hotel_slug': hotel.slug,
                'conversation_id': str(conversation.id),
                'pusher_channel': f"{hotel.slug}-room-{room.room_number}-chat"
            }
        })
    
    return Response({'valid': False}, status=401)


# Get or create a conversation for a room (first message)
@api_view(['POST'])
@permission_classes([AllowAny])
def get_or_create_conversation_from_room(request, hotel_slug, room_number):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)

    conversation, created = Conversation.objects.get_or_create(room=room)
    messages = RoomMessage.objects.filter(conversation=conversation).order_by('timestamp')
    serializer = RoomMessageSerializer(messages, many=True)

    if created:
        # New conversation events are handled by NotificationManager when messages are created
        # The realtime_guest_chat_message_created method includes conversation context
        logger.info(f"New conversation created: {conversation.id} for room {room.room_number}")

    return Response({
        "conversation_id": conversation.id,
        "messages": serializer.data,
        "conversation_created": created
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_rooms(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    conversations = Conversation.objects.filter(room__hotel=hotel).select_related('room').prefetch_related('room__guests', 'messages').order_by('-updated_at')
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_unread_count(request, hotel_slug):
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response({"unread_counts": {}})

    hotel = get_object_or_404(Hotel, slug=hotel_slug)

    # Annotate counts of unread guest messages per room
    unread_counts = (
        RoomMessage.objects
        .filter(
            room__hotel=hotel,
            read_by_staff=False,
            sender_type="guest"
        )
        .values("room_id")
        .annotate(unread_count=Count("id"))
    )

    # Convert into dict {room_id: count}
    counts_dict = {item["room_id"]: item["unread_count"] for item in unread_counts}

    return Response({"unread_counts": counts_dict})

@api_view(['POST'])
@permission_classes([AllowAny])
def mark_conversation_read(request, conversation_id):
    """Mark messages as read with detailed tracking for staff and guests"""
    staff = getattr(request.user, "staff_profile", None)
    is_staff = staff is not None
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    room = conversation.room
    hotel = room.hotel

    if is_staff:
        # Staff reading guest messages
        messages_to_update = conversation.messages.filter(
            sender_type="guest",
            read_by_staff=False
        )
        message_ids = list(messages_to_update.values_list('id', flat=True))
        
        updated_count = messages_to_update.update(
            read_by_staff=True,
            staff_read_at=timezone.now(),
            status='read'
        )
        
        # Trigger Pusher for guest to show read receipt
        # Send to CONVERSATION channel (both guest and staff can listen)
        if message_ids:
            conversation_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
            try:
                pusher_client.trigger(
                    conversation_channel,
                    "messages-read-by-staff",
                    {
                        "message_ids": message_ids,
                        "read_at": timezone.now().isoformat(),
                        "staff_name": str(staff),
                        "conversation_id": conversation.id
                    }
                )
                logger.info(
                    f"📡 Pusher triggered: messages-read-by-staff to "
                    f"conversation channel {conversation_channel}, "
                    f"message_ids={message_ids}, count={len(message_ids)}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to trigger Pusher for "
                    f"messages-read-by-staff: {e}"
                )
        
        # Clear conversation unread flag
        if conversation.has_unread:
            conversation.has_unread = False
            conversation.save()

            # Update unread count via NotificationManager
            try:
                notification_manager.realtime_guest_chat_unread_updated(room, 0)  # 0 unread after reading
                logger.info(f"Unread count reset for conversation {conversation.id}")
            except Exception as e:
                logger.error(f"Failed to update unread count via NotificationManager: {e}")
    
    else:
        # Guest reading staff messages
        messages_to_update = conversation.messages.filter(
            sender_type="staff",
            read_by_guest=False
        )
        message_ids = list(messages_to_update.values_list('id', flat=True))
        
        updated_count = messages_to_update.update(
            read_by_guest=True,
            guest_read_at=timezone.now(),
            status='read'
        )
        
        # Trigger Pusher for staff to show read receipt
        if message_ids:
            message_channel = (
                f"{hotel.slug}-conversation-{conversation.id}-chat"
            )
            try:
                pusher_client.trigger(
                    message_channel,
                    "messages-read-by-guest",
                    {
                        "message_ids": message_ids,
                        "read_at": timezone.now().isoformat(),
                        "room_number": room.room_number
                    }
                )
                logger.info(
                    f"Pusher triggered: messages-read-by-guest, "
                    f"count={len(message_ids)}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to trigger Pusher for "
                    f"messages-read-by-guest: {e}"
                )

    return Response({
        "conversation_id": conversation.id,
        "marked_as_read": updated_count
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_unread_conversation_count(request, hotel_slug):
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response({"unread_count": 0, "rooms": []})

    hotel = get_object_or_404(Hotel, slug=hotel_slug)

    # Count distinct conversations flagged as having unread
    unread_count = (
        Conversation.objects
        .filter(room__hotel=hotel, has_unread=True)
        .count()
    )
    print(f"[DEBUG] Unread conversation count for hotel '{hotel_slug}': {unread_count}")

    # Collect all conversations with has_unread=True and include their unread messages
    rooms_with_unread = []
    conversations = (
        Conversation.objects
        .filter(room__hotel=hotel, has_unread=True)
        .select_related("room")
        .prefetch_related("messages")
    )

    for convo in conversations:
        unread_messages = convo.messages.filter(
            sender_type="guest",
            read_by_staff=False  # still need this at message level to fetch actual unread texts
        )
        rooms_with_unread.append({
            "room_id": convo.room.id,
            "room_number": convo.room.room_number,
            "conversation_id": convo.id,
            "unread_count": unread_messages.count(),
            "unread_messages": [
                {
                    "id": msg.id,
                    "message": msg.message,
                    "timestamp": msg.timestamp,
                }
                for msg in unread_messages
            ]
        })

    return Response({
        "unread_count": unread_count,
        "rooms": rooms_with_unread
    })


# Helper functions for guest sessions
def get_staff_info(staff):
    """Format staff info for guest display"""
    if not staff:
        return None
    return {
        'name': f"{staff.first_name} {staff.last_name}".strip(),
        'role': staff.role.name if staff.role else 'Staff',
        'profile_image': (staff.profile_image.url
                          if staff.profile_image else None)
    }


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])
def initialize_guest_session(request, hotel_slug, room_number):
    """
    Create or retrieve a guest chat session.
    Returns session token for local storage.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)

    # Validate PIN first
    pin = request.data.get('pin')
    if pin != room.guest_id_pin:
        return Response({'error': 'Invalid PIN'}, status=401)

    # Get or create conversation
    conversation, _ = Conversation.objects.get_or_create(room=room)

    # Check if session token provided (returning guest)
    existing_token = request.data.get('session_token')

    if existing_token:
        try:
            session = GuestChatSession.objects.get(
                session_token=existing_token,
                room=room,
                is_active=True
            )
            if not session.is_expired():
                # Refresh activity
                session.last_activity = timezone.now()
                session.save()

                logger.info(
                    f"Existing guest session refreshed: "
                    f"{session.session_token} for room {room_number}"
                )

                return Response({
                    'session_token': str(session.session_token),
                    'conversation_id': conversation.id,
                    'room_number': room.room_number,
                    'is_new_session': False,
                    'pusher_channel': (
                        f"{hotel.slug}-room-{room.room_number}-chat"
                    ),
                    'current_staff_handler': get_staff_info(
                        session.current_staff_handler
                    )
                })
        except GuestChatSession.DoesNotExist:
            pass

    # Create new session
    session = GuestChatSession.objects.create(
        conversation=conversation,
        room=room,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        last_ip=get_client_ip(request),
        expires_at=timezone.now() + timedelta(days=7)
    )

    logger.info(
        f"New guest session created: {session.session_token} "
        f"for room {room_number}"
    )

    return Response({
        'session_token': str(session.session_token),
        'conversation_id': conversation.id,
        'room_number': room.room_number,
        'is_new_session': True,
        'pusher_channel': f"{hotel.slug}-room-{room.room_number}-chat",
        'current_staff_handler': None
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def validate_guest_session(request, session_token):
    """
    Validate if guest session is still active.
    Called on page load to verify local storage token.
    """
    try:
        session = GuestChatSession.objects.get(
            session_token=session_token,
            is_active=True
        )

        if session.is_expired():
            session.is_active = False
            session.save()
            logger.info(f"Guest session expired: {session_token}")
            return Response(
                {'valid': False, 'reason': 'expired'},
                status=401
            )

        # Update activity
        session.last_activity = timezone.now()
        session.save()

        return Response({
            'valid': True,
            'conversation_id': session.conversation.id,
            'room_number': session.room.room_number,
            'hotel_slug': session.room.hotel.slug,
            'current_staff_handler': get_staff_info(
                session.current_staff_handler
            ),
            'pusher_channel': (
                f"{session.room.hotel.slug}-room-"
                f"{session.room.room_number}-chat"
            )
        })

    except GuestChatSession.DoesNotExist:
        return Response(
            {'valid': False, 'reason': 'not_found'},
            status=404
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_unread_messages_for_guest(request, session_token):
    """
    Get count of unread messages for a guest session.
    Used for browser notifications.
    """
    try:
        session = GuestChatSession.objects.get(
            session_token=session_token,
            is_active=True
        )

        if session.is_expired():
            return Response({'unread_count': 0})

        unread_count = session.conversation.messages.filter(
            sender_type='staff',
            read_by_guest=False
        ).count()

        # Get latest unread message for preview
        latest_unread = session.conversation.messages.filter(
            sender_type='staff',
            read_by_guest=False
        ).order_by('-timestamp').first()

        return Response({
            'unread_count': unread_count,
            'latest_message': {
                'text': (latest_unread.message[:50]
                         if latest_unread else None),
                'staff_name': (latest_unread.staff_display_name
                               if latest_unread else None),
                'timestamp': (latest_unread.timestamp
                              if latest_unread else None)
            } if latest_unread else None
        })

    except GuestChatSession.DoesNotExist:
        return Response({'unread_count': 0})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_staff_to_conversation(request, hotel_slug, conversation_id):
    """
    Assign the authenticated staff member as the current handler when they
    open/click on a conversation. Supports conversation handoff between
    multiple staff members (e.g., shift changes, coverage).
    
    This allows any staff member to take over a conversation at any time,
    and the guest will see the new staff member's name in their chat window.
    """
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response(
            {"error": "Not authenticated as staff"},
            status=403
        )
    
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify conversation belongs to this hotel
    if conversation.room.hotel != hotel:
        return Response(
            {"error": "Conversation does not belong to this hotel"},
            status=400
        )
    
    # Check current staff handler before updating
    sessions = GuestChatSession.objects.filter(
        conversation=conversation,
        is_active=True
    )
    
    # Get current handler (if any)
    current_handler = None
    if sessions.exists():
        current_handler = sessions.first().current_staff_handler
    
    # Only update and notify if staff handler is changing
    staff_changed = current_handler != staff
    
    if staff_changed:
        updated_count = sessions.update(current_staff_handler=staff)
        
        logger.info(
            f"Staff handler changed from {current_handler} to {staff} "
            f"for conversation {conversation_id}. "
            f"Updated {updated_count} guest session(s)"
        )
        
        # Notify guest that a NEW staff member is now handling their chat
        room = conversation.room
        guest_channel = f"{hotel.slug}-room-{room.room_number}-chat"
        
        try:
            pusher_client.trigger(
                guest_channel,
                "staff-assigned",
                {
                    "staff_name": (
                        f"{staff.first_name} {staff.last_name}".strip()
                    ),
                    "staff_role": (
                        staff.role.name if staff.role else "Staff"
                    ),
                    "conversation_id": conversation.id
                }
            )
            logger.info(
                f"Pusher triggered: staff-assigned event sent to guest "
                f"on channel {guest_channel}"
            )
        except Exception as e:
            logger.error(
                f"Failed to trigger Pusher for staff-assigned: {e}"
            )
    else:
        logger.info(
            f"Staff {staff} already assigned to conversation "
            f"{conversation_id}, skipping staff-assigned event"
        )
        updated_count = 0
    
    # IMPORTANT: Mark all unread guest messages as read when staff opens conversation
    room = conversation.room
    messages_to_mark_read = conversation.messages.filter(
        sender_type="guest",
        read_by_staff=False
    )
    message_ids = list(messages_to_mark_read.values_list('id', flat=True))
    
    print(f"👁️ Staff {staff.id} opened conversation {conversation_id}")
    print(f"👁️ Found {len(message_ids)} unread guest messages: {message_ids}")
    
    if message_ids:
        # Mark messages as read
        read_count = messages_to_mark_read.update(
            read_by_staff=True,
            staff_read_at=timezone.now(),
            status='read'
        )
        
        print(f"✅ Marked {read_count} messages as read_by_staff=True")
        
        # Clear conversation unread flag
        if conversation.has_unread:
            conversation.has_unread = False
            conversation.save()
            print(f"✅ Cleared conversation unread flag")
        
        # Send Pusher event to CONVERSATION channel (both guest and staff listen)
        conversation_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
        print(f"📡 Sending messages-read-by-staff to: {conversation_channel}")
        print(f"📡 Event payload: message_ids={message_ids}")
        
        try:
            pusher_client.trigger(
                conversation_channel,
                "messages-read-by-staff",
                {
                    "message_ids": message_ids,
                    "read_at": timezone.now().isoformat(),
                    "staff_name": str(staff),
                    "conversation_id": conversation.id
                }
            )
            print("✅ Successfully sent messages-read-by-staff event")
            logger.info(
                f"📡 Staff opened conversation: marked {read_count} messages as read, "
                f"sent to conversation channel {conversation_channel}, message_ids={message_ids}"
            )
        except Exception as e:
            print(f"❌ FAILED to send messages-read-by-staff event: {e}")
            logger.error(
                f"Failed to send messages-read-by-staff event: {e}"
            )
    else:
        print(f"ℹ️ No unread guest messages to mark as read")
    
    return Response({
        "conversation_id": conversation.id,
        "assigned_staff": get_staff_info(staff),
        "sessions_updated": updated_count,
        "room_number": room.room_number,
        "messages_marked_read": len(message_ids)
    })


# ==================== MESSAGE CRUD OPERATIONS ====================

@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_message(request, message_id):
    """
    Update/edit a message. Only the sender can edit their own messages.
    Staff can edit their messages, guests can edit their messages.
    """
    message = get_object_or_404(RoomMessage, id=message_id)
    
    # Check permissions
    staff = getattr(request.user, "staff_profile", None)
    is_staff = staff is not None
    
    # Staff can only edit their own messages
    if is_staff and message.sender_type == "staff":
        if message.staff != staff:
            return Response(
                {"error": "You can only edit your own messages"},
                status=403
            )
    # Guest messages can only be edited if sender is guest
    elif not is_staff and message.sender_type == "guest":
        # For guests, we allow editing if they're in the same room
        # (more permissive since guests don't have accounts)
        pass
    else:
        return Response(
            {"error": "You don't have permission to edit this message"},
            status=403
        )
    
    # Check if message is already deleted
    if message.is_deleted:
        return Response(
            {"error": "Cannot edit a deleted message"},
            status=400
        )
    
    # Update message
    new_text = request.data.get('message', '').strip()
    if not new_text:
        return Response(
            {"error": "Message cannot be empty"},
            status=400
        )
    
    message.message = new_text
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save()
    
    logger.info(
        f"Message {message_id} edited by "
        f"{'staff ' + str(staff) if is_staff else 'guest'}"
    )
    
    # Trigger Pusher for real-time update
    from .serializers import RoomMessageSerializer
    serializer = RoomMessageSerializer(message)
    
    hotel = message.room.hotel
    message_channel = (
        f"{hotel.slug}-conversation-{message.conversation.id}-chat"
    )
    
    try:
        pusher_client.trigger(
            message_channel,
            "message-updated",
            serializer.data
        )
        logger.info(f"Pusher triggered: message-updated for message {message_id}")
    except Exception as e:
        logger.error(f"Failed to trigger Pusher for message-updated: {e}")
    
    return Response({
        "message": serializer.data,
        "success": True
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_message(request, message_id):
    """
    Soft delete a message. Only the sender can delete their own messages.
    Hard delete is available for staff with admin permissions.
    """
    message = get_object_or_404(RoomMessage, id=message_id)
    
    # Check permissions
    staff = getattr(request.user, "staff_profile", None)
    is_staff = staff is not None
    hard_delete = request.query_params.get('hard_delete') == 'true'
    
    # Debug logging
    print("=" * 80)
    print("🔍 DELETE PERMISSION CHECK")
    print(f"   User: {request.user}")
    print(f"   Is authenticated: {request.user.is_authenticated}")
    print(f"   Staff profile: {staff}")
    print(f"   is_staff: {is_staff}")
    print(f"   Message sender_type: {message.sender_type}")
    print(f"   Message ID: {message_id}")
    print("=" * 80)
    
    # Permission logic:
    # 1. Staff can delete their own staff messages
    # 2. Staff can delete ANY guest messages (moderation)
    # 3. Guest (anonymous) can delete their own guest messages
    # 4. Guest CANNOT delete staff messages
    
    if is_staff:
        # Staff user (authenticated)
        if message.sender_type == "staff":
            # Staff deleting a staff message - must be their own
            if message.staff != staff:
                # Check if staff has admin/manager role for hard delete
                if hard_delete and not (
                    staff.role and staff.role.slug in ['manager', 'admin']
                ):
                    return Response(
                        {"error": "Only managers can hard delete other staff messages"},
                        status=403
                    )
                elif not hard_delete:
                    return Response(
                        {"error": "You can only delete your own messages"},
                        status=403
                    )
        # else: Staff deleting guest message - ALLOWED (moderation)
    else:
        # Guest user (anonymous via QR/PIN)
        if message.sender_type == "staff":
            # Guest cannot delete staff messages
            return Response(
                {"error": "Guests cannot delete staff messages"},
                status=403
            )
        
        # Guest deleting guest message - verify they have access to this room
        # Guests can delete ANY guest message in their room (since they're anonymous)
        # We verify room access by checking the message is in their conversation
        print(f"✅ Guest deleting guest message in room {message.room.room_number}")
    
    hotel = message.room.hotel
    room = message.room
    conversation = message.conversation
    room_number = room.room_number
    hotel_slug = hotel.slug
    
    # Prepare Pusher channels
    message_channel = f"{hotel_slug}-conversation-{conversation.id}-chat"
    guest_channel = f"{hotel_slug}-room-{room_number}-chat"
    # NEW: Dedicated deletion channel for clearer event handling
    deletion_channel = f"{hotel_slug}-room-{room_number}-deletions"
    
    print(f"🗑️ DELETE REQUEST | message_id={message_id} | hotel={hotel_slug} | room={room_number}")
    print(f"🗑️ CHANNELS | conversation={message_channel} | guest={guest_channel}")
    print(f"🗑️ DELETION CHANNEL | {deletion_channel}")
    print(f"🗑️ SENDER | type={message.sender_type} | is_staff={is_staff} | hard_delete={hard_delete}")
    
    if hard_delete and is_staff:
        # Hard delete (only for admin staff)
        message_id_copy = message.id
        original_sender_type = message.sender_type
        
        # Get attachment IDs before deleting message
        attachment_ids = list(message.attachments.values_list('id', flat=True))
        
        pusher_data = {
            "message_id": message_id_copy,
            "hard_delete": True,
            "soft_delete": False,  # Inverse of hard_delete for frontend
            "attachment_ids": attachment_ids,
            "deleted_by": "staff",  # Who performed the deletion
            "original_sender": original_sender_type,  # Who sent the message
            "staff_id": staff.id if staff else None,
            "staff_name": f"{staff.first_name} {staff.last_name}".strip() if staff else None,
            "timestamp": timezone.now().isoformat()
        }
        
        print("=" * 80)
        print("🗑️ HARD DELETE INITIATED")
        print(f"Message ID: {message_id_copy}")
        print(f"Original Sender: {original_sender_type}")
        print(f"Deleted By: staff ({staff})")
        print(f"Attachments: {attachment_ids}")
        print(f"Pusher Data: {pusher_data}")
        print("=" * 80)
        
        message.delete()
        
        logger.info(
            f"Message {message_id_copy} hard deleted by staff {staff}"
        )
        
        # Trigger Pusher to multiple channels
        try:
            # 1. Conversation channel (for all participants)
            pusher_client.trigger(
                message_channel,
                "message-deleted",
                pusher_data
            )
            logger.info(f"✅ Pusher: message-deleted → {message_channel}")
            
            # Also emit a secondary event name for clients that listen for
            # a different event (some frontends expect "message-removed")
            try:
                pusher_client.trigger(
                    message_channel,
                    "message-removed",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-removed → {message_channel}")
            except Exception as e:
                logger.debug(f"Optional secondary trigger failed for {message_channel}: {e}")

            # 2. Room channel for guest (existing channel, for compatibility)
            room_channel = f'{hotel_slug}-room-{room_number}-chat'
            print("\n" + "=" * 80)
            print("📡 BROADCASTING TO ROOM CHANNEL")
            print(f"   Channel: {room_channel}")
            print(f"   Payload: {pusher_data}")
            print("   Event 1: message-deleted")
            print("   Event 2: message-removed")
            print("=" * 80)
            
            try:
                result = pusher_client.trigger(
                    room_channel,
                    'message-deleted',
                    pusher_data
                )
                print(f"✅ SENT message-deleted to {room_channel}")
                print(f"   Pusher response: {result}")
                logger.info(f"Pusher: message-deleted sent to {room_channel}")
            except Exception as e:
                print(f"❌ FAILED to send message-deleted: {e}")
                logger.error(f"Failed to trigger message-deleted: {e}")
            
            # Also broadcast 'message-removed' alias
            try:
                result = pusher_client.trigger(
                    room_channel,
                    'message-removed',
                    pusher_data
                )
                print(f"✅ SENT message-removed to {room_channel}")
                print(f"   Pusher response: {result}")
                logger.info(f"Pusher: message-removed sent to {room_channel}")
            except Exception as e:
                print(f"❌ FAILED to send message-removed: {e}")
                logger.error(f"Failed to trigger message-removed: {e}")
            
            print("=" * 80 + "\n")
            
            # 2B. NEW DEDICATED DELETION CHANNEL
            # Separate channel for deletion events for clearer handling
            print("=" * 80)
            print("🗑️ BROADCASTING TO DEDICATED DELETION CHANNEL")
            print(f"   Channel: {deletion_channel}")
            print(f"   Payload: {pusher_data}")
            print("=" * 80)
            
            try:
                result = pusher_client.trigger(
                    deletion_channel,
                    'content-deleted',
                    pusher_data
                )
                print(f"✅ SENT content-deleted to {deletion_channel}")
                print(f"   Pusher response: {result}")
                logger.info(
                    f"Pusher: content-deleted sent to {deletion_channel}"
                )
            except Exception as e:
                print(f"❌ FAILED to send to deletion channel: {e}")
                logger.error(
                    f"Failed to trigger content-deleted on "
                    f"{deletion_channel}: {e}"
                )
            
            print("=" * 80 + "\n")

            # 3. Guest channel (so guest sees deletion) - kept for compatibility
            pusher_client.trigger(
                guest_channel,
                "message-deleted",
                pusher_data
            )
            logger.info(f"✅ Pusher: message-deleted → {guest_channel}")

            # Secondary event for guest channel as well
            try:
                pusher_client.trigger(
                    guest_channel,
                    "message-removed",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-removed → {guest_channel}")
            except Exception as e:
                logger.debug(f"Optional secondary trigger failed for {guest_channel}: {e}")
            
            # 3. Individual staff channels (so all staff see deletion)
            for staff_member in conversation.participants_staff.all():
                staff_channel = f"{hotel.slug}-staff-{staff_member.id}-chat"
                pusher_client.trigger(
                    staff_channel,
                    "message-deleted",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-deleted → {staff_channel}")
                try:
                    pusher_client.trigger(
                        staff_channel,
                        "message-removed",
                        pusher_data
                    )
                    logger.info(f"✅ Pusher: message-removed → {staff_channel}")
                except Exception as e:
                    logger.debug(f"Optional secondary trigger failed for {staff_channel}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to trigger Pusher for message-deleted: {e}")
        
        return Response({
            "success": True,
            "hard_delete": True,
            "message_id": message_id_copy
        })
    else:
        # Soft delete
        original_sender_type = message.sender_type
        message.soft_delete()
        
        deleter_type = "staff" if is_staff else "guest"
        logger.info(
            f"Message {message_id} soft deleted by "
            f"{deleter_type} ({staff if is_staff else 'anonymous guest'})"
        )
        
        from .serializers import RoomMessageSerializer
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        serializer = RoomMessageSerializer(message)
        
        # Get attachment IDs for UI update
        attachment_ids = list(message.attachments.values_list('id', flat=True))
        
        # Convert serializer.data to ensure datetime objects are strings
        message_data = json.loads(
            json.dumps(serializer.data, cls=DjangoJSONEncoder)
        )
        
        pusher_data = {
            "message_id": message.id,
            "hard_delete": False,
            "soft_delete": True,  # Inverse of hard_delete for frontend
            "message": message_data,
            "attachment_ids": attachment_ids,
            "deleted_by": deleter_type,  # Who performed the deletion
            "original_sender": original_sender_type,  # Who sent the message
            "staff_id": staff.id if is_staff else None,
            "staff_name": (
                f"{staff.first_name} {staff.last_name}".strip()
                if is_staff and staff else None
            ),
            "timestamp": timezone.now().isoformat()
        }
        
        try:
            # 1. Conversation channel (for all participants)
            pusher_client.trigger(
                message_channel,
                "message-deleted",
                pusher_data
            )
            logger.info(f"✅ Pusher: message-deleted → {message_channel}")

            # Also emit secondary "message-removed" event for compatibility
            try:
                pusher_client.trigger(
                    message_channel,
                    "message-removed",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-removed → {message_channel}")
            except Exception as e:
                logger.debug(f"Optional secondary trigger failed for {message_channel}: {e}")
            
            # 2. Room channel for guest (existing channel, for compatibility)
            room_channel = f'{hotel_slug}-room-{room_number}-chat'
            print(f"📡 [SOFT DELETE] BROADCASTING TO ROOM: "
                  f"{room_channel}")
            print(f"📦 [SOFT DELETE] PAYLOAD: {pusher_data}")
            
            pusher_client.trigger(
                room_channel,
                'message-deleted',
                pusher_data
            )
            print(f"✅ [SOFT DELETE] SENT message-deleted to "
                  f"{room_channel}")
            logger.info(
                f"✅ Pusher: message-deleted → "
                f"{hotel_slug}-room-{room_number}-chat"
            )
            
            # Also broadcast 'message-removed' alias
            pusher_client.trigger(
                room_channel,
                'message-removed',
                pusher_data
            )
            print(f"✅ [SOFT DELETE] SENT message-removed to "
                  f"{room_channel}")
            logger.info(
                f"✅ Pusher: message-removed → "
                f"{hotel_slug}-room-{room_number}-chat"
            )
            
            # 2B. NEW DEDICATED DELETION CHANNEL
            # Separate channel for deletion events for clearer handling
            print("=" * 80)
            print("🗑️ [SOFT DELETE] BROADCASTING TO DELETION CHANNEL")
            print(f"   Channel: {deletion_channel}")
            print(f"   Payload: {pusher_data}")
            print("=" * 80)
            
            try:
                result = pusher_client.trigger(
                    deletion_channel,
                    'content-deleted',
                    pusher_data
                )
                print(f"✅ SENT content-deleted to {deletion_channel}")
                print(f"   Pusher response: {result}")
                logger.info(
                    f"Pusher: content-deleted sent to {deletion_channel}"
                )
            except Exception as e:
                print(f"❌ FAILED to send to deletion channel: {e}")
                logger.error(
                    f"Failed to trigger content-deleted on "
                    f"{deletion_channel}: {e}"
                )
            
            print("=" * 80 + "\n")

            # 3. Guest channel (so guest sees deletion) - kept for compatibility
            pusher_client.trigger(
                guest_channel,
                "message-deleted",
                pusher_data
            )
            logger.info(f"✅ Pusher: message-deleted → {guest_channel}")

            # Secondary event for guest channel as well
            try:
                pusher_client.trigger(
                    guest_channel,
                    "message-removed",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-removed → {guest_channel}")
            except Exception as e:
                logger.debug(f"Optional secondary trigger failed for {guest_channel}: {e}")
            
            # 3. Individual staff channels (so all staff see deletion)
            for staff_member in conversation.participants_staff.all():
                staff_channel = f"{hotel.slug}-staff-{staff_member.id}-chat"
                pusher_client.trigger(
                    staff_channel,
                    "message-deleted",
                    pusher_data
                )
                logger.info(f"✅ Pusher: message-deleted → {staff_channel}")
                try:
                    pusher_client.trigger(
                        staff_channel,
                        "message-removed",
                        pusher_data
                    )
                    logger.info(f"✅ Pusher: message-removed → {staff_channel}")
                except Exception as e:
                    logger.debug(f"Optional secondary trigger failed for {staff_channel}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to trigger Pusher for message-deleted: {e}")
        
        return Response({
            "success": True,
            "hard_delete": False,
            "message": serializer.data
        })


# ==================== FILE ATTACHMENT OPERATIONS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_message_attachment(request, hotel_slug, conversation_id):
    """
    Upload file attachment(s) to a message.
    Supports multiple files per message.
    """
    from .models import MessageAttachment
    from .serializers import MessageAttachmentSerializer
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    if conversation.room.hotel != hotel:
        return Response(
            {"error": "Conversation does not belong to this hotel"},
            status=400
        )
    
    # Get or create message
    message_id = request.data.get('message_id')
    message_text = request.data.get('message', '').strip()
    reply_to_id = request.data.get('reply_to')
    
    # Determine sender type based on authentication
    staff_instance = getattr(request.user, "staff_profile", None)
    sender_type = "staff" if staff_instance else "guest"
    
    logger.info(
        f"📤 File upload request | User: {request.user} | "
        f"Is authenticated: {request.user.is_authenticated} | "
        f"Has staff_profile: {staff_instance is not None} | "
        f"Sender type: {sender_type} | "
        f"Reply to: {reply_to_id if reply_to_id else 'None'}"
    )
    
    if message_id:
        # Attach to existing message
        message = get_object_or_404(RoomMessage, id=message_id)
    else:
        # Create new message with attachment
        if not message_text:
            message_text = "[File shared]"
        
        # Handle reply_to if provided
        reply_to_message = None
        if reply_to_id:
            try:
                reply_to_message = RoomMessage.objects.get(
                    id=reply_to_id,
                    conversation=conversation
                )
                logger.info(
                    f"File attachment message is replying to "
                    f"message ID: {reply_to_id}"
                )
            except RoomMessage.DoesNotExist:
                logger.warning(
                    f"Reply target message {reply_to_id} not found "
                    f"for file upload"
                )
        
        message = RoomMessage.objects.create(
            conversation=conversation,
            room=conversation.room,
            staff=staff_instance if staff_instance else None,
            message=message_text,
            sender_type=sender_type,
            reply_to=reply_to_message,
        )
    
    # Process uploaded files
    files = request.FILES.getlist('files')
    if not files:
        return Response(
            {"error": "No files provided"},
            status=400
        )
    
    # File size limit (50MB per file for high-resolution images)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
        '.pdf',  # PDF
        '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'  # Documents
    ]
    
    attachments = []
    errors = []
    
    for file in files:
        # Validate file size
        if file.size > MAX_FILE_SIZE:
            size_mb = file.size / (1024 * 1024)
            errors.append(
                f"{file.name}: File too large ({size_mb:.2f}MB, max 50MB)"
            )
            continue
        
        # Validate file extension
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(
                f"{file.name}: File type '{ext}' not allowed. "
                f"Allowed: images, PDF, documents"
            )
            continue
        
        try:
            # Create attachment
            attachment = MessageAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name,
                file_size=file.size,
                mime_type=file.content_type or ''
            )
            attachments.append(attachment)
            logger.info(
                f"File uploaded: {file.name} ({file.size} bytes) "
                f"by {sender_type}"
            )
        except Exception as e:
            errors.append(f"{file.name}: Upload failed - {str(e)}")
            logger.error(f"Failed to upload {file.name}: {e}")
    
    if not attachments and errors:
        return Response(
            {"error": "No valid files uploaded", "details": errors},
            status=400
        )
    
    # Serialize attachments
    serializer = MessageAttachmentSerializer(
        attachments,
        many=True,
        context={'request': request}
    )
    
    # Get full message with attachments
    from .serializers import RoomMessageSerializer
    message_serializer = RoomMessageSerializer(message, context={'request': request})
    
    logger.info(
        f"Uploaded {len(attachments)} file(s) to message {message.id} "
        f"by {'staff ' + str(staff_instance) if staff_instance else 'guest'}"
    )
    
    # Trigger Pusher for real-time update
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    
    try:
        pusher_client.trigger(
            message_channel,
            "new-message" if not message_id else "message-updated",
            message_serializer.data
        )
    except Exception as e:
        logger.error(f"Failed to trigger Pusher: {e}")
    
    # Send notifications similar to text messages
    if sender_type == "guest":
        # Notify staff
        reception_staff = Staff.objects.filter(
            hotel=hotel,
            role__slug="receptionist"
        )
        
        target_staff = (
            reception_staff if reception_staff.exists()
            else Staff.objects.filter(hotel=hotel, department__slug="front-office")
        )
        
        for staff in target_staff:
            staff_channel = f"{hotel.slug}-staff-{staff.id}-chat"
            
            # Send Pusher notification
            try:
                pusher_client.trigger(
                    staff_channel,
                    "new-guest-message",
                    message_serializer.data
                )
            except Exception as e:
                logger.error(f"Failed to trigger Pusher: {e}")
            
            # Send FCM notification
            if staff.fcm_token:
                try:
                    # Create notification based on attachment type
                    file_types = [att.file_type for att in attachments]
                    if 'image' in file_types:
                        fcm_title = f"📷 Guest sent {len(attachments)} image(s) - Room {conversation.room.room_number}"
                    elif 'pdf' in file_types:
                        fcm_title = f"📄 Guest sent document(s) - Room {conversation.room.room_number}"
                    else:
                        fcm_title = f"📎 Guest sent {len(attachments)} file(s) - Room {conversation.room.room_number}"
                    
                    fcm_body = message_text if message_text else f"{len(attachments)} file(s) attached"
                    fcm_data = {
                        "type": "new_chat_message_with_files",
                        "conversation_id": str(conversation.id),
                        "room_number": str(conversation.room.room_number),
                        "message_id": str(message.id),
                        "sender_type": "guest",
                        "has_attachments": "true",
                        "attachment_count": str(len(attachments)),
                        "hotel_slug": hotel.slug,
                        "click_action": f"/chat/{hotel.slug}/conversation/{conversation.id}",
                        "url": f"https://hotelsmates.com/chat/{hotel.slug}/conversation/{conversation.id}"
                    }
                    send_fcm_notification(
                        staff.fcm_token,
                        fcm_title,
                        fcm_body,
                        data=fcm_data
                    )
                    logger.info(
                        f"✅ FCM sent to staff {staff.id} for file upload from room {conversation.room.room_number}"
                    )
                except Exception as fcm_error:
                    logger.error(
                        f"❌ Failed to send FCM to staff {staff.id}: {fcm_error}"
                    )
    else:
        # Staff sent files - notify guest
        guest_channel = f"{hotel.slug}-room-{conversation.room.room_number}-chat"
        
        # Send Pusher notification
        try:
            pusher_client.trigger(
                guest_channel,
                "new-staff-message",
                message_serializer.data
            )
            logger.info(
                f"Pusher triggered: guest_channel={guest_channel}, "
                f"event=new-staff-message with {len(attachments)} file(s)"
            )
        except Exception as e:
            logger.error(
                f"Failed to trigger Pusher for guest_channel={guest_channel}: {e}"
            )
        
        # Send FCM notification to guest
        if conversation.room.guest_fcm_token:
            try:
                staff_name = (
                    f"{staff_instance.first_name} {staff_instance.last_name}".strip()
                    if staff_instance else "Hotel Staff"
                )
                
                # Create notification based on attachment type
                file_types = [att.file_type for att in attachments]
                if 'image' in file_types:
                    fcm_title = f"📷 {staff_name} sent {len(attachments)} image(s)"
                elif 'pdf' in file_types:
                    fcm_title = f"📄 {staff_name} sent document(s)"
                else:
                    fcm_title = f"📎 {staff_name} sent {len(attachments)} file(s)"
                
                fcm_body = message_text if message_text else "View attachment(s)"
                fcm_data = {
                    "type": "new_chat_message_with_files",
                    "conversation_id": str(conversation.id),
                    "room_number": str(conversation.room.room_number),
                    "message_id": str(message.id),
                    "sender_type": "staff",
                    "staff_name": staff_name,
                    "has_attachments": "true",
                    "attachment_count": str(len(attachments)),
                    "hotel_slug": hotel.slug,
                    "click_action": f"/chat/{hotel.slug}/room/{conversation.room.room_number}",
                    "url": f"https://hotelsmates.com/chat/{hotel.slug}/room/{conversation.room.room_number}"
                }
                send_fcm_notification(
                    conversation.room.guest_fcm_token,
                    fcm_title,
                    fcm_body,
                    data=fcm_data
                )
                logger.info(
                    f"✅ FCM sent to guest in room {conversation.room.room_number} "
                    f"for file upload from staff"
                )
            except Exception as fcm_error:
                logger.error(
                    f"❌ Failed to send FCM to guest room "
                    f"{conversation.room.room_number}: {fcm_error}"
                )
    
    response_data = {
        "message": message_serializer.data,
        "attachments": serializer.data,
        "success": True
    }
    
    if errors:
        response_data["warnings"] = errors
    
    return Response(response_data)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_attachment(request, attachment_id):
    """
    Delete a file attachment.
    Only the message sender can delete attachments.
    """
    from .models import MessageAttachment
    
    attachment = get_object_or_404(MessageAttachment, id=attachment_id)
    message = attachment.message
    
    # Check permissions
    staff = getattr(request.user, "staff_profile", None)
    is_staff = staff is not None
    
    if is_staff and message.sender_type == "staff":
        if message.staff != staff:
            return Response(
                {"error": "You can only delete your own attachments"},
                status=403
            )
    elif not is_staff and message.sender_type == "guest":
        pass
    else:
        return Response(
            {"error": "You don't have permission to delete this attachment"},
            status=403
        )
    
    # Delete the file from storage
    if attachment.file:
        attachment.file.delete(save=False)
    if attachment.thumbnail:
        attachment.thumbnail.delete(save=False)
    
    attachment_id_copy = attachment.id
    attachment.delete()
    
    logger.info(
        f"Attachment {attachment_id_copy} deleted from message {message.id}"
    )
    
    # Trigger Pusher for real-time update
    hotel = message.room.hotel
    room = message.room
    message_channel = (
        f"{hotel.slug}-conversation-{message.conversation.id}-chat"
    )
    # NEW: Dedicated deletion channel
    deletion_channel = f"{hotel.slug}-room-{room.room_number}-deletions"
    
    # Determine who deleted the attachment
    deleter_type = "staff" if is_staff else "guest"
    
    pusher_data = {
        "attachment_id": attachment_id_copy,
        "message_id": message.id,
        "deleted_by": deleter_type,
        "original_sender": message.sender_type,
        "staff_id": staff.id if is_staff else None,
        "staff_name": (
            f"{staff.first_name} {staff.last_name}".strip()
            if is_staff and staff else None
        ),
        "timestamp": timezone.now().isoformat()
    }
    
    # Broadcast to conversation channel (for compatibility)
    try:
        pusher_client.trigger(
            message_channel,
            "attachment-deleted",
            pusher_data
        )
        logger.info(
            f"Pusher: attachment-deleted → {message_channel}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger Pusher: {e}")
    
    # Broadcast to dedicated deletion channel (NEW)
    try:
        pusher_client.trigger(
            deletion_channel,
            "attachment-deleted",
            pusher_data
        )
        print(f"✅ Attachment deletion sent to {deletion_channel}")
        logger.info(
            f"Pusher: attachment-deleted → {deletion_channel}"
        )
    except Exception as e:
        print(f"❌ Failed to send attachment deletion: {e}")
        logger.error(
            f"Failed to trigger attachment-deleted on "
            f"{deletion_channel}: {e}"
        )
    
    return Response({
        "success": True,
        "attachment_id": attachment_id_copy,
        "message_id": message.id
    })


# ==================== FCM TOKEN MANAGEMENT ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def save_fcm_token(request, hotel_slug):
    """
    Save FCM token for guest chat notifications.
    Used to enable push notifications for guests using the chat system.
    
    POST /api/chat/{hotel_slug}/save-fcm-token/
    Body: {"fcm_token": "device_token_here", "room_number": 101}
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    fcm_token = request.data.get('fcm_token')
    room_number = request.data.get('room_number')
    
    if not fcm_token:
        return Response(
            {'error': 'fcm_token is required'},
            status=400
        )
    
    if not room_number:
        return Response(
            {'error': 'room_number is required'},
            status=400
        )
    
    try:
        room = get_object_or_404(Room, hotel=hotel, room_number=room_number)
        
        # Save FCM token to room
        room.guest_fcm_token = fcm_token
        room.save()
        
        logger.info(
            f"Chat FCM token saved for room {room_number} "
            f"at {hotel.name} via chat endpoint"
        )
        
        return Response({
            'success': True,
            'message': 'FCM token saved successfully for chat notifications',
            'room_number': room_number,
            'hotel_slug': hotel_slug
        })
        
    except Room.DoesNotExist:
        return Response(
            {'error': f'Room {room_number} not found in {hotel.name}'},
            status=404
        )
    except Exception as e:
        logger.error(f"Failed to save chat FCM token: {e}")
        return Response(
            {'error': 'Failed to save FCM token'},
            status=500
        )


# ==================== TEST ENDPOINTS ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def test_deletion_broadcast(request, hotel_slug, room_number):
    """
    TEST ENDPOINT: Simulate a deletion broadcast to guest channel.
    This helps verify that Pusher events reach the guest UI.
    
    Usage: POST /api/chat/test/{hotel_slug}/room/{room_number}/test-deletion/
    Body: {"message_id": 123, "hard_delete": true}
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    
    # Get test data from request
    message_id = request.data.get('message_id', 999)
    hard_delete = request.data.get('hard_delete', True)
    
    # Prepare channels
    room_channel = f'{hotel_slug}-room-{room_number}-chat'
    
    # Prepare payload
    pusher_data = {
        "message_id": message_id,
        "hard_delete": hard_delete
    }
    
    print("\n" + "=" * 80)
    print("🧪 TEST DELETION BROADCAST")
    print(f"   Hotel: {hotel_slug}")
    print(f"   Room: {room_number}")
    print(f"   Channel: {room_channel}")
    print(f"   Message ID: {message_id}")
    print(f"   Hard Delete: {hard_delete}")
    print(f"   Payload: {pusher_data}")
    print("=" * 80)
    
    results = {
        "test": "deletion_broadcast",
        "hotel": hotel_slug,
        "room": room_number,
        "channel": room_channel,
        "payload": pusher_data,
        "broadcasts": []
    }
    
    # Broadcast to room channel (guest)
    try:
        print(f"\n📡 Broadcasting 'message-deleted' to {room_channel}...")
        result = pusher_client.trigger(
            room_channel,
            'message-deleted',
            pusher_data
        )
        print(f"✅ SUCCESS: message-deleted sent")
        print(f"   Pusher response: {result}")
        results["broadcasts"].append({
            "event": "message-deleted",
            "channel": room_channel,
            "status": "success",
            "response": str(result)
        })
    except Exception as e:
        print(f"❌ FAILED: message-deleted - {e}")
        results["broadcasts"].append({
            "event": "message-deleted",
            "channel": room_channel,
            "status": "error",
            "error": str(e)
        })
    
    # Also try message-removed alias
    try:
        print(f"\n📡 Broadcasting 'message-removed' to {room_channel}...")
        result = pusher_client.trigger(
            room_channel,
            'message-removed',
            pusher_data
        )
        print(f"✅ SUCCESS: message-removed sent")
        print(f"   Pusher response: {result}")
        results["broadcasts"].append({
            "event": "message-removed",
            "channel": room_channel,
            "status": "success",
            "response": str(result)
        })
    except Exception as e:
        print(f"❌ FAILED: message-removed - {e}")
        results["broadcasts"].append({
            "event": "message-removed",
            "channel": room_channel,
            "status": "error",
            "error": str(e)
        })
    
    print("=" * 80 + "\n")
    
    logger.info(
        f"Test deletion broadcast completed for {hotel_slug}/room-{room_number}"
    )
    
    return Response(results)
