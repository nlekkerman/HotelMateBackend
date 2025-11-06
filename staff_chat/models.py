from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
import os


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
    
    # Group chat specific fields
    created_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_staff_conversations',
        help_text="Staff member who created this conversation"
    )
    group_avatar = CloudinaryField(
        "group_avatar",
        folder="staff_chat_groups",
        null=True,
        blank=True,
        help_text="Optional avatar for group conversations"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description for group chats"
    )
    
    # Conversation management
    is_archived = models.BooleanField(
        default=False,
        help_text="Archived conversations are hidden from main list"
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Unread tracking (conversation level flag)
    has_unread = models.BooleanField(
        default=False,
        help_text="Quick flag to show if conversation has any unread messages"
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
    
    @classmethod
    def get_or_create_conversation(cls, hotel, staff_list, title=''):
        """
        Get existing conversation or create new one.
        For 1-on-1: Returns existing conversation between two staff members
        For groups: Returns existing conversation with same participants
        
        Args:
            hotel: Hotel instance
            staff_list: List of Staff instances (including creator)
            title: Optional title for group chats
        
        Returns:
            tuple: (conversation, created)
        """
        from django.db.models import Count
        
        # For 1-on-1 conversations (2 total participants)
        if len(staff_list) == 2:
            # Check if conversation exists between these two staff members
            # First get all non-group conversations with correct count
            conversations = cls.objects.filter(
                hotel=hotel,
                is_group=False
            ).annotate(
                participant_count=Count('participants')
            ).filter(
                participant_count=2
            ).filter(
                participants=staff_list[0]
            ).filter(
                participants=staff_list[1]
            )
            
            if conversations.exists():
                return conversations.first(), False
        
        # For group conversations (3+ participants)
        else:
            # Check if conversation exists with exact same participants
            # Start with conversations that have the right participant count
            conversations = cls.objects.filter(
                hotel=hotel,
                is_group=True
            ).annotate(
                participant_count=Count('participants')
            ).filter(participant_count=len(staff_list))
            
            # Filter to find one with exact same participants
            for conv in conversations:
                conv_participants = set(conv.participants.all())
                if conv_participants == set(staff_list):
                    return conv, False
        
        # Create new conversation
        is_group = len(staff_list) > 2
        conversation = cls.objects.create(
            hotel=hotel,
            title=title,
            is_group=is_group,
            created_by=staff_list[0],  # First in list is creator
            has_unread=False
        )
        
        # Add all participants
        conversation.participants.add(*staff_list)
        
        return conversation, True

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update is_group based on participant count
        if self.participants.count() > 2:
            if not self.is_group:
                self.is_group = True
                super().save(update_fields=['is_group'])
        elif self.participants.count() == 2:
            if self.is_group:
                self.is_group = False
                super().save(update_fields=['is_group'])
    
    def archive(self):
        """Archive this conversation"""
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=['is_archived', 'archived_at'])
    
    def unarchive(self):
        """Unarchive this conversation"""
        self.is_archived = False
        self.archived_at = None
        self.save(update_fields=['is_archived', 'archived_at'])
    
    def get_other_participant(self, staff):
        """Get the other participant in a 1-on-1 conversation"""
        if self.is_group:
            return None
        participants = self.participants.exclude(id=staff.id)
        return participants.first() if participants.exists() else None
    
    def get_unread_count_for_staff(self, staff):
        """Get unread message count for a specific staff member"""
        return self.messages.filter(
            is_deleted=False
        ).exclude(sender=staff).exclude(read_by=staff).count()


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
    STATUS_CHOICES = (
        ("pending", "Pending"),      # Message sending in progress
        ("delivered", "Delivered"),   # Message reached server
        ("read", "Read")              # Message has been read by all recipients
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="delivered"
    )
    delivered_at = models.DateTimeField(default=timezone.now)
    
    # Read tracking (per participant)
    is_read = models.BooleanField(
        default=False,
        help_text="True when ALL participants have read the message"
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
    
    # Mentions (for @staff notifications)
    mentions = models.ManyToManyField(
        'staff.Staff',
        blank=True,
        related_name='mentioned_in_staff_messages',
        help_text="Staff members mentioned in this message"
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
        
        # Check if message had attachments
        has_attachments = self.attachments.exists()
        had_text = bool(self.message and self.message.strip())
        
        if has_attachments and not had_text:
            self.message = "[File deleted]"
        elif has_attachments and had_text:
            self.message = "[Message and file(s) deleted]"
        else:
            self.message = "[Message deleted]"
        
        self.save()
    
    def mark_as_read_by(self, staff):
        """Mark message as read by a specific staff member"""
        if staff != self.sender and not self.read_by.filter(id=staff.id).exists():
            self.read_by.add(staff)
            
            # Check if ALL participants (except sender) have read
            all_participants = self.conversation.participants.exclude(id=self.sender.id)
            if self.read_by.count() >= all_participants.count():
                self.is_read = True
                self.status = 'read'
                self.save(update_fields=['is_read', 'status'])
            
            return True
        return False
    
    def get_read_by_list(self):
        """Get list of staff members who read this message"""
        return list(self.read_by.all())
    
    def is_read_by(self, staff):
        """Check if message was read by specific staff member"""
        return self.read_by.filter(id=staff.id).exists()


def validate_file_size(file):
    """Validate file size - max 50MB"""
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size > max_size:
        size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f'File size cannot exceed 50MB. '
            f'Current size: {size_mb:.2f}MB'
        )


def validate_file_extension(file):
    """Validate file extension"""
    allowed_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
        '.pdf',  # PDF
        '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'  # Documents
    ]
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f'File type "{ext}" is not allowed. '
            f'Allowed types: {", ".join(allowed_extensions)}'
        )


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
        help_text="File size in bytes"
    )
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Optional thumbnail for images
    thumbnail = models.ImageField(
        upload_to='staff_chat_thumbnails/',
        null=True,
        blank=True,
        help_text="Auto-generated thumbnail for images"
    )
    
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
    
    def get_file_extension(self):
        """Get file extension"""
        return os.path.splitext(self.file_name)[1].lower()
    
    def is_image(self):
        """Check if file is an image"""
        return self.file_type == 'image'
    
    def save(self, *args, **kwargs):
        # Auto-detect file type based on extension
        if not self.file_type or self.file_type == 'other':
            ext = self.get_file_extension()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                self.file_type = 'image'
            elif ext == '.pdf':
                self.file_type = 'pdf'
            elif ext in ['.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv']:
                self.file_type = 'document'
        
        super().save(*args, **kwargs)


class StaffMessageReaction(models.Model):
    """
    Model for emoji reactions to staff chat messages.
    """
    REACTION_CHOICES = (
        ('👍', 'Thumbs Up'),
        ('❤️', 'Heart'),
        ('😊', 'Smile'),
        ('😂', 'Laugh'),
        ('😮', 'Wow'),
        ('😢', 'Sad'),
        ('🎉', 'Party'),
        ('🔥', 'Fire'),
        ('✅', 'Check'),
        ('👏', 'Clap'),
    )
    
    message = models.ForeignKey(
        StaffChatMessage,
        on_delete=models.CASCADE,
        related_name='reactions',
        help_text="Message this reaction belongs to"
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='staff_message_reactions',
        help_text="Staff member who reacted"
    )
    emoji = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        help_text="Emoji reaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Only one reaction per user per message
        unique_together = ('message', 'staff')
        ordering = ['created_at']
        verbose_name = 'Staff Message Reaction'
        verbose_name_plural = 'Staff Message Reactions'
    
    def __str__(self):
        return (
            f"{self.emoji} by {self.staff.first_name} "
            f"on message {self.message.id}"
        )
