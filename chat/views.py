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
from .models import Conversation, RoomMessage, GuestConversationParticipant
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
    ).select_related('room').prefetch_related('messages').order_by('-updated_at')

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
        # Check if this is a guest conversation (has room)
        if room:
            # Get or create participant record
            participant, created = GuestConversationParticipant.objects.get_or_create(
                conversation=conversation,
                staff=staff_instance,
                defaults={'joined_at': timezone.now()}
            )
            
            # If staff member is new to this conversation, create system join message
            if created:
                staff_name = f"{staff_instance.first_name} {staff_instance.last_name}".strip()
                join_message = RoomMessage.objects.create(
                    conversation=conversation,
                    room=room,
                    staff=None,  # System message has no staff FK
                    message=f"{staff_name} has joined the conversation.",
                    sender_type="system",
                    reply_to=None,
                )
                
                # Emit system message via NotificationManager
                try:
                    notification_manager.realtime_guest_chat_message_created(join_message)
                    logger.info(f"System join message created and emitted: {join_message.id}")
                except Exception as e:
                    logger.error(f"Failed to emit system join message {join_message.id}: {e}")
        
        # Check if staff handler is changing before updating
        # Get current handler from GuestConversationParticipant
        current_participant = GuestConversationParticipant.objects.filter(
            conversation=conversation
        ).order_by('-joined_at').first()
        
        current_handler = current_participant.staff if current_participant else None
        
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
            
            # Staff assignment notifications now handled by booking channel
            # via realtime_guest_chat_message_created() when staff sends first message
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

        # Legacy broadcasts removed - now handled by NotificationManager.realtime_guest_chat_message_created()
        # which uses only booking-scoped channels: private-hotel-{slug}-guest-chat-booking-{booking_id}

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


# === NEW: Token-based Guest Chat Context ===

@api_view(['GET'])
@permission_classes([AllowAny])
def guest_chat_context(request, hotel_slug):
    """
    Get guest chat context using token authentication.
    Replaces the PIN-based flow for the guest portal.
    
    Query Parameters:
        token (required): Guest booking token
        
    Returns:
        200: {
            conversation_id: int,
            room_number: str,
            pusher_channel: str,
            current_staff_handler: {name: str, role: str} | null
        }
        404: Invalid token or hotel mismatch
        403: Guest not checked in
        409: No room assigned
    """
    from bookings.services import resolve_guest_chat_context, GuestChatAccessError
    
    token = request.GET.get('token')
    if not token:
        return Response({"error": "Token parameter is required"}, status=400)
    
    try:
        booking, room, conversation = resolve_guest_chat_context(
            hotel_slug=hotel_slug,
            token_str=token,
            require_in_house=True
        )
        
        # Get current staff handler from GuestConversationParticipant (active staff in conversation)
        current_staff_handler = None
        active_participant = GuestConversationParticipant.objects.filter(
            conversation=conversation
        ).order_by('-joined_at').first()
        
        if active_participant and active_participant.staff:
            staff = active_participant.staff
            current_staff_handler = {
                "name": f"{staff.first_name} {staff.last_name}".strip(),
                "role": staff.role.name if staff.role else "Staff"
            }
        
        # Build pusher channel name (booking-scoped, survives room moves)
        pusher_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking.booking_id}"
        
        logger.info(
            f"✅ Guest chat context provided: booking={booking.booking_id}, "
            f"room={room.room_number}, conversation={conversation.id}"
        )
        
        return Response({
            "conversation_id": conversation.id,
            "room_number": room.room_number,
            "booking_id": booking.booking_id,
            "pusher": {
                "channel": pusher_channel,
                "event": "realtime_event"  # Single event name for eventBus routing
            },
            "allowed_actions": {
                "can_chat": True
            },
            "current_staff_handler": current_staff_handler,
            "assigned_room_id": room.id
        })
        
    except GuestChatAccessError as e:
        logger.warning(f"Guest chat context denied: {e.message}")
        return Response({"error": e.message}, status=e.status_code)
    except Exception as e:
        logger.error(f"Unexpected error in guest_chat_context: {e}")
        return Response({"error": "Internal server error"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def guest_send_message(request, hotel_slug):
    """
    Send a message as a guest using token authentication.
    Dedicated endpoint for guest portal to send messages.
    
    Query Parameters:
        token (required): Guest booking token
        
    Body:
        message (required): Message text
        reply_to (optional): Message ID to reply to
        
    Returns:
        201: Message created successfully
        400: Invalid request data
        401: Token required
        403/404/409: Access denied (various reasons)
    """
    from bookings.services import resolve_guest_chat_context, GuestChatAccessError
    
    token = request.GET.get('token')
    if not token:
        return Response({"error": "Token parameter is required"}, status=401)
    
    message_text = request.data.get("message", "").strip()
    if not message_text:
        return Response({"error": "Message cannot be empty"}, status=400)
    
    reply_to_id = request.data.get("reply_to")
    reply_to_message = None
    
    try:
        # Validate token and get guest context
        booking, room, conversation = resolve_guest_chat_context(
            hotel_slug=hotel_slug,
            token_str=token,
            require_in_house=True
        )
        
        # Handle reply_to if provided
        if reply_to_id:
            try:
                reply_to_message = RoomMessage.objects.get(
                    id=reply_to_id,
                    conversation=conversation
                )
                logger.info(f"Guest message replying to message ID: {reply_to_id}")
            except RoomMessage.DoesNotExist:
                logger.warning(f"Guest reply target message {reply_to_id} not found")
                # Continue without reply - don't fail the request
        
        # Create the message
        message = RoomMessage.objects.create(
            conversation=conversation,
            room=room,
            staff=None,  # Guest message
            message=message_text,
            sender_type="guest",
            reply_to=reply_to_message,
        )
        
        logger.info(
            f"✅ Guest message created: ID={message.id}, booking={booking.booking_id}, "
            f"room={room.room_number}, conversation={conversation.id}"
        )
        
        # Use existing NotificationManager for realtime events
        try:
            notification_manager.realtime_guest_chat_message_created(message)
            logger.info(f"NotificationManager triggered for guest message {message.id}")
        except Exception as e:
            logger.error(f"NotificationManager failed for guest message {message.id}: {e}")
        
        # Serialize and return the message
        serializer = RoomMessageSerializer(message)
        return Response(serializer.data, status=201)
        
    except GuestChatAccessError as e:
        logger.warning(f"Guest send message denied: {e.message}")
        return Response({"error": e.message}, status=e.status_code)
    except Exception as e:
        logger.error(f"Unexpected error in guest_send_message: {e}")
        return Response({"error": "Internal server error"}, status=500)


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
def mark_conversation_read(request, hotel_slug, conversation_id):
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
            # Read receipt notifications now handled by booking channel
            # Staff clients should listen to booking channels for read status updates
            logger.info(
                f"Guest marked {len(message_ids)} messages as read. "
                f"Read receipts now delivered via booking channel."
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
    current_participant = GuestConversationParticipant.objects.filter(
        conversation=conversation
    ).order_by('-joined_at').first()
    
    current_handler = current_participant.staff if current_participant else None
    
    # Only update and notify if staff handler is changing
    staff_changed = current_handler != staff
    created = False  # Initialize for response
    
    if staff_changed:
        # Create or update participant record to make this staff member the current handler
        participant, created = GuestConversationParticipant.objects.get_or_create(
            conversation=conversation,
            staff=staff,
            defaults={'joined_at': timezone.now()}
        )
        
        # If this creates a new participant, it automatically makes them the current handler
        # since we order by -joined_at to get the latest participant
        
        logger.info(
            f"Staff handler changed from {current_handler} to {staff} "
            f"for conversation {conversation_id}. "
            f"Participant record {'created' if created else 'updated'}"
        )
        
        # Notify guest that a NEW staff member is now handling their chat
        room = conversation.room
        
        # Staff assignment notifications now handled by booking channel
        # Guest will see staff info when staff sends their first message
        logger.info(
            f"Staff assignment complete: {staff} assigned to conversation {conversation_id}. "
            f"Guest will be notified via booking channel when staff responds."
        )
    else:
        logger.info(
            f"Staff {staff} already assigned to conversation "
            f"{conversation_id}, skipping staff-assigned event"
        )
    
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
        
        # Send read receipt notification via booking channel
        try:
            # Staff read receipts now handled by booking channel
            # Guest clients should listen to booking channels for read status updates
            logger.info(
                f"📡 Staff opened conversation: marked {read_count} messages as read, "
                f"read receipts delivered via booking channel, message_ids={message_ids}"
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
        "participant_created": created if staff_changed else False,
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
    
    # Use unified guest chat edit broadcast  
    try:
        notification_manager.realtime_guest_chat_message_edited(message)
        logger.info(f"Unified edit broadcast sent for message {message_id}")
    except Exception as e:
        logger.error(f"Failed to broadcast edit via NotificationManager: {e}")
    
    # Serialize for response
    from .serializers import RoomMessageSerializer
    serializer = RoomMessageSerializer(message)
    
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
        
        # Use unified guest chat deletion broadcast
        try:
            notification_manager.realtime_guest_chat_message_deleted(
                message_id=message_id_copy,
                conversation_id=conversation.id,
                room=room,
                deleted_by_staff=staff,
                deleted_by_guest=False
            )
            logger.info(f"Unified deletion broadcast sent for message {message_id_copy}")
        except Exception as e:
            logger.error(f"Failed to broadcast deletion via NotificationManager: {e}")
        
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
            # Use unified guest chat deletion broadcast
            is_guest_deleting = not is_staff
            notification_manager.realtime_guest_chat_message_deleted(
                message_id=message.id,
                conversation_id=conversation.id,
                room=room,
                deleted_by_staff=staff if is_staff else None,
                deleted_by_guest=is_guest_deleting
            )
            logger.info(f"Unified deletion broadcast sent for message {message.id}")
        except Exception as e:
            logger.error(f"Failed to broadcast deletion via NotificationManager: {e}")
        
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
    
    # Use unified guest chat message broadcast for file attachments
    try:
        notification_manager.realtime_guest_chat_message_created(message)
        logger.info(f"Unified file attachment broadcast sent for message {message.id}")
    except Exception as e:
        logger.error(f"Failed to broadcast file attachment via NotificationManager: {e}")
    
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
            "attachment_deleted",
            pusher_data
        )
        logger.info(
            f"Pusher: attachment_deleted → {message_channel}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger Pusher: {e}")
    
    # Broadcast to dedicated deletion channel (NEW)
    try:
        pusher_client.trigger(
            deletion_channel,
            "attachment_deleted",
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
