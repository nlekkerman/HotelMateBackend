from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

class Guest(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    room = models.ForeignKey('rooms.Room', related_name='guests_in_room', on_delete=models.SET_NULL, null=True, blank=True)
    days_booked = models.PositiveIntegerField(default=1)  # The number of days the guest has booked
    check_in_date = models.DateField(null=True, blank=True)  # The date the guest checked in
    check_out_date = models.DateField(null=True, blank=True)  # The date the guest checked out
    id_pin = models.CharField(max_length=4, unique=True, null=True, blank=True)  # Unique PIN for the guest
    
    def delete(self, *args, **kwargs):
        # Set room to unoccupied if this guest is assigned a room
        if self.room:
            self.room.is_occupied = False
            self.room.save()
        super().delete(*args, **kwargs)
    
    @property
    def in_house(self):
        today = timezone.now().date()
        return self.check_in_date and self.check_out_date and self.check_in_date <= today <= self.check_out_date

 
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

