from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import json

from .models import RoomMessage
from .serializers import RoomMessageSerializer
from .utils import pusher_client
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rooms.models import Room
from hotel.models import  Hotel

@csrf_exempt
@api_view(['POST'])
def send_room_message(request, hotel_slug, room_number):
    """
    Guest or staff sends a message in a room chat for a specific hotel
    """
    data = json.loads(request.body)
    guest_id = data.get("guest")  # optional if staff
    staff_id = data.get("staff")  # optional if guest
    message_text = data.get("message")

    if not message_text:
        return Response({"error": "message required"}, status=400)

    message = RoomMessage.objects.create(
        room_id=room_number,  # you can fetch Room object if needed
        guest_id=guest_id,
        staff_id=staff_id,
        message=message_text,
        hotel_slug=hotel_slug
    )

    # Trigger Pusher event for real-time update
    pusher_client.trigger(
        f"{hotel_slug}-room-{room_number}-chat",
        "new-message",
        {
            "id": message.id,
            "room": room_number,
            "guest": guest_id,
            "staff": staff_id,
            "message": message_text,
            "created_at": message.created_at.isoformat()
        }
    )

    serializer = RoomMessageSerializer(message)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_room_messages(request, hotel_slug, room_number):
    """
    Staff can fetch all messages for a room in a hotel
    """
    messages = RoomMessage.objects.filter(room__room_number=room_number, hotel_slug=hotel_slug)
    serializer = RoomMessageSerializer(messages, many=True)
    return Response(serializer.data)

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

