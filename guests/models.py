from django.db import models

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    room = models.ForeignKey('rooms.Room', related_name='guests_in_room', on_delete=models.SET_NULL, null=True, blank=True)
    days_booked = models.PositiveIntegerField(default=1)  # The number of days the guest has booked
    check_in_date = models.DateField(null=True, blank=True)  # The date the guest checked in
    check_out_date = models.DateField(null=True, blank=True)  # The date the guest checked out
    id_pin = models.CharField(max_length=4, unique=True, null=True, blank=True)  # Unique PIN for the guest
    phone_number = models.CharField(max_length=15, null=True, blank=True)  # Optional phone number field
    def __str__(self):
        return f"{self.first_name} {self.last_name}"