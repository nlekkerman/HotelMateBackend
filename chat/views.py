from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

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
    message = RoomMessage.objects.create(
        conversation=conversation,
        room=room,
        staff=staff_instance if staff_instance else None,
        message=message_text,
        sender_type=sender_type,
    )

    serializer = RoomMessageSerializer(message)

    # Trigger Pusher
    channel_name = f"{hotel.slug}-conversation-{conversation.id}-chat"
    pusher_client.trigger(channel_name, "new-message", serializer.data)

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


