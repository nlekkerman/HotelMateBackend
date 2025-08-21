from rest_framework import serializers
from .models import RoomMessage

class RoomMessageSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)

    class Meta:
        model = RoomMessage
        fields = ['id', 'room', 'room_number', 'sender', 'message', 'timestamp', 'read_by_staff']
        read_only_fields = ['timestamp']
