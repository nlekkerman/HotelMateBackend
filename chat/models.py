from django.db import models
from django.utils import timezone


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

    def __str__(self):
        return (f"[{self.timestamp}] Room {self.room.room_number} - "
                f"{self.sender_type}: {self.message[:20]}")
