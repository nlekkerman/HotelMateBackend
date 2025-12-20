"""
Housekeeping Services

Canonical business logic for room status management.
Single source of truth for all room status changes.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import RoomStatusEvent
from .policy import can_change_room_status


@transaction.atomic
def set_room_status(*, room, to_status, staff=None, source="HOUSEKEEPING", note=""):
    """
    Canonical function for all room status changes.
    
    This is the ONLY function that should modify room.room_status.
    All status changes must flow through this function to ensure:
    - Validation of transitions
    - Permission enforcement
    - Audit trail creation
    - Consistent field updates
    
    Args:
        room: Room instance to update
        to_status: Target room status (must be valid ROOM_STATUS_CHOICES key)
        staff: Staff member initiating the change (optional for system changes)
        source: Source of the change (HOUSEKEEPING, FRONT_DESK, SYSTEM, MANAGER_OVERRIDE)
        note: Additional notes about the change
    
    Returns:
        Room: Updated room instance
    
    Raises:
        ValidationError: If transition is invalid or permissions are insufficient
    """
    if not room:
        raise ValidationError("Room is required")
    
    # Import here to avoid circular imports
    from rooms.models import Room
    
    # Validate to_status is valid
    valid_statuses = dict(Room.ROOM_STATUS_CHOICES)
    if to_status not in valid_statuses:
        raise ValidationError(f"Invalid room status: {to_status}. Must be one of: {list(valid_statuses.keys())}")
    
    # Store original status for audit
    from_status = room.room_status
    
    # Skip validation if status is not changing
    if from_status == to_status:
        return room
    
    # Validate room can transition to new status
    if not room.can_transition_to(to_status):
        raise ValidationError(
            f"Room {room.room_number} cannot transition from {from_status} to {to_status}. "
            f"Current state does not allow this transition."
        )
    
    # Enforce permissions if staff is provided
    if staff:
        can_change, error_msg = can_change_room_status(
            staff=staff, 
            room=room, 
            to_status=to_status, 
            source=source, 
            note=note
        )
        if not can_change:
            raise ValidationError(f"Permission denied: {error_msg}")
    
    # Create audit record BEFORE making changes
    RoomStatusEvent.objects.create(
        hotel=room.hotel,
        room=room,
        from_status=from_status,
        to_status=to_status,
        changed_by=staff,
        source=source,
        note=note
    )
    
    # Update room fields based on new status
    now = timezone.now()
    fields_to_update = ['room_status']
    
    # Set the new status
    room.room_status = to_status
    
    # Update status-specific fields
    if to_status == 'CLEANING_IN_PROGRESS':
        # Optional: Add turnover note when cleaning starts
        if hasattr(room, 'add_turnover_note'):
            if staff:
                staff_name = f"{staff.first_name} {staff.last_name}".strip() or staff.email or "Staff"
            else:
                staff_name = "System"
            room.add_turnover_note(f"Cleaning started by {staff_name}", staff_member=staff)
    
    elif to_status == 'CLEANED_UNINSPECTED':
        # Mark as cleaned
        room.last_cleaned_at = now
        if staff:
            room.cleaned_by_staff = staff
        fields_to_update.extend(['last_cleaned_at', 'cleaned_by_staff'])
    
    elif to_status == 'READY_FOR_GUEST':
        # Mark as inspected (treating READY_FOR_GUEST as inspected)
        room.last_inspected_at = now
        if staff:
            room.inspected_by_staff = staff
        fields_to_update.extend(['last_inspected_at', 'inspected_by_staff'])
    
    elif to_status == 'MAINTENANCE_REQUIRED':
        # Flag for maintenance
        room.maintenance_required = True
        fields_to_update.append('maintenance_required')
        
        # Optional: Add maintenance note
        if note and hasattr(room, 'maintenance_notes'):
            existing_notes = room.maintenance_notes or ""
            timestamp = now.strftime("%Y-%m-%d %H:%M")
            if staff:
                staff_name = f"{staff.first_name} {staff.last_name}".strip() or staff.email or "Staff"
            else:
                staff_name = "System"
            new_note = f"[{timestamp}] {staff_name}: {note}"
            
            if existing_notes:
                room.maintenance_notes = f"{existing_notes}\n{new_note}"
            else:
                room.maintenance_notes = new_note
            fields_to_update.append('maintenance_notes')
    
    elif to_status in ['READY_FOR_GUEST']:
        # These statuses indicate room is not occupied
        # Only set is_occupied=False if there's no active booking checked in
        if hasattr(room, 'is_occupied'):
            # Check for active bookings with check-in
            active_bookings = room.room_bookings.filter(
                checked_in_at__isnull=False,
                checked_out_at__isnull=True
            ).exists()
            
            if not active_bookings:
                room.is_occupied = False
                fields_to_update.append('is_occupied')
    
    # Save only the fields we've modified
    room.save(update_fields=fields_to_update)
    
    # Emit realtime room update after commit
    from notifications.notification_manager import NotificationManager
    notification_manager = NotificationManager()
    
    # Use transaction.on_commit to ensure the update is sent after database commit
    from django.db import transaction
    transaction.on_commit(
        lambda: notification_manager.realtime_room_updated(
            room=room,
            changed_fields=fields_to_update,
            source=source.lower()  # Convert to lowercase for consistency
        )
    )
    
    return room


def get_room_status_history(room, limit=50):
    """
    Get status change history for a room.
    
    Args:
        room: Room instance
        limit: Maximum number of events to return
    
    Returns:
        QuerySet: RoomStatusEvent instances ordered by most recent first
    """
    return RoomStatusEvent.objects.filter(room=room).order_by('-created_at')[:limit]


def get_room_dashboard_data(hotel):
    """
    Get dashboard data for housekeeping overview.
    
    Args:
        hotel: Hotel instance
    
    Returns:
        dict: Dashboard data with room counts and status groupings
    """
    from rooms.models import Room
    from collections import defaultdict
    
    # Get all rooms for this hotel
    rooms = Room.objects.filter(hotel=hotel, is_active=True)
    
    # Count rooms by status
    status_counts = defaultdict(int)
    rooms_by_status = defaultdict(list)
    
    for room in rooms:
        status = room.room_status
        status_counts[status] += 1
        
        # Add room data for grouping
        rooms_by_status[status].append({
            'id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type.name if room.room_type else None,
            'maintenance_required': room.maintenance_required,
            'last_cleaned_at': room.last_cleaned_at,
            'last_inspected_at': room.last_inspected_at,
            'is_out_of_order': room.is_out_of_order,
        })
    
    return {
        'counts': dict(status_counts),
        'rooms_by_status': dict(rooms_by_status),
        'total_rooms': len(rooms),
    }


def create_turnover_task(room, booking=None, staff=None, priority='MED', note=""):
    """
    Create a turnover task for a room.
    
    Args:
        room: Room instance
        booking: Optional RoomBooking instance
        staff: Staff member creating the task
        priority: Task priority (LOW, MED, HIGH)
        note: Task notes
    
    Returns:
        HousekeepingTask: Created task instance
    """
    from .models import HousekeepingTask
    
    return HousekeepingTask.objects.create(
        hotel=room.hotel,
        room=room,
        booking=booking,
        task_type='TURNOVER',
        priority=priority,
        created_by=staff,
        note=note
    )
