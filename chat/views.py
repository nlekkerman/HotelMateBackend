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

    # Determine sender
    staff_instance = getattr(request.user, "staff_profile", None)
    sender_type = "staff" if staff_instance else "guest"
    
    logger.info(
        f"🔵 NEW MESSAGE | Type: {sender_type} | "
        f"Hotel: {hotel.slug} | Room: {room.room_number} | "
        f"Conversation: {conversation.id}"
    )

    # Get session token for guest
    session_token = request.data.get("session_token")

    # Create the message
    message = RoomMessage.objects.create(
        conversation=conversation,
        room=room,
        staff=staff_instance if staff_instance else None,
        message=message_text,
        sender_type=sender_type,
    )

    # Update session handler when staff replies
    if sender_type == "staff" and session_token:
        try:
            session = GuestChatSession.objects.get(
                session_token=session_token,
                conversation=conversation,
                is_active=True
            )
            session.current_staff_handler = staff_instance
            session.save()
            logger.info(
                f"Updated session handler to {staff_instance} "
                f"for session {session_token}"
            )
        except GuestChatSession.DoesNotExist:
            logger.warning(
                f"Session token {session_token} not found "
                f"for conversation {conversation.id}"
            )

    serializer = RoomMessageSerializer(message)
    logger.info(f"Message created with ID: {message.id}")

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

        for staff in target_staff:
            staff_channel = f"{hotel.slug}-staff-{staff.id}-chat"
            try:
                pusher_client.trigger(staff_channel, "new-guest-message", serializer.data)
                logger.info(f"Pusher triggered: staff_channel={staff_channel}, event=new-guest-message, message_id={message.id}")
            except Exception as e:
                logger.error(f"Failed to trigger Pusher for staff_channel={staff_channel}: {e}")
            
            # Send FCM notification to staff
            if staff.fcm_token:
                print(f"🔔 Staff {staff.id} has FCM token: {staff.fcm_token[:20]}...")
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
        if message_ids:
            message_channel = (
                f"{hotel.slug}-conversation-{conversation.id}-chat"
            )
            try:
                pusher_client.trigger(
                    message_channel,
                    "messages-read-by-staff",
                    {
                        "message_ids": message_ids,
                        "read_at": timezone.now().isoformat(),
                        "staff_name": str(staff)
                    }
                )
                logger.info(
                    f"Pusher triggered: messages-read-by-staff, "
                    f"count={len(message_ids)}"
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
