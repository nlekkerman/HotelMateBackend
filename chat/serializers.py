from rest_framework import serializers
from .models import Conversation, RoomMessage


class RoomMessageSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)
    staff_name = serializers.CharField(source='staff.__str__', read_only=True)
    guest_name = serializers.SerializerMethodField()  # <-- add guest name

    class Meta:
        model = RoomMessage
        fields = [
            'id', 'conversation', 'room', 'room_number',
            'sender_type', 'staff', 'staff_name',
            'guest_name',  # include guest name
            'message', 'timestamp', 'read_by_staff'
        ]
        read_only_fields = ['timestamp']

    def get_guest_name(self, obj):
        # Since only one guest per room, grab the first (if any)
        guest = obj.room.guests.first()  # ManyToManyField
        if guest:
            return f"{guest.first_name} {guest.last_name}".strip()
        return None


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField() 
    room_number = serializers.IntegerField(source='room.room_number', read_only=True)
    conversation_id = serializers.IntegerField(source='id', read_only=True)
    has_unread = serializers.BooleanField(read_only=True)
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'room_number',
            'last_message',
            'last_message_time',
            'has_unread',
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return last_msg.message  # just return text for sidebar
        return None
    
    def get_last_message_time(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return last_msg.timestamp
        return None

class ConversationUnreadCountSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()
