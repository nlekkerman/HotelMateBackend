"""
Serializers for Staff Chat Messages
"""
from rest_framework import serializers
from django.utils import timezone
from .models import StaffChatMessage, StaffMessageReaction
from .serializers_staff import StaffBasicSerializer
from .serializers_attachments import StaffChatAttachmentSerializer


class MessageReactionSerializer(serializers.ModelSerializer):
    """
    Serializer for message reactions
    """
    staff_name = serializers.SerializerMethodField()
    staff_avatar = serializers.SerializerMethodField()

    class Meta:
        model = StaffMessageReaction
        fields = [
            'id',
            'emoji',
            'staff',
            'staff_name',
            'staff_avatar',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_staff_name(self, obj):
        """Get reactor's name"""
        return f"{obj.staff.first_name} {obj.staff.last_name}".strip()

    def get_staff_avatar(self, obj):
        """Get reactor's avatar"""
        if obj.staff.profile_image and hasattr(
            obj.staff.profile_image, 'url'
        ):
            return obj.staff.profile_image.url
        return None


class ReplyToMessageSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for replied-to messages
    Prevents infinite nesting
    """
    sender_name = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    attachments_preview = serializers.SerializerMethodField()

    class Meta:
        model = StaffChatMessage
        fields = [
            'id',
            'message',
            'sender',
            'sender_name',
            'sender_avatar',
            'timestamp',
            'is_deleted',
            'attachments_preview'
        ]
        read_only_fields = fields

    def get_sender_name(self, obj):
        """Get sender's name"""
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip()

    def get_sender_avatar(self, obj):
        """Get sender's avatar"""
        if obj.sender.profile_image and hasattr(
            obj.sender.profile_image, 'url'
        ):
            return obj.sender.profile_image.url
        return None

    def get_attachments_preview(self, obj):
        """Get preview of attachments (first 3)"""
        attachments = obj.attachments.all()[:3]
        if not attachments:
            return []

        previews = []
        for att in attachments:
            previews.append({
                'id': att.id,
                'file_name': att.file_name,
                'file_type': att.file_type,
                'file_url': (
                    att.file.url if att.file and
                    hasattr(att.file, 'url') else None
                ),
                'thumbnail_url': (
                    att.thumbnail.url if att.thumbnail and
                    hasattr(att.thumbnail, 'url') else None
                )
            })
        return previews


class StaffChatMessageSerializer(serializers.ModelSerializer):
    """
    Full serializer for staff chat messages
    """
    sender_info = StaffBasicSerializer(source='sender', read_only=True)
    sender_name = serializers.SerializerMethodField()
    attachments = StaffChatAttachmentSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reply_to_message = ReplyToMessageSerializer(
        source='reply_to',
        read_only=True
    )

    # Read tracking
    is_read_by_current_user = serializers.SerializerMethodField()
    read_by_list = serializers.SerializerMethodField()
    read_by_count = serializers.SerializerMethodField()

    # Mentioned staff
    mentioned_staff = StaffBasicSerializer(
        source='mentions',
        many=True,
        read_only=True
    )

    # Computed fields
    has_attachments = serializers.SerializerMethodField()
    reaction_summary = serializers.SerializerMethodField()

    class Meta:
        model = StaffChatMessage
        fields = [
            'id',
            'conversation',
            'sender',
            'sender_info',
            'sender_name',
            'message',
            'timestamp',
            'status',
            'delivered_at',
            'is_read',
            'read_by',
            'read_by_list',
            'read_by_count',
            'is_read_by_current_user',
            'is_edited',
            'edited_at',
            'is_deleted',
            'deleted_at',
            'reply_to',
            'reply_to_message',
            'attachments',
            'has_attachments',
            'reactions',
            'reaction_summary',
            'mentions',
            'mentioned_staff'
        ]
        read_only_fields = [
            'timestamp',
            'delivered_at',
            'is_read',
            'is_edited',
            'edited_at',
            'is_deleted',
            'deleted_at'
        ]

    def get_sender_name(self, obj):
        """Get sender's full name"""
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip()

    def get_is_read_by_current_user(self, obj):
        """Check if current user has read this message"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'staff_profile'):
            return False

        staff = request.user.staff_profile

        # Sender always "read" their own messages
        if obj.sender.id == staff.id:
            return True

        return obj.read_by.filter(id=staff.id).exists()

    def get_read_by_list(self, obj):
        """Get list of staff who read this message"""
        read_by_staff = obj.read_by.all()
        return [
            {
                'id': staff.id,
                'name': f"{staff.first_name} {staff.last_name}".strip(),
                'avatar': (
                    staff.profile_image.url if staff.profile_image and
                    hasattr(staff.profile_image, 'url') else None
                )
            }
            for staff in read_by_staff
        ]

    def get_read_by_count(self, obj):
        """Get count of staff who read this message"""
        return obj.read_by.count()

    def get_has_attachments(self, obj):
        """Check if message has attachments"""
        return obj.attachments.exists()

    def get_reaction_summary(self, obj):
        """
        Get summary of reactions grouped by emoji
        Format: {'👍': 3, '❤️': 2, ...}
        """
        reactions = obj.reactions.all()
        summary = {}
        for reaction in reactions:
            emoji = reaction.emoji
            if emoji in summary:
                summary[emoji] += 1
            else:
                summary[emoji] = 1
        return summary


class MessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new messages
    """
    reply_to = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = StaffChatMessage
        fields = [
            'conversation',
            'message',
            'reply_to'
        ]

    def validate_message(self, value):
        """Validate message is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Message cannot be empty"
            )
        return value.strip()

    def validate_reply_to(self, value):
        """Validate reply_to message exists"""
        if value:
            try:
                message = StaffChatMessage.objects.get(id=value)
                # Ensure reply is in same conversation
                conversation_id = self.initial_data.get('conversation')
                if message.conversation.id != conversation_id:
                    raise serializers.ValidationError(
                        "Reply must be to a message in the same conversation"
                    )
                if message.is_deleted:
                    raise serializers.ValidationError(
                        "Cannot reply to a deleted message"
                    )
            except StaffChatMessage.DoesNotExist:
                raise serializers.ValidationError(
                    "Reply target message does not exist"
                )
        return value


class MessageUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating/editing messages
    """
    class Meta:
        model = StaffChatMessage
        fields = ['message']

    def validate_message(self, value):
        """Validate message is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Message cannot be empty"
            )
        return value.strip()

    def update(self, instance, validated_data):
        """Update message and mark as edited"""
        instance.message = validated_data.get('message', instance.message)
        instance.is_edited = True
        instance.edited_at = timezone.now()
        instance.save()
        return instance


class MessageReactionCreateSerializer(serializers.Serializer):
    """
    Serializer for adding a reaction to a message
    """
    emoji = serializers.ChoiceField(
        choices=[
            '👍', '❤️', '😊', '😂', '😮',
            '😢', '🎉', '🔥', '✅', '👏'
        ]
    )

    def validate_emoji(self, value):
        """Validate emoji is allowed"""
        allowed_emojis = [
            '👍', '❤️', '😊', '😂', '😮',
            '😢', '🎉', '🔥', '✅', '👏'
        ]
        if value not in allowed_emojis:
            raise serializers.ValidationError(
                f"Emoji '{value}' is not allowed"
            )
        return value
