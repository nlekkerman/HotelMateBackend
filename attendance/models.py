from django.db import models

class StaffFace(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='staff_faces'
    )
    staff = models.OneToOneField(
        'staff.Staff',
        on_delete=models.CASCADE,
        related_name="face_data"
    )
    image = models.ImageField(upload_to="staff_faces/")
    encoding = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face data for {self.staff.first_name} {self.staff.last_name} @ {self.hotel.slug}"


class ClockLog(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='clock_logs'
    )
    staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.CASCADE
    )
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    verified_by_face = models.BooleanField(default=True)
    location_note = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.staff} @ {self.hotel.slug} - In: {self.time_in} | Out: {self.time_out or '---'}"
