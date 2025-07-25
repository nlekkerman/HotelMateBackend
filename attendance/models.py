from django.db import models

class StaffFace(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='staff_faces')
    staff = models.OneToOneField('staff.Staff', on_delete=models.CASCADE, related_name="face_data")
    image = models.ImageField(upload_to="staff_faces/")
    encoding = models.JSONField(
        help_text="128‑dim face descriptor (list of floats)",
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Face data for {self.staff} @ {self.hotel.slug}"


class ClockLog(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='clock_logs')
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    verified_by_face = models.BooleanField(default=True)
    location_note = models.CharField(max_length=255, blank=True, null=True)
    auto_clock_out = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.staff} @ {self.hotel.slug} - In: {self.time_in} | Out: {self.time_out or '---'}"

    class Meta:
        ordering = ['-time_in']


class RosterPeriod(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, help_text="e.g., 'Week 29 Roster'")
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey('staff.Staff', on_delete=models.SET_NULL, null=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.hotel.name} | {self.title}"


class StaffRoster(models.Model):
    SHIFT_TYPES = [
        ('morning', 'Morning'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('split', 'Split'),
        ('custom', 'Custom'),
    ]

    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE, related_name='staff_rosters')
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='roster_entries')
    department = models.CharField(max_length=50)
    period = models.ForeignKey('RosterPeriod', on_delete=models.CASCADE, related_name='entries', null=True)

    shift_date = models.DateField()
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    break_start = models.TimeField(blank=True, null=True)
    break_end = models.TimeField(blank=True, null=True)

    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, default='custom')
    is_split_shift = models.BooleanField(default=False)
    is_night_shift = models.BooleanField(default=False)
    expected_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    approved_by = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_rosters'
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Allow multiple shifts on the same date, but unique per start time
        unique_together = ('staff', 'shift_date', 'shift_start')
        ordering = ['shift_date', 'shift_start']

    def __str__(self):
        return f"{self.staff} on {self.shift_date} ({self.shift_start}-{self.shift_end})"

class StaffAvailability(models.Model):
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    available = models.BooleanField(default=True)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.staff} | {self.date} - {'Available' if self.available else 'Unavailable'}"


class ShiftTemplate(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_night = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.hotel.name} | {self.name} ({self.start_time}-{self.end_time})"


class RosterRequirement(models.Model):
    period = models.ForeignKey('RosterPeriod', on_delete=models.CASCADE, related_name='requirements')
    department = models.CharField(max_length=50)
    role = models.CharField(max_length=50)
    date = models.DateField()
    required_count = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.department} | {self.role} on {self.date}: {self.required_count} needed"
