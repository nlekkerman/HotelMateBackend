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
@permission_classes([IsAuthenticated])
def get_conversation_messages(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = conversation.messages.order_by('timestamp')
    serializer = RoomMessageSerializer(messages, many=True)
    return Response(serializer.data)


# Send a message in a conversation
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_conversation_message(request, hotel_slug, room_number):
    # Get hotel and room
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)

    # Try to get existing conversation or create a new one
    conversation, created = Conversation.objects.get_or_create(room=room)

    message_text = request.data.get("message", "").strip()
    if not message_text:
        return Response({"error": "Message cannot be empty"}, status=400)

    staff_instance = getattr(request.user, "staff_profile", None)
    if staff_instance:
        sender_type = "staff"
        message = RoomMessage.objects.create(
            conversation=conversation,
            room=room,
            staff=staff_instance,
            message=message_text,
            sender_type=sender_type
        )
    else:
        sender_type = "guest"
        message = RoomMessage.objects.create(
            conversation=conversation,
            room=room,
            message=message_text,
            sender_type=sender_type
        )

    serializer = RoomMessageSerializer(message)

    # Trigger Pusher event
    channel_name = f"{hotel.slug}-conversation-{conversation.id}-chat"
    pusher_client.trigger(channel_name, "new-message", serializer.data)

    return Response(serializer.data)


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
