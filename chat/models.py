from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from cloudinary.models import CloudinaryField
import uuid
import os


# Conversation model
class Conversation(models.Model):
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True, blank=True  # Optional if you want direct staff DMs later
    )
    participants_staff = models.ManyToManyField(
        'staff.Staff',
        blank=True,
        related_name='conversations'
    )
    has_unread = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.room:
            return f"Conversation in Room {self.room.room_number}"
        return f"Conversation {self.id}"


# RoomMessage model
class RoomMessage(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='messages'
    )
    booking = models.ForeignKey(
        'hotel.RoomBooking',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='chat_messages',
        help_text="Booking associated with this message (for guest messages)"
    )
    sender_type = models.CharField(
        max_length=10,
        choices=(("guest", "Guest"), ("staff", "Staff"), ("system", "System")),
        default="guest"
    )
    staff = models.ForeignKey(
        'staff.Staff',   # replace with your actual staff/user model
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='room_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Staff display info for guest-facing messages
    staff_display_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Staff name shown to guest (e.g., 'John Smith')"
    )
    staff_role_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Staff role for guest display (e.g., 'Receptionist')"
    )
    
    # Message status tracking
    status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),      # Message sending in progress
            ("delivered", "Delivered"),   # Message reached server
            ("read", "Read")              # Message has been read
        ),
        default="delivered"
    )
    
    # Detailed read tracking
    read_by_staff = models.BooleanField(default=False)
    read_by_guest = models.BooleanField(default=False)
    staff_read_at = models.DateTimeField(null=True, blank=True)
    guest_read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery confirmation
    delivered_at = models.DateTimeField(default=timezone.now)
    
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

    def save(self, *args, **kwargs):
        # Auto-populate staff display info when staff sends message
        if self.staff and self.sender_type == "staff":
            full_name = f"{self.staff.first_name} {self.staff.last_name}"
            self.staff_display_name = full_name.strip()
            if self.staff.role:
                self.staff_role_name = self.staff.role.name
        super().save(*args, **kwargs)
    
    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        
        # Check if message had attachments
        has_attachments = self.attachments.exists()
        had_text = bool(self.message and self.message.strip())
        
        if has_attachments and not had_text:
            # Only files, no text
            self.message = "[File deleted]"
        elif has_attachments and had_text:
            # Both text and files
            self.message = "[Message and file(s) deleted]"
        else:
            # Only text message
            self.message = "[Message deleted]"
        
        self.save()

    def __str__(self):
        return (f"[{self.timestamp}] Room {self.room.room_number} - "
                f"{self.sender_type}: {self.message[:20]}")


class GuestConversationParticipant(models.Model):
    """
    Track staff members who have joined guest conversations.
    Used for system join messages and conversation history.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='guest_participants'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name='guest_conversation_participations'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('conversation', 'staff'),)
        ordering = ['joined_at']
        verbose_name = 'Guest Conversation Participant'
        verbose_name_plural = 'Guest Conversation Participants'
    
    def __str__(self):
        return f"{self.staff} joined conversation {self.conversation.id}"


def message_attachment_path(instance, filename):
    """Generate upload path for message attachments"""
    # Organize by hotel -> room -> date
    date_str = timezone.now().strftime('%Y/%m/%d')
    # Sanitize filename to prevent issues
    import re
    safe_filename = re.sub(r'[^\w\s.-]', '', filename)
    return f'chat/{instance.message.room.hotel.slug}/room_{instance.message.room.room_number}/{date_str}/{safe_filename}'


def validate_file_size(file):
    """Validate file size - max 50MB"""
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size > max_size:
        raise ValidationError(f'File size cannot exceed 50MB. Current size: {file.size / (1024*1024):.2f}MB')


def validate_file_extension(file):
    """Validate file extension"""
    allowed_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
        '.pdf',  # PDF
        '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'  # Documents
    ]
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'File type "{ext}" is not allowed. Allowed types: {", ".join(allowed_extensions)}')


class MessageAttachment(models.Model):
    """
    File attachments for chat messages.
    Supports images, PDFs, and common document formats.
    """
    ATTACHMENT_TYPES = (
        ('image', 'Image'),
        ('document', 'Document'),
        ('pdf', 'PDF'),
        ('other', 'Other'),
    )
    
    message = models.ForeignKey(
        RoomMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = CloudinaryField(
        "attachment",
        folder="chat_attachments",
        resource_type="auto",
        validators=[validate_file_size, validate_file_extension]
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
        upload_to=message_attachment_path,
        null=True,
        blank=True,
        help_text="Auto-generated thumbnail for images"
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'
    
    def __str__(self):
        return f"{self.file_name} ({self.get_file_type_display()})"
    
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
