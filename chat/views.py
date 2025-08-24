from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rooms.models import Room
from hotel.models import Hotel
from .models import Conversation, RoomMessage
from .serializers import ConversationSerializer, RoomMessageSerializer
from .utils import pusher_client


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
    # optional: verify that conversation.room.hotel.slug == hotel_slug
    if conversation.room.hotel.slug != hotel_slug:
        return Response({"error": "Conversation does not belong to this hotel"}, status=400)

    messages = conversation.messages.order_by('timestamp')
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
        return Response({"error": "Message cannot be empty"}, status=400)

    # Determine sender
    staff_instance = getattr(request.user, "staff_profile", None)
    sender_type = "staff" if staff_instance else "guest"

    # Create the message
    message = RoomMessage.objects.create(
        conversation=conversation,
        room=room,
        staff=staff_instance if staff_instance else None,
        message=message_text,
        sender_type=sender_type,
    )

    serializer = RoomMessageSerializer(message)

    # Update conversation unread status if guest sends a message
    if sender_type == "guest" and not conversation.has_unread:
        conversation.has_unread = True
        conversation.save()

        # Trigger Pusher for sidebar badge update
        badge_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
        pusher_client.trigger(badge_channel, "conversation-unread", {
            "conversation_id": conversation.id,
            "room_number": room.room_number,
        })

    # Trigger Pusher for the actual new message
    message_channel = f"{hotel.slug}-conversation-{conversation.id}-chat"
    pusher_client.trigger(message_channel, "new-message", serializer.data)

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
@permission_classes([IsAuthenticated])
def get_active_rooms(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    conversations = Conversation.objects.filter(room__hotel=hotel).order_by('-updated_at')
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def get_unread_conversation_count(request, hotel_slug):
    staff = getattr(request.user, "staff_profile", None)
    if not staff:
        return Response({"unread_count": 0})

    hotel = get_object_or_404(Hotel, slug=hotel_slug)

    # Count distinct conversations with at least 1 unread guest message
    unread_count = (
        Conversation.objects
        .filter(room__hotel=hotel)
        .filter(messages__read_by_staff=False, messages__sender_type="guest")
        .distinct()
        .count()
    )

    return Response({"unread_count": unread_count})