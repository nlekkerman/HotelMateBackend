from rest_framework import serializers
from .models import Conversation, RoomMessage

class RoomMessageSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)
    staff_name = serializers.CharField(source='staff.__str__', read_only=True)  # show staff name if available

    class Meta:
        model = RoomMessage
        fields = [
            'id',
            'conversation',
            'room',
            'room_number',
            'sender_type',
            'staff',        # staff id (if sender_type == "staff")
            'staff_name',   # human-readable staff name
            'message',
            'timestamp',
            'read_by_staff'
        ]
        read_only_fields = ['timestamp']


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'room',
            'participants',
            'created_at',
            'updated_at',
            'last_message',
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return RoomMessageSerializer(last_msg).data
        return None

    def get_participants(self, obj):
        return [staff.name for staff in obj.participants_staff.all()]
