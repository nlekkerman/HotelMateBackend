from django.db import models
from django.utils import timezone
from hotel.models import Hotel
from rooms.models import Room
from staff.models import Staff
from cloudinary.models import CloudinaryField


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    location_note = models.CharField(max_length=255, blank=True, help_text="E.g., Lobby, Gym, Kitchen")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    reported_by = models.ForeignKey(
        Staff,
        related_name='reported_maintenance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    accepted_by = models.ForeignKey(
        Staff,
        related_name='accepted_maintenance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        loc = self.room.room_number if self.room else self.location_note
        return f"{self.title} ({loc}) - {self.status}"


class MaintenanceComment(models.Model):
    request = models.ForeignKey(MaintenanceRequest, related_name='comments', on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.staff} on {self.request}"


class MaintenancePhoto(models.Model):
    request = models.ForeignKey(MaintenanceRequest, related_name='photos', on_delete=models.CASCADE)
    image = CloudinaryField("image")
    uploaded_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.request} by {self.uploaded_by}"
