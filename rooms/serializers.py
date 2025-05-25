from rest_framework import serializers
from .models import Room
from guests.serializers import GuestSerializer
class RoomSerializer(serializers.ModelSerializer):
    guests_in_room = GuestSerializer(many=True, read_only=True)
    class Meta:
        model = Room
        
        # or explicitly list fields, e.g.
        fields = ['id', 'room_number', 'guests_in_room', 'guest_id_pin', 'guests', 'is_occupied', 'room_service_qr_code', 'in_room_breakfast_qr_code']
