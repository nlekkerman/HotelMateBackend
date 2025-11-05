from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField


class StaffConversation(models.Model):
    """
    Model to represent a conversation between staff members.
    Can be 1-on-1 or group conversations.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='staff_conversations',
        help_text="Hotel this conversation belongs to"
    )
    participants = models.ManyToManyField(
        'staff.Staff',
        related_name='staff_conversations',
        help_text="Staff members participating in this conversation"
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional conversation title for group chats"
    )
    is_group = models.BooleanField(
        default=False,
        help_text="True if conversation has more than 2 participants"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Staff Conversation'
        verbose_name_plural = 'Staff Conversations'

    def __str__(self):
        if self.title:
            return f"{self.title} ({self.hotel.name})"
        participants = self.participants.all()[:2]
        participant_names = ", ".join(
            [f"{p.first_name} {p.last_name}" for p in participants]
        )
        return f"Conversation: {participant_names}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update is_group based on participant count
        if self.participants.count() > 2:
            if not self.is_group:
                self.is_group = True
                super().save(update_fields=['is_group'])


class StaffChatMessage(models.Model):
    """
    Model to represent a message in a staff conversation.
    """
    conversation = models.ForeignKey(
        StaffConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )
    sender = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='sent_staff_messages',
        help_text="Staff member who sent this message"
    )
    message = models.TextField(
        help_text="Message content"
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the message was sent"
    )

    # Message status tracking
    is_read = models.BooleanField(
        default=False,
        help_text="Whether message has been read by recipients"
    )
    read_by = models.ManyToManyField(
        'staff.Staff',
        blank=True,
        related_name='read_staff_messages',
        help_text="Staff members who have read this message"
    )

    # Message editing and deletion
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Reply functionality
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        help_text="Message this is replying to"
    )

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Staff Chat Message'
        verbose_name_plural = 'Staff Chat Messages'

    def __str__(self):
        return (
            f"[{self.timestamp}] {self.sender.first_name} "
            f"{self.sender.last_name}: {self.message[:30]}"
        )

    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.message = "[Message deleted]"
        self.save()


class StaffChatAttachment(models.Model):
    """
    Model for file attachments in staff chat messages.
    """
    ATTACHMENT_TYPES = (
        ('image', 'Image'),
        ('document', 'Document'),
        ('pdf', 'PDF'),
        ('other', 'Other'),
    )

    message = models.ForeignKey(
        StaffChatMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Message this attachment belongs to"
    )
    file = CloudinaryField(
        "staff_chat_attachment",
        folder="staff_chat_attachments",
        resource_type="auto"
    )
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPES,
        default='other'
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
        null=True,
        blank=True
    )
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Staff Chat Attachment'
        verbose_name_plural = 'Staff Chat Attachments'

    def __str__(self):
        return (
            f"{self.file_name} ({self.get_file_type_display()}) "
            f"- {self.message.sender.first_name}"
        )
