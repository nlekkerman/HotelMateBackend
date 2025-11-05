"""
Serializers for Staff Conversations
"""
from rest_framework import serializers
from django.db.models import Count, Q
from .models import StaffConversation
from .serializers_staff import StaffBasicSerializer, StaffChatProfileSerializer


class StaffConversationListSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation list view
    Shows conversation preview with last message
    """
    participants_info = StaffBasicSerializer(
        source='participants',
        many=True,
        read_only=True
    )
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    display_avatar = serializers.SerializerMethodField()

    class Meta:
        model = StaffConversation
        fields = [
            'id',
            'hotel',
            'title',
            'display_title',
            'display_avatar',
            'is_group',
            'participants',
            'participants_info',
            'last_message',
            'last_message_time',
            'last_message_preview',
            'unread_count',
            'other_participant',
            'is_archived',
            'has_unread',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields

    def get_last_message(self, obj):
        """Get the last message in conversation"""
        last_msg = obj.messages.filter(is_deleted=False).order_by(
            '-timestamp'
        ).first()
        if last_msg:
            sender_name = (
                f"{last_msg.sender.first_name} "
                f"{last_msg.sender.last_name}"
            ).strip()
            return {
                'id': last_msg.id,
                'message': last_msg.message[:100],
                'sender_id': last_msg.sender.id,
                'sender_name': sender_name,
                'timestamp': last_msg.timestamp,
                'has_attachments': last_msg.attachments.exists()
            }
        return None

    def get_last_message_time(self, obj):
        """Get timestamp of last message"""
        last_msg = obj.messages.order_by('-timestamp').first()
        return last_msg.timestamp if last_msg else obj.updated_at

    def get_last_message_preview(self, obj):
        """Get short preview of last message"""
        last_msg = obj.messages.filter(is_deleted=False).order_by(
            '-timestamp'
        ).first()
        if last_msg:
            if last_msg.attachments.exists() and not last_msg.message.strip():
                return "📎 Sent a file"
            return last_msg.message[:50]
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return 0

        staff = request.user.staff_profile
        return obj.get_unread_count_for_staff(staff)

    def get_other_participant(self, obj):
        """Get the other participant in 1-on-1 conversation"""
        if obj.is_group:
            return None

        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return None

        staff = request.user.staff_profile
        other = obj.get_other_participant(staff)

        if other:
            return {
                'id': other.id,
                'name': f"{other.first_name} {other.last_name}".strip(),
                'avatar': (
                    other.profile_image.url if other.profile_image and
                    hasattr(other.profile_image, 'url') else None
                ),
                'role': other.role.name if other.role else None,
                'department': (
                    other.department.name if other.department else None
                ),
                'is_online': other.is_on_duty
            }
        return None

    def get_display_title(self, obj):
        """Get display title for conversation"""
        if obj.is_group:
            return obj.title or "Group Chat"

        # For 1-on-1, show other participant's name
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return obj.title or "Conversation"

        staff = request.user.staff_profile
        other = obj.get_other_participant(staff)

        if other:
            return f"{other.first_name} {other.last_name}".strip()

        return obj.title or "Conversation"

    def get_display_avatar(self, obj):
        """Get display avatar for conversation"""
        if obj.is_group:
            # Group avatar
            if obj.group_avatar and hasattr(obj.group_avatar, 'url'):
                return obj.group_avatar.url
            return None

        # For 1-on-1, show other participant's avatar
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return None

        staff = request.user.staff_profile
        other = obj.get_other_participant(staff)

        if other and other.profile_image and hasattr(
            other.profile_image, 'url'
        ):
            return other.profile_image.url

        return None


class StaffConversationDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for conversation view
    Includes full participant information
    """
    participants_info = StaffChatProfileSerializer(
        source='participants',
        many=True,
        read_only=True
    )
    created_by_info = StaffBasicSerializer(
        source='created_by',
        read_only=True
    )
    group_avatar_url = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    total_messages = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = StaffConversation
        fields = [
            'id',
            'hotel',
            'title',
            'description',
            'is_group',
            'participants',
            'participants_info',
            'created_by',
            'created_by_info',
            'group_avatar',
            'group_avatar_url',
            'is_archived',
            'archived_at',
            'has_unread',
            'unread_count',
            'total_messages',
            'other_participant',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'is_archived',
            'archived_at',
            'has_unread'
        ]

    def get_group_avatar_url(self, obj):
        """Get group avatar URL"""
        if obj.group_avatar and hasattr(obj.group_avatar, 'url'):
            return obj.group_avatar.url
        return None

    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return 0

        staff = request.user.staff_profile
        return obj.get_unread_count_for_staff(staff)

    def get_total_messages(self, obj):
        """Get total message count"""
        return obj.messages.filter(is_deleted=False).count()

    def get_other_participant(self, obj):
        """Get the other participant in 1-on-1 conversation"""
        if obj.is_group:
            return None

        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return None

        staff = request.user.staff_profile
        other = obj.get_other_participant(staff)

        if other:
            serializer = StaffChatProfileSerializer(other)
            return serializer.data

        return None


class ConversationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new conversations
    """
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = StaffConversation
        fields = [
            'title',
            'description',
            'participant_ids'
        ]

    def validate_participant_ids(self, value):
        """Validate participant IDs"""
        if not value:
            raise serializers.ValidationError(
                "At least one participant is required"
            )

        # Remove duplicates
        unique_ids = list(set(value))

        if len(unique_ids) > 50:
            raise serializers.ValidationError(
                "Maximum 50 participants allowed"
            )

        return unique_ids

    def validate(self, data):
        """Validate conversation data"""
        participant_ids = data.get('participant_ids', [])

        # For group chats, title is recommended
        if len(participant_ids) > 1 and not data.get('title'):
            raise serializers.ValidationError(
                "Group conversations should have a title"
            )

        return data


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating conversation details
    """
    class Meta:
        model = StaffConversation
        fields = [
            'title',
            'description',
            'group_avatar'
        ]

    def validate_title(self, value):
        """Validate title"""
        if value and len(value) > 255:
            raise serializers.ValidationError(
                "Title cannot exceed 255 characters"
            )
        return value


class ConversationParticipantUpdateSerializer(serializers.Serializer):
    """
    Serializer for adding/removing participants
    """
    action = serializers.ChoiceField(
        choices=['add', 'remove'],
        required=True
    )
    staff_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_staff_ids(self, value):
        """Validate staff IDs"""
        if not value:
            raise serializers.ValidationError(
                "At least one staff ID is required"
            )
        return list(set(value))  # Remove duplicates
