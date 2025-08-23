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
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)
    conversation_id = serializers.IntegerField(source='id', read_only=True)
    has_unread = serializers.BooleanField(read_only=True)
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'room_number',
            'last_message',
            'has_unread', 
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return last_msg.message  # just return text for sidebar
        return None

class ConversationUnreadCountSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()
