from rest_framework import serializers
from .models import (
    StaffConversation, StaffChatMessage, StaffChatAttachment
)
from staff.models import Staff, Department, Role
from hotel.models import Hotel


class StaffMemberSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for staff member info in chat context
    """
    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(
        source='department.name',
        read_only=True,
        allow_null=True
    )
    role_name = serializers.CharField(
        source='role.name',
        read_only=True,
        allow_null=True
    )
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'department_name', 'role_name',
            'is_on_duty', 'profile_image_url'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return str(obj.profile_image.url)
        return None


class StaffListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing all staff members (for chat UI)
    """
    full_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number',
            'department', 'role',
            'is_active', 'is_on_duty',
            'hotel_name', 'profile_image_url'
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_department(self, obj):
        if obj.department:
            return {
                'id': obj.department.id,
                'name': obj.department.name,
                'slug': obj.department.slug
            }
        return None

    def get_role(self, obj):
        if obj.role:
            return {
                'id': obj.role.id,
                'name': obj.role.name,
                'slug': obj.role.slug
            }
        return None

    def get_profile_image_url(self, obj):
        if obj.profile_image:
            return str(obj.profile_image.url)
        return None


class StaffChatAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for chat message attachments
    """
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffChatAttachment
        fields = [
            'id', 'file_name', 'file_type', 'file_size',
            'mime_type', 'file_url', 'uploaded_at'
        ]

    def get_file_url(self, obj):
        if obj.file:
            return str(obj.file.url)
        return None


class StaffChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for staff chat messages
    """
    sender = StaffMemberSerializer(read_only=True)
    attachments = StaffChatAttachmentSerializer(many=True, read_only=True)
    reply_to_message = serializers.SerializerMethodField()
    read_by_staff = serializers.SerializerMethodField()

    class Meta:
        model = StaffChatMessage
        fields = [
            'id', 'conversation', 'sender', 'message',
            'timestamp', 'is_read', 'read_by', 'read_by_staff',
            'is_edited', 'edited_at',
            'is_deleted', 'deleted_at',
            'reply_to', 'reply_to_message',
            'attachments'
        ]
        read_only_fields = [
            'id', 'timestamp', 'is_edited', 'edited_at',
            'is_deleted', 'deleted_at'
        ]

    def get_reply_to_message(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'sender': f"{obj.reply_to.sender.first_name} "
                         f"{obj.reply_to.sender.last_name}",
                'message': obj.reply_to.message[:100],
                'timestamp': obj.reply_to.timestamp
            }
        return None

    def get_read_by_staff(self, obj):
        """Return list of staff who have read this message"""
        return [
            {
                'id': staff.id,
                'name': f"{staff.first_name} {staff.last_name}"
            }
            for staff in obj.read_by.all()
        ]


class StaffConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for staff conversations
    """
    participants = StaffMemberSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Staff.objects.all(),
        write_only=True,
        source='participants'
    )
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = StaffConversation
        fields = [
            'id', 'hotel', 'hotel_name',
            'participants', 'participant_ids',
            'title', 'is_group',
            'created_at', 'updated_at',
            'last_message', 'unread_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_group']

    def get_last_message(self, obj):
        """Get the most recent message in this conversation"""
        last_msg = obj.messages.filter(
            is_deleted=False
        ).order_by('-timestamp').first()

        if last_msg:
            return {
                'id': last_msg.id,
                'sender': f"{last_msg.sender.first_name} "
                         f"{last_msg.sender.last_name}",
                'message': last_msg.message[:100],
                'timestamp': last_msg.timestamp,
                'is_read': last_msg.is_read
            }
        return None

    def get_unread_count(self, obj):
        """
        Get unread message count for the current user
        Requires user to be passed in context
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'staff_profile'):
            staff = request.user.staff_profile
            return obj.messages.filter(
                is_deleted=False,
                is_read=False
            ).exclude(sender=staff).count()
        return 0


class StaffConversationDetailSerializer(StaffConversationSerializer):
    """
    Detailed serializer for a single conversation with all messages
    """
    messages = StaffChatMessageSerializer(many=True, read_only=True)

    class Meta(StaffConversationSerializer.Meta):
        fields = StaffConversationSerializer.Meta.fields + ['messages']
