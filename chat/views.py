from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import json

from .models import RoomMessage
from .serializers import RoomMessageSerializer
from .utils import pusher_client

@csrf_exempt
@api_view(['POST'])
def send_room_message(request, hotel_slug):
    """
    Guest or staff sends a message in a room chat for a specific hotel
    """
    data = json.loads(request.body)
    room_id = data.get("room")
    guest_id = data.get("guest")  # optional if staff
    staff_id = data.get("staff")  # optional if guest
    message_text = data.get("message")

    if not message_text or not room_id:
        return Response({"error": "room and message required"}, status=400)

    message = RoomMessage.objects.create(
        room_id=room_id,
        guest_id=guest_id,
        staff_id=staff_id,
        message=message_text,
        hotel_slug=hotel_slug  # if your model has this field
    )

    # Trigger Pusher event for real-time update
    pusher_client.trigger(
        f"{hotel_slug}-room-{room_id}-chat",
        "new-message",
        {
            "id": message.id,
            "room": room_id,
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
def get_room_messages(request, hotel_slug, room_id):
    """
    Staff can fetch all messages for a room in a hotel
    """
    messages = RoomMessage.objects.filter(room_id=room_id, hotel_slug=hotel_slug)
    serializer = RoomMessageSerializer(messages, many=True)
    return Response(serializer.data)
