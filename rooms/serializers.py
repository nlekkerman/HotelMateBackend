from rest_framework import serializers
from .models import Room

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
        # or explicitly list fields, e.g.
        # fields = ['id', 'room_number', 'guest_id_pin', 'guests', 'is_occupied', 'room_service_qr_code', 'in_room_breakfast_qr_code']
