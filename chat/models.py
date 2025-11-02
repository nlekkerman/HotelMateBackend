from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


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
    sender_type = models.CharField(
        max_length=10,
        choices=(("guest", "Guest"), ("staff", "Staff")),
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

    def save(self, *args, **kwargs):
        # Auto-populate staff display info when staff sends message
        if self.staff and self.sender_type == "staff":
            full_name = f"{self.staff.first_name} {self.staff.last_name}"
            self.staff_display_name = full_name.strip()
            if self.staff.role:
                self.staff_role_name = self.staff.role.name
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"[{self.timestamp}] Room {self.room.room_number} - "
                f"{self.sender_type}: {self.message[:20]}")


class GuestChatSession(models.Model):
    """
    Tracks anonymous guest chat sessions for push notifications
    and staff identification
    """
    session_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Unique token stored in guest's browser"
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='guest_sessions'
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='guest_chat_sessions'
    )

    # Track which staff member is currently handling this guest
    current_staff_handler = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_guest_sessions',
        help_text="Staff member currently handling this conversation"
    )

    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Session expires after guest checkout or 7 days"
    )
    is_active = models.BooleanField(default=True)

    # Device info for better tracking
    user_agent = models.TextField(blank=True, null=True)
    last_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"Session {self.session_token} - Room {self.room.room_number}"

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        # Auto-set expiration to 7 days if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'Guest Chat Session'
        verbose_name_plural = 'Guest Chat Sessions'
