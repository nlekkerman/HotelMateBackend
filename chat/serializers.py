from rest_framework import serializers
from .models import Conversation, RoomMessage


class RoomMessageSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(
        source='room.room_number', read_only=True
    )
    staff_name = serializers.CharField(
        source='staff.__str__', read_only=True
    )
    guest_name = serializers.SerializerMethodField()
    
    # Status fields
    status = serializers.CharField(read_only=True)
    is_read_by_recipient = serializers.SerializerMethodField()
    read_at = serializers.SerializerMethodField()
    
    # Staff info for guest display
    staff_info = serializers.SerializerMethodField()

    class Meta:
        model = RoomMessage
        fields = [
            'id', 'conversation', 'room', 'room_number',
            'sender_type', 'staff', 'staff_name',
            'guest_name', 'staff_info',
            'message', 'timestamp',
            'status', 'is_read_by_recipient', 'read_at',
            'read_by_staff', 'read_by_guest',
            'staff_read_at', 'guest_read_at', 'delivered_at',
            'staff_display_name', 'staff_role_name'
        ]
        read_only_fields = ['timestamp', 'delivered_at']

    def get_guest_name(self, obj):
        # Since only one guest per room, grab the first (if any)
        guest = obj.room.guests.first()  # ManyToManyField
        if guest:
            return f"{guest.first_name} {guest.last_name}".strip()
        return None

    def get_is_read_by_recipient(self, obj):
        """Check if message was read by the intended recipient"""
        if obj.sender_type == "guest":
            return obj.read_by_staff
        else:
            return obj.read_by_guest

    def get_read_at(self, obj):
        """Get when message was read by recipient"""
        if obj.sender_type == "guest":
            return obj.staff_read_at
        else:
            return obj.guest_read_at

    def get_staff_info(self, obj):
        """Return staff info for guest-facing display"""
        if obj.sender_type == 'staff' and obj.staff:
            return {
                'name': (obj.staff_display_name or
                         f"{obj.staff.first_name} {obj.staff.last_name}"),
                'role': (obj.staff_role_name or
                         (obj.staff.role.name if obj.staff.role else 'Staff')),
                'profile_image': (obj.staff.profile_image.url
                                  if obj.staff.profile_image else None)
            }
        return None


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    room_number = serializers.IntegerField(
        source='room.room_number', read_only=True
    )
    conversation_id = serializers.IntegerField(source='id', read_only=True)
    has_unread = serializers.BooleanField(read_only=True)
    
    # Guest information
    guest_name = serializers.SerializerMethodField()
    guest_first_name = serializers.SerializerMethodField()
    guest_last_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'room_number',
            'guest_name',
            'guest_first_name',
            'guest_last_name',
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
    
    def get_guest_name(self, obj):
        """Get full guest name"""
        guest = obj.room.guests.first()
        if guest:
            return f"{guest.first_name} {guest.last_name}".strip()
        return None
    
    def get_guest_first_name(self, obj):
        """Get guest first name"""
        guest = obj.room.guests.first()
        return guest.first_name if guest else None
    
    def get_guest_last_name(self, obj):
        """Get guest last name"""
        guest = obj.room.guests.first()
        return guest.last_name if guest else None


class ConversationUnreadCountSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()
