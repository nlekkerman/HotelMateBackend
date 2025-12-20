from django.db import models
from django.core.exceptions import ValidationError


class RoomStatusEvent(models.Model):
    """
    Immutable audit trail for all room status changes.
    Every status transition must create an audit record.
    """
    SOURCE_CHOICES = [
        ('HOUSEKEEPING', 'Housekeeping'),
        ('FRONT_DESK', 'Front Desk'),
        ('SYSTEM', 'System'),
        ('MANAGER_OVERRIDE', 'Manager Override'),
    ]
    
    hotel = models.ForeignKey(
        'hotel.Hotel', 
        on_delete=models.CASCADE,
        help_text="Hotel where the room status change occurred"
    )
    room = models.ForeignKey(
        'rooms.Room', 
        on_delete=models.CASCADE,
        help_text="Room that had status changed"
    )
    from_status = models.CharField(
        max_length=20,
        help_text="Previous room status"
    )
    to_status = models.CharField(
        max_length=20,
        help_text="New room status"
    )
    changed_by = models.ForeignKey(
        'staff.Staff',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Staff member who initiated the status change"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='HOUSEKEEPING',
        help_text="Source system/department that initiated the change"
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about the status change"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the status change occurred"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hotel', 'room', '-created_at']),
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['hotel', 'source', '-created_at']),
        ]
        verbose_name = 'Room Status Event'
        verbose_name_plural = 'Room Status Events'
    
    def __str__(self):
        return f"{self.room} {self.from_status} → {self.to_status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def clean(self):
        """Validate that room belongs to the same hotel"""
        if self.room and self.hotel and self.room.hotel_id != self.hotel_id:
            raise ValidationError({
                'room': 'Room must belong to the specified hotel.'
            })


class HousekeepingTask(models.Model):
    """
    Workflow management for housekeeping operations.
    Tracks tasks assigned to staff for room maintenance and turnover.
    """
    TASK_TYPE_CHOICES = [
        ('TURNOVER', 'Turnover'),
        ('STAYOVER', 'Stayover'),
        ('INSPECTION', 'Inspection'),
        ('DEEP_CLEAN', 'Deep Clean'),
        ('AMENITY', 'Amenity'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MED', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        help_text="Hotel where the task is to be performed"
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        help_text="Room where the task is to be performed"
    )
    booking = models.ForeignKey(
        'hotel.RoomBooking',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Associated booking (optional)"
    )
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        help_text="Type of housekeeping task"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        help_text="Current status of the task"
    )
    priority = models.CharField(
        max_length=5,
        choices=PRIORITY_CHOICES,
        default='MED',
        help_text="Priority level of the task"
    )
    assigned_to = models.ForeignKey(
        'staff.Staff',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_housekeeping_tasks',
        help_text="Staff member assigned to complete the task"
    )
    note = models.TextField(
        blank=True,
        default="",
        help_text="Additional task notes or instructions"
    )
    created_by = models.ForeignKey(
        'staff.Staff',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_housekeeping_tasks',
        help_text="Staff member who created the task"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the task was created"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When work on the task began"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was completed"
    )
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['hotel', 'status', 'task_type']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['room', 'status']),
            models.Index(fields=['hotel', 'priority', '-created_at']),
        ]
        verbose_name = 'Housekeeping Task'
        verbose_name_plural = 'Housekeeping Tasks'
    
    def __str__(self):
        assigned_to_name = f"{self.assigned_to.first_name} {self.assigned_to.last_name}".strip() or self.assigned_to.email or "Staff" if self.assigned_to else "Unassigned"
        return f"{self.get_task_type_display()} - Room {self.room.room_number} ({assigned_to_name})"
    
    def clean(self):
        """Validate task constraints"""
        errors = {}
        
        # Validate room belongs to same hotel
        if self.room and self.hotel and self.room.hotel_id != self.hotel_id:
            errors['room'] = 'Room must belong to the specified hotel.'
        
        # Validate assigned_to belongs to same hotel (if assigned)
        if self.assigned_to and self.hotel and self.assigned_to.hotel_id != self.hotel_id:
            errors['assigned_to'] = 'Assigned staff member must belong to the same hotel.'
        
        # Validate created_by belongs to same hotel (if specified)
        if self.created_by and self.hotel and self.created_by.hotel_id != self.hotel_id:
            errors['created_by'] = 'Creating staff member must belong to the same hotel.'
        
        # Validate booking belongs to same hotel (if specified)
        if self.booking and self.hotel and self.booking.hotel_id != self.hotel_id:
            errors['booking'] = 'Booking must belong to the same hotel.'
        
        if errors:
            raise ValidationError(errors)
    
    @property
    def is_overdue(self):
        """Check if task is overdue based on priority and creation time"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status in ['DONE', 'CANCELLED']:
            return False
        
        now = timezone.now()
        hours_since_created = (now - self.created_at).total_seconds() / 3600
        
        # Define SLA hours based on priority
        sla_hours = {
            'HIGH': 2,
            'MED': 4,
            'LOW': 8,
        }
        
        return hours_since_created > sla_hours.get(self.priority, 4)
