from django.db import models
from django.utils import timezone

class RoomMessage(models.Model):
    room = models.ForeignKey('rooms.Room', on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=100)  # could be 'guest' or staff username
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read_by_staff = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.timestamp}] {self.room}: {self.message[:20]}"
