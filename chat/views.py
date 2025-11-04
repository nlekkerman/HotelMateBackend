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
import logging

logger = logging.getLogger(__name__)

# Fetch all conversations (rooms with messages) for a hotel
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_conversations(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    conversations = Conversation.objects.filter(
        room__hotel=hotel
    ).order_by('-updated_at')

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
    
    # DEBUG: Log serialized data
    logger.info(
        f"📤 Serialized data | "
        f"reply_to: {serializer.data.get('reply_to')} | "
        f"reply_to_message: {serializer.data.get('reply_to_message')}"
    )

    # Trigger message-delivered event
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    try:
        pusher_client.trigger(message_channel, "message-delivered", {
            "message_id": message.id,
            "delivered_at": message.delivered_at.isoformat(),
            "status": "delivered"
        })
        logger.info(
            f"Pusher triggered for message delivered: "
            f"message_id={message.id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher for message-delivered: {e}"
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
                serializer.data
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

        # Trigger Pusher for sidebar badge update
        badge_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
        try:
            pusher_client.trigger(badge_channel, "conversation-unread", {
                "conversation_id": conversation.id,
                "room_number": room.room_number,
            })
            logger.info(f"Pusher triggered for badge update: channel={badge_channel}")
        except Exception as e:
            logger.error(f"Failed to trigger Pusher for badge update: {e}")

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

        print(f"📬 Sending notifications to {target_staff.count()} staff members")
        for staff in target_staff:
            staff_channel = f"{hotel.slug}-staff-{staff.id}-chat"
            
            # Send Pusher event
            try:
                pusher_client.trigger(staff_channel, "new-guest-message", serializer.data)
                print(f"✅ Pusher sent to staff {staff.id}: {staff_channel}")
                logger.info(f"Pusher triggered: staff_channel={staff_channel}, event=new-guest-message, message_id={message.id}")
            except Exception as e:
                print(f"❌ Pusher FAILED for staff {staff.id}: {e}")
                logger.error(f"Failed to trigger Pusher for staff_channel={staff_channel}: {e}")
            
            # Send FCM notification to staff
            if staff.fcm_token:
                print(f"🔔 Staff {staff.id} ({staff.user.username}) has FCM token, sending notification...")
                try:
                    fcm_title = f"💬 New Message - Room {room.room_number}"
                    fcm_body = message_text[:100]  # Preview of message
                    fcm_data = {
                        "type": "new_chat_message",
                        "conversation_id": str(conversation.id),
                        "room_number": str(room.room_number),
                        "message_id": str(message.id),
                        "sender_type": "guest",
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
                    print(f"✅ FCM sent to staff {staff.id} for message from room {room.room_number}")
                    logger.info(
                        f"FCM sent to staff {staff.id} "
                        f"for message from room {room.room_number}"
                    )
                except Exception as fcm_error:
                    print(f"❌ FCM FAILED for staff {staff.id}: {fcm_error}")
                    logger.error(
                        f"Failed to send FCM to staff {staff.id}: "
                        f"{fcm_error}"
                    )
            else:
                print(f"⚠️ Staff {staff.id} ({staff.user.username}) has NO FCM token")

    else:
        # Staff sent a message - notify guest on room-specific channel
        guest_channel = f"{hotel.slug}-room-{room.room_number}-chat"
        try:
            pusher_client.trigger(
                guest_channel,
                "new-staff-message",
                serializer.data
            )
            logger.info(
                f"Pusher triggered: guest_channel={guest_channel}, "
                f"event=new-staff-message, message_id={message.id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to trigger Pusher for "
                f"guest_channel={guest_channel}: {e}"
            )
        
        # Send FCM notification to guest
        if room.guest_fcm_token:
            try:
                staff_name = (
                    message.staff_display_name 
                    if message.staff_display_name 
                    else "Hotel Staff"
                )
                fcm_title = f"💬 {staff_name}"
                fcm_body = message_text[:100]  # Preview of message
                fcm_data = {
                    "type": "new_chat_message",
                    "conversation_id": str(conversation.id),
                    "room_number": str(room.room_number),
                    "message_id": str(message.id),
                    "sender_type": "staff",
                    "staff_name": staff_name,
                    "hotel_slug": hotel.slug,
                    "click_action": f"/chat/{hotel.slug}/room/{room.room_number}",
                    "url": f"https://hotelsmates.com/chat/{hotel.slug}/room/{room.room_number}"
                }
                send_fcm_notification(
                    room.guest_fcm_token,
                    fcm_title,
                    fcm_body,
                    data=fcm_data
                )
                logger.info(
                    f"FCM sent to guest in room {room.room_number} "
                    f"for message from staff"
                )
            except Exception as fcm_error:
                logger.error(
                    f"Failed to send FCM to guest room "
                    f"{room.room_number}: {fcm_error}"
                )

    # Trigger Pusher for the actual new message (for all listeners)
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    try:
        pusher_client.trigger(message_channel, "new-message", serializer.data)
        logger.info(
            f"Pusher triggered for new message: "
            f"channel={message_channel}, message_id={message.id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to trigger Pusher for "
            f"message_channel={message_channel}: {e}"
        )

    # Prepare response with staff info
    response_data = {
        "conversation_id": conversation.id,
        "message": serializer.data
    }

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
        # Trigger Pusher for new conversation
        channel_name = f"{hotel.slug}-new-conversation"
        pusher_client.trigger(channel_name, "new-conversation", {
            "conversation_id": conversation.id,
            "room_number": room.room_number,
        })

    return Response({
        "conversation_id": conversation.id,
        "messages": serializer.data,
        "conversation_created": created
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_active_rooms(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    conversations = Conversation.objects.filter(room__hotel=hotel).order_by('-updated_at')
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

            # Trigger Pusher to update sidebar badge
            badge_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
            try:
                pusher_client.trigger(badge_channel, "conversation-read", {
                    "conversation_id": conversation.id,
                    "room_number": room.room_number,
                })
            except Exception as e:
                logger.error(f"Failed to trigger conversation-read: {e}")
    
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
    
    # Staff can only delete their own messages (or with admin permission)
    if is_staff and message.sender_type == "staff":
        if message.staff != staff:
            # Check if staff has admin/manager role for hard delete
            if hard_delete and not (
                staff.role and staff.role.slug in ['manager', 'admin']
            ):
                return Response(
                    {"error": "Only managers can hard delete other's messages"},
                    status=403
                )
            elif not hard_delete:
                return Response(
                    {"error": "You can only delete your own messages"},
                    status=403
                )
    # Guest messages can only be deleted by the guest
    elif not is_staff and message.sender_type == "guest":
        pass
    else:
        return Response(
            {"error": "You don't have permission to delete this message"},
            status=403
        )
    
    hotel = message.room.hotel
    room = message.room
    conversation = message.conversation
    
    # Prepare Pusher channels
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    guest_channel = f"{hotel.slug}-room-{room.room_number}-chat"
    
    print(f"🗑️ DELETE REQUEST | message_id={message_id} | hotel={hotel.slug} | room={room.room_number}")
    print(f"🗑️ CHANNELS | conversation={message_channel} | guest={guest_channel}")
    print(f"🗑️ SENDER | type={message.sender_type} | is_staff={is_staff} | hard_delete={hard_delete}")
    
    if hard_delete and is_staff:
        # Hard delete (only for admin staff)
        message_id_copy = message.id
        pusher_data = {"message_id": message_id_copy, "hard_delete": True}
        
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

            # 2. Guest channel (so guest sees deletion)
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
        message.soft_delete()
        
        logger.info(
            f"Message {message_id} soft deleted by "
            f"{'staff ' + str(staff) if is_staff else 'guest'}"
        )
        
        from .serializers import RoomMessageSerializer
        serializer = RoomMessageSerializer(message)
        
        pusher_data = {
            "message_id": message.id,
            "hard_delete": False,
            "message": serializer.data
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
            
            # 2. Guest channel (so guest sees deletion)
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
    message_channel = (
        f"{hotel.slug}-conversation-{message.conversation.id}-chat"
    )
    
    try:
        pusher_client.trigger(
            message_channel,
            "attachment-deleted",
            {
                "attachment_id": attachment_id_copy,
                "message_id": message.id
            }
        )
    except Exception as e:
        logger.error(f"Failed to trigger Pusher: {e}")
    
    return Response({
        "success": True,
        "attachment_id": attachment_id_copy,
        "message_id": message.id
    })
