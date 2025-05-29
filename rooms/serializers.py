from rest_framework import serializers
from .models import Room
from hotel.models import Hotel
from guests.serializers import GuestSerializer

class RoomSerializer(serializers.ModelSerializer):
    guests_in_room = GuestSerializer(many=True, read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())  # or use a nested serializer if you want details

    class Meta:
        model = Room
        fields = [
            'id',
            'hotel',
            'room_number',
            'guests_in_room',
            'guest_id_pin',
            'guests',
            'is_occupied',
            'room_service_qr_code',
            'in_room_breakfast_qr_code'
        ]
