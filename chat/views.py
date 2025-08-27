from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rooms.models import Room
from hotel.models import Hotel
from staff.models import Staff
from .models import Conversation, RoomMessage
from .serializers import ConversationSerializer, RoomMessageSerializer
from .utils import pusher_client
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
    logger.info(f"Message sender type: {sender_type}, user_id: {request.user.id}")

    # Create the message
    message = RoomMessage.objects.create(
        conversation=conversation,
        room=room,
        staff=staff_instance if staff_instance else None,
        message=message_text,
        sender_type=sender_type,
    )

    serializer = RoomMessageSerializer(message)
    logger.info(f"Message created with ID: {message.id}")

    # Update conversation unread status if guest sends a message
    if sender_type == "guest":
        if not conversation.has_unread:
            conversation.has_unread = True
            conversation.save()
            logger.info(f"Conversation {conversation.id} marked as unread")

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

        if reception_staff.exists():
            target_staff = reception_staff
            logger.info(f"Targeting reception staff for notifications: count={reception_staff.count()}")
        else:
            target_staff = Staff.objects.filter(
                hotel=hotel,
                department__slug="front-office"
            )
            logger.info(f"No reception staff found. Targeting front-office staff: count={target_staff.count()}")

        for staff in target_staff:
            staff_channel = f"{hotel.slug}-staff-{staff.id}-chat"
            try:
                pusher_client.trigger(staff_channel, "new-guest-message", serializer.data)
                logger.info(f"Pusher triggered: staff_channel={staff_channel}, event=new-guest-message, message_id={message.id}")
            except Exception as e:
                logger.error(f"Failed to trigger Pusher for staff_channel={staff_channel}: {e}")

    # Trigger Pusher for the actual new message (for all listeners)
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    try:
        pusher_client.trigger(message_channel, "new-message", serializer.data)
        logger.info(f"Pusher triggered for new message: channel={message_channel}, message_id={message.id}")
    except Exception as e:
        logger.error(f"Failed to trigger Pusher for message_channel={message_channel}: {e}")

    return Response({
        "conversation_id": conversation.id,
        "message": serializer.data
    })

# Keep validation unchanged
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_chat_pin(request, hotel_slug, room_number):
    """
    Validates the PIN for accessing a chat room.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    
    pin = request.data.get('pin')
    if pin == room.guest_id_pin:  # you can add a separate field for chat if needed
        return Response({'valid': True})
    
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
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response({"detail": "Unauthorized"}, status=403)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    room = conversation.room
    hotel = room.hotel

    # Mark all guest messages in this conversation as read
    updated_count = conversation.messages.filter(
        sender_type="guest",
        read_by_staff=False
    ).update(read_by_staff=True)

    # Clear conversation unread flag
    if conversation.has_unread:
        conversation.has_unread = False
        conversation.save()

        # Trigger Pusher to update sidebar badge
        badge_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
        pusher_client.trigger(badge_channel, "conversation-read", {
            "conversation_id": conversation.id,
            "room_number": room.room_number,
        })

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
