from django.db import models
from cloudinary.models import CloudinaryField


class StaffFace(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE, related_name='staff_faces'
    )
    staff = models.OneToOneField(
        'staff.Staff', on_delete=models.CASCADE, related_name="face_data"
    )
    image = CloudinaryField(
        'face_image',
        folder='staff_faces',
        null=True,
        blank=True,
        help_text="Face image stored in Cloudinary cloud storage"
    )
    encoding = models.JSONField(
        help_text="128‑dim face descriptor (list of floats)",
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit and security fields
    consent_given = models.BooleanField(
        default=True,
        help_text="Whether staff member consented to face data collection"
    )
    registered_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_faces',
        help_text="Staff member who performed the registration"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this face data is active for recognition"
    )

    def get_image_url(self):
        """Get secure URL for face image"""
        if self.image:
            try:
                return self.image.url
            except Exception:
                return None
        return None
    
    def get_public_id(self):
        """Get Cloudinary public_id for the image"""
        if self.image and hasattr(self.image, 'public_id'):
            return self.image.public_id
        return None
    
    def revoke(self, performed_by=None, reason=None):
        """Revoke this face data and create audit log"""
        self.is_active = False
        self.save()
        
        # Create audit log
        from .utils import create_face_audit_log
        create_face_audit_log(
            hotel=self.hotel,
            staff=self.staff,
            action='REVOKED',
            performed_by=performed_by or self.staff,
            reason=reason
        )
    
    def __str__(self):
        status = "Active" if self.is_active else "Revoked"
        return f"Face data for {self.staff} @ {self.hotel.slug} ({status})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Staff Face Data"
        verbose_name_plural = "Staff Face Data"
        indexes = [
            models.Index(fields=['hotel', 'is_active']),
            models.Index(fields=['staff', 'is_active']),
        ]


class ClockLog(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE, related_name='clock_logs'
    )
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    time_in = models.DateTimeField(auto_now_add=True)
    time_out = models.DateTimeField(null=True, blank=True)
    verified_by_face = models.BooleanField(default=True)
    location_note = models.CharField(max_length=255, blank=True, null=True)
    auto_clock_out = models.BooleanField(default=False)
    hours_worked = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # NEW: link clock log to a planned roster shift
    roster_shift = models.ForeignKey(
        'attendance.StaffRoster',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='clock_logs',
        help_text="Optional link to planned roster shift for this log.",
    )

    # PHASE 4: Unrostered clock-in approval fields
    # True if there was no matching roster shift at clock-in
    is_unrostered = models.BooleanField(
        default=False,
        help_text="True if clocked in without matching roster shift"
    )

    # Approved by manager for payroll / reports
    is_approved = models.BooleanField(
        default=True,
        help_text="Whether this log is approved for payroll calculations"
    )

    # If explicitly rejected by manager (do not count to hours)
    is_rejected = models.BooleanField(
        default=False,
        help_text="Whether this log was rejected by management"
    )

    # PHASE 4: Long-session warning flags
    break_warning_sent = models.BooleanField(
        default=False,
        help_text="Break reminder notification sent for this session"
    )
    overtime_warning_sent = models.BooleanField(
        default=False,
        help_text="Overtime warning notification sent for this session"
    )
    hard_limit_warning_sent = models.BooleanField(
        default=False,
        help_text="Hard limit warning notification sent for this session"
    )

    # Optional – track how the hard limit alert was handled
    long_session_ack_mode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=(
            ('stay', 'Stay clocked in'),
            ('clocked_out', 'Clocked out after warning'),
        ),
        help_text="How staff responded to hard limit warning"
    )

    def save(self, *args, **kwargs):
        # If both time_in and time_out exist, calculate hours
        if self.time_in and self.time_out:
            delta = self.time_out - self.time_in
            self.hours_worked = round(delta.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.staff} @ {self.hotel.slug} - "
            f"In: {self.time_in} | Out: {self.time_out or '---'}"
        )

    class Meta:
        ordering = ['-time_in']


class RosterPeriod(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    title = models.CharField(
        max_length=100, help_text="e.g., 'Week 29 Roster'"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True
    )
    published = models.BooleanField(default=False)
    
    # PHASE 4: Period finalization for locking
    is_finalized = models.BooleanField(
        default=False,
        help_text="When finalized, related ClockLogs and StaffRoster shifts are locked"
    )
    finalized_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finalized_periods',
        help_text="Staff member who finalized this period"
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this period was finalized"
    )

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

    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE, related_name='staff_rosters'
    )
    staff = models.ForeignKey(
        'staff.Staff', on_delete=models.CASCADE, related_name='roster_entries'
    )
    # ForeignKey to Department model instead of CharField
    department = models.ForeignKey(
        'staff.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roster_entries'
    )
    period = models.ForeignKey(
        'RosterPeriod', on_delete=models.CASCADE, related_name='entries', null=True
    )

    shift_date = models.DateField()
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    break_start = models.TimeField(blank=True, null=True)
    break_end = models.TimeField(blank=True, null=True)

    shift_type = models.CharField(
        max_length=20, choices=SHIFT_TYPES, default='custom'
    )
    is_split_shift = models.BooleanField(default=False)
    is_night_shift = models.BooleanField(default=False)
    expected_hours = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
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
    location = models.ForeignKey(
        'attendance.ShiftLocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shifts"
    )

    class Meta:
        # Allow multiple shifts on the same date, but unique per start time
        unique_together = ('staff', 'shift_date', 'shift_start')
        ordering = ['shift_date', 'shift_start']

    def __str__(self):
        return (
            f"{self.staff} on {self.shift_date} "
            f"({self.shift_start}-{self.shift_end})"
        )



class StaffAvailability(models.Model):
    staff = models.ForeignKey(
        'staff.Staff', on_delete=models.CASCADE, related_name='availabilities'
    )
    date = models.DateField()
    available = models.BooleanField(default=True)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        status = 'Available' if self.available else 'Unavailable'
        return f"{self.staff} | {self.date} - {status}"


class ShiftTemplate(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_night = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.hotel.name} | {self.name} "
            f"({self.start_time}-{self.end_time})"
        )


class RosterRequirement(models.Model):
    period = models.ForeignKey(
        'RosterPeriod', on_delete=models.CASCADE, related_name='requirements'
    )
    # ForeignKey for Department and Role models
    department = models.ForeignKey(
        'staff.Department',
        on_delete=models.CASCADE,
        related_name='roster_requirements'
    )

    role = models.ForeignKey(
        'staff.Role',
        on_delete=models.CASCADE,
        related_name='roster_requirements'
    )
    date = models.DateField()
    required_count = models.PositiveIntegerField()

    def __str__(self):
        return (
            f"{self.department} | {self.role} on {self.date}: "
            f"{self.required_count} needed"
        )

# attendance/models.py


class ShiftLocation(models.Model):
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE, related_name='shift_locations'
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#0d6efd")  # hex color

    def __str__(self):
        return f"{self.name} @ {self.hotel.slug}"


class DailyPlan(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hotel', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"Daily Plan for {self.hotel.name} on {self.date}"


class DailyPlanEntry(models.Model):
    plan = models.ForeignKey(
        DailyPlan, related_name='entries', on_delete=models.CASCADE
    )
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    department = models.ForeignKey(
        'staff.Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        editable=False  # to avoid manual editing
    )
    roster = models.ForeignKey(
        'StaffRoster',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='daily_plan_entries'
    )
    location = models.ForeignKey(
        'attendance.ShiftLocation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        unique_together = (
            'plan', 'staff', 'location', 'shift_start', 'shift_end'
        )
        ordering = ['location__name', 'staff__last_name', 'staff__first_name']

    def save(self, *args, **kwargs):
        # Automatically set department from staff on save
        if self.staff:
            self.department = self.staff.department
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff} → {self.location} on {self.plan.date}"


class RosterAuditLog(models.Model):
    """Audit log for tracking all roster modifications and copy operations"""
    
    OPERATION_TYPES = [
        ('create', 'Create Shift'),
        ('update', 'Update Shift'),
        ('delete', 'Delete Shift'),
        ('copy_bulk', 'Copy All Shifts (Period to Period)'),
        ('copy_day', 'Copy Day Shifts'),
        ('copy_staff', 'Copy Staff Shifts'),
        ('bulk_save', 'Bulk Save Operation'),
    ]
    
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.CASCADE, related_name='roster_audit_logs'
    )
    performed_by = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL, null=True, blank=True
    )
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    
    # Operation details
    affected_shifts_count = models.PositiveIntegerField(default=0)
    source_period = models.ForeignKey(
        'RosterPeriod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_as_source'
    )
    target_period = models.ForeignKey(
        'RosterPeriod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs_as_target'
    )
    
    # Specific shift information (for single operations)
    roster_shift = models.ForeignKey(
        'StaffRoster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    affected_staff = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roster_modifications_audit'
    )
    
    # Additional metadata
    operation_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional operation metadata (source_date, target_date, etc.)"
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['hotel', 'operation_type']),
            models.Index(fields=['performed_by', 'timestamp']),
            models.Index(fields=['hotel', 'timestamp']),
        ]
    
    def __str__(self):
        staff_name = (
            self.performed_by.user.get_full_name() if self.performed_by
            else "System"
        )
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M')
        return (
            f"{staff_name} - {self.get_operation_type_display()} "
            f"on {timestamp_str}"
        )


class FaceAuditLog(models.Model):
    """Audit log for tracking face lifecycle events (registration, revocation, re-registration)"""
    ACTION_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('REVOKED', 'Revoked'),
        ('RE_REGISTERED', 'Re-registered'),
    ]
    
    hotel = models.ForeignKey(
        'hotel.Hotel', 
        on_delete=models.CASCADE, 
        related_name='face_audit_logs'
    )
    staff = models.ForeignKey(
        'staff.Staff', 
        on_delete=models.CASCADE,
        related_name='face_audit_logs'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of face lifecycle action performed"
    )
    performed_by = models.ForeignKey(
        'staff.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_face_actions',
        help_text="Staff member who performed this action (may be same as target staff for self-registration)"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Optional reason for the action (especially for revocation)"
    )
    consent_given = models.BooleanField(
        default=True,
        help_text="Whether consent was explicitly given for face data processing"
    )
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the client when action was performed"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string for audit trail"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Face Audit Log"
        verbose_name_plural = "Face Audit Logs"

    def __str__(self):
        return f"{self.action} for {self.staff} at {self.hotel.slug} by {self.performed_by or 'system'}"
