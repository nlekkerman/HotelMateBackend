from rest_framework import serializers
from .models import Conversation, RoomMessage, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message file attachments"""
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file', 'file_url', 'file_name', 'file_type',
            'file_size', 'file_size_display', 'mime_type',
            'thumbnail', 'thumbnail_url', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_at', 'file_size', 'mime_type']
    
    def get_file_url(self, obj):
        """Get absolute URL for file"""
        if obj.file and hasattr(obj.file, 'url'):
            file_url = obj.file.url
            # Cloudinary URLs are already absolute, don't modify them
            if file_url.startswith('http://') or file_url.startswith('https://'):
                return file_url
            # For local storage, build absolute URI
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(file_url)
            return file_url
        return None
    
    def get_thumbnail_url(self, obj):
        """Get absolute URL for thumbnail"""
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            thumbnail_url = obj.thumbnail.url
            # Cloudinary URLs are already absolute, don't modify them
            if thumbnail_url.startswith('http://') or thumbnail_url.startswith('https://'):
                return thumbnail_url
            # For local storage, build absolute URI
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(thumbnail_url)
            return thumbnail_url
        return None
    
    def get_file_size_display(self, obj):
        """Human-readable file size"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class RoomMessageSerializer(serializers.ModelSerializer):
    room_number = serializers.IntegerField(
        source='room.room_number', read_only=True
    )
    booking_id = serializers.CharField(
        source='booking.booking_id', read_only=True
    )
    staff_name = serializers.SerializerMethodField()
    guest_name = serializers.SerializerMethodField()
    
    # Status fields
    status = serializers.CharField(read_only=True)
    is_read_by_recipient = serializers.SerializerMethodField()
    read_at = serializers.SerializerMethodField()
    
    # Staff info for guest display
    staff_info = serializers.SerializerMethodField()
    
    # Attachments
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    has_attachments = serializers.SerializerMethodField()
    
    # Reply functionality
    reply_to_message = serializers.SerializerMethodField()

    # Add conversation_id for frontend consistency
    conversation_id = serializers.IntegerField(source='conversation.id', read_only=True)

    class Meta:
        model = RoomMessage
        fields = [
            'id', 'conversation', 'conversation_id', 'room', 'room_number',
            'booking', 'booking_id', 'sender_type', 'staff', 'staff_name',
            'guest_name', 'staff_info',
            'message', 'timestamp',
            'status', 'is_read_by_recipient', 'read_at',
            'read_by_staff', 'read_by_guest',
            'staff_read_at', 'guest_read_at', 'delivered_at',
            'staff_display_name', 'staff_role_name',
            'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'reply_to', 'reply_to_message',
            'attachments', 'has_attachments'
        ]
        read_only_fields = [
            'timestamp', 'delivered_at', 'is_edited', 
            'edited_at', 'is_deleted', 'deleted_at'
        ]
    
    def get_staff_name(self, obj):
        """Get staff name, handling system messages appropriately."""
        if obj.sender_type == "system":
            return None  # System messages have no staff name
        elif obj.staff:
            return f"{obj.staff.first_name} {obj.staff.last_name}".strip()
        return None

    def get_guest_name(self, obj):
        """
        Get guest name, preferring current in-house booking data.
        Falls back to room.guests_in_room for legacy compatibility.
        """
        from hotel.models import RoomBooking
        
        # Prefer current in-house booking for the room
        try:
            current_booking = RoomBooking.objects.filter(
                assigned_room=obj.room,
                checked_in_at__isnull=False,
                checked_out_at__isnull=True,
                status__in=['CONFIRMED', 'COMPLETED']  # Active statuses
            ).select_related('hotel').first()
            
            if current_booking:
                primary_name = f"{current_booking.primary_first_name} {current_booking.primary_last_name}".strip()
                if primary_name:
                    return primary_name
        except Exception as e:
            # Log but don't fail - fall back to legacy method
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get guest name from booking for room {obj.room.room_number}: {e}")
        
        # Fallback to legacy room.guests_in_room system
        guest = obj.room.guests_in_room.first()
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
        if obj.sender_type == 'system':
            return None  # System messages have no staff info
        elif obj.sender_type == 'staff' and obj.staff:
            return {
                'name': (obj.staff_display_name or
                         f"{obj.staff.first_name} {obj.staff.last_name}"),
                'role': (obj.staff_role_name or
                         (obj.staff.role.name if obj.staff.role else 'Staff')),
                'department': (obj.staff.department.name if hasattr(obj.staff, 'department') and obj.staff.department else None),
                'profile_image': (obj.staff.profile_image.url
                                  if obj.staff.profile_image else None)
            }
        return None
    
    def get_has_attachments(self, obj):
        """Check if message has attachments"""
        return obj.attachments.exists()
    
    def get_reply_to_message(self, obj):
        """
        Get basic info about the message being replied to,
        including attachment previews
        """
        if obj.reply_to and not obj.reply_to.is_deleted:
            # Get attachment info for preview
            attachments_data = []
            if obj.reply_to.attachments.exists():
                # Limit to 3 previews
                for attachment in obj.reply_to.attachments.all()[:3]:
                    file_url = None
                    if hasattr(attachment.file, 'url'):
                        file_url = attachment.file.url

                    thumbnail_url = None
                    if (attachment.thumbnail and
                            hasattr(attachment.thumbnail, 'url')):
                        thumbnail_url = attachment.thumbnail.url

                    attachments_data.append({
                        'id': attachment.id,
                        'file_name': attachment.file_name,
                        'file_type': attachment.file_type,
                        'file_url': file_url,
                        'thumbnail_url': thumbnail_url,
                        'mime_type': attachment.mime_type
                    })

            return {
                'id': obj.reply_to.id,
                'message': obj.reply_to.message[:100],
                'sender_type': obj.reply_to.sender_type,
                'sender_name': (
                    obj.reply_to.staff_display_name
                    if obj.reply_to.sender_type == 'staff'
                    else 'Guest'
                ),
                'timestamp': obj.reply_to.timestamp,
                'has_attachments': obj.reply_to.attachments.exists(),
                'attachments': attachments_data,
                'attachment_count': obj.reply_to.attachments.count()
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
    guest_id = serializers.SerializerMethodField()
    guest_name = serializers.SerializerMethodField()
    guest_first_name = serializers.SerializerMethodField()
    guest_last_name = serializers.SerializerMethodField()
    
    # CamelCase aliases for frontend compatibility
    lastMessage = serializers.SerializerMethodField()
    roomNumber = serializers.IntegerField(source='room.room_number', read_only=True)
    guestId = serializers.SerializerMethodField()
    guestName = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    unreadCountForStaff = serializers.SerializerMethodField()
    unreadCountForGuest = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',  # Add id field for frontend compatibility
            'conversation_id',
            'room_number', 'roomNumber',  # Both snake_case and camelCase
            'guest_id', 'guestId',  # Both versions
            'guest_name', 'guestName',  # Both versions
            'guest_first_name',
            'guest_last_name',
            'last_message', 'lastMessage',  # Both versions
            'last_message_time',
            'has_unread',
            'unread_count', 'unreadCountForStaff', 'unreadCountForGuest',
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
    
    def get_guest_id(self, obj):
        """Get guest ID, preferring current booking data"""
        from hotel.models import RoomBooking
        
        # Try to get ID from current booking first
        try:
            current_booking = RoomBooking.objects.filter(
                assigned_room=obj.room,
                checked_in_at__isnull=False,
                checked_out_at__isnull=True,
                status__in=['CONFIRMED', 'COMPLETED']
            ).first()
            
            if current_booking:
                # Return booking ID as a fallback - there's no single guest ID in new system
                return current_booking.id
        except Exception:
            pass
        
        # Fallback to legacy guest system
        guest = obj.room.guests_in_room.first()
        return guest.id if guest else None
    
    def get_guest_name(self, obj):
        """
        Get full guest name, preferring current booking data.
        Falls back to room.guests_in_room for legacy compatibility.
        """
        from hotel.models import RoomBooking
        
        # Prefer current in-house booking for the room
        try:
            current_booking = RoomBooking.objects.filter(
                assigned_room=obj.room,
                checked_in_at__isnull=False,
                checked_out_at__isnull=True,
                status__in=['CONFIRMED', 'COMPLETED']
            ).first()
            
            if current_booking:
                primary_name = f"{current_booking.primary_first_name} {current_booking.primary_last_name}".strip()
                if primary_name:
                    return primary_name
        except Exception:
            pass
        
        # Fallback to legacy room.guests_in_room system
        guest = obj.room.guests_in_room.first()
        if guest:
            return f"{guest.first_name} {guest.last_name}".strip()
        return None
    
    def get_guest_first_name(self, obj):
        """Get guest first name, preferring booking data"""
        from hotel.models import RoomBooking
        
        # Try booking data first
        try:
            current_booking = RoomBooking.objects.filter(
                assigned_room=obj.room,
                checked_in_at__isnull=False,
                checked_out_at__isnull=True,
                status__in=['CONFIRMED', 'COMPLETED']
            ).first()
            
            if current_booking and current_booking.primary_first_name:
                return current_booking.primary_first_name
        except Exception:
            pass
        
        # Fallback to legacy system
        guest = obj.room.guests_in_room.first()
        return guest.first_name if guest else None
    
    def get_guest_last_name(self, obj):
        """Get guest last name, preferring booking data"""
        from hotel.models import RoomBooking
        
        # Try booking data first
        try:
            current_booking = RoomBooking.objects.filter(
                assigned_room=obj.room,
                checked_in_at__isnull=False,
                checked_out_at__isnull=True,
                status__in=['CONFIRMED', 'COMPLETED']
            ).first()
            
            if current_booking and current_booking.primary_last_name:
                return current_booking.primary_last_name
        except Exception:
            pass
        
        # Fallback to legacy system
        guest = obj.room.guests_in_room.first()
        return guest.last_name if guest else None
    
    # CamelCase method implementations
    def get_lastMessage(self, obj):
        """CamelCase alias for last_message"""
        return self.get_last_message(obj)
    
    def get_guestId(self, obj):
        """CamelCase alias for guest_id"""
        return self.get_guest_id(obj)
    
    def get_guestName(self, obj):
        """CamelCase alias for guest_name"""
        return self.get_guest_name(obj)
    
    def get_unread_count(self, obj):
        """Get total unread count"""
        return obj.messages.filter(read_by_staff=False, sender_type='guest').count()
    
    def get_unreadCountForStaff(self, obj):
        """Get unread count for staff (guest messages not read by staff)"""
        return obj.messages.filter(read_by_staff=False, sender_type='guest').count()
    
    def get_unreadCountForGuest(self, obj):
        """Get unread count for guest (staff messages not read by guest)"""
        return obj.messages.filter(read_by_guest=False, sender_type='staff').count()


class ConversationUnreadCountSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    unread_count = serializers.IntegerField()
