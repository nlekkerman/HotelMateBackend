"""
Housekeeping Serializers

API serialization for housekeeping models and operations.
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import HousekeepingTask, RoomStatusEvent
from .policy import can_change_room_status, can_assign_task


class RoomStatusEventSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for room status audit events.
    """
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = RoomStatusEvent
        fields = [
            'id', 'hotel', 'hotel_name', 'room', 'room_number',
            'from_status', 'to_status', 'changed_by', 'changed_by_name',
            'source', 'source_display', 'note', 'created_at'
        ]
        read_only_fields = fields


class HousekeepingTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for housekeeping task management.
    """
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type_name = serializers.CharField(source='room.room_type.name', read_only=True)
    booking_id = serializers.CharField(source='booking.booking_id', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = HousekeepingTask
        fields = [
            'id', 'hotel', 'hotel_name', 'room', 'room_number', 'room_type_name',
            'booking', 'booking_id', 'task_type', 'task_type_display', 
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to', 'assigned_to_name', 'note', 
            'created_by', 'created_by_name', 'created_at', 
            'started_at', 'completed_at', 'is_overdue'
        ]
        read_only_fields = [
            'id', 'hotel', 'hotel_name', 'room_number', 'room_type_name',
            'booking_id', 'task_type_display', 'status_display', 'priority_display',
            'assigned_to_name', 'created_by_name', 'created_at', 'is_overdue'
        ]
    
    def validate(self, data):
        """Validate task data and hotel scoping"""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not hasattr(request.user, 'staff_profile'):
            raise serializers.ValidationError("Staff authentication required")
        
        staff = request.user.staff_profile
        hotel = staff.hotel
        
        # For create operations, set hotel and created_by
        if not self.instance:
            data['hotel'] = hotel
            data['created_by'] = staff
        
        # Validate room belongs to staff's hotel
        room = data.get('room')
        if room and room.hotel_id != hotel.id:
            raise serializers.ValidationError({
                'room': 'Room must belong to your hotel.'
            })
        
        # Validate booking belongs to staff's hotel (if provided)
        booking = data.get('booking')
        if booking and booking.hotel_id != hotel.id:
            raise serializers.ValidationError({
                'booking': 'Booking must belong to your hotel.'
            })
        
        # Validate assigned_to belongs to staff's hotel (if provided)
        assigned_to = data.get('assigned_to')
        if assigned_to and assigned_to.hotel_id != hotel.id:
            raise serializers.ValidationError({
                'assigned_to': 'Assigned staff member must belong to your hotel.'
            })
        
        return data


class HousekeepingTaskAssignSerializer(serializers.Serializer):
    """
    Serializer for assigning tasks to staff members.
    """
    assigned_to_id = serializers.IntegerField(
        help_text="ID of staff member to assign the task to"
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional note about the assignment"
    )
    
    def validate_assigned_to_id(self, value):
        """Validate assigned staff member"""
        from staff.models import Staff
        
        try:
            staff = Staff.objects.get(id=value)
        except Staff.DoesNotExist:
            raise serializers.ValidationError("Staff member not found.")
        
        request = self.context.get('request')
        if request and hasattr(request.user, 'staff_profile'):
            requesting_staff = request.user.staff_profile
            
            # Validate staff belongs to same hotel
            if staff.hotel_id != requesting_staff.hotel_id:
                raise serializers.ValidationError(
                    "Can only assign tasks to staff members in your hotel."
                )
        
        return value
    
    def validate(self, data):
        """Validate assignment permissions"""
        request = self.context.get('request')
        task = self.context.get('task')
        
        if not request or not hasattr(request.user, 'staff_profile'):
            raise serializers.ValidationError("Staff authentication required")
        
        if not task:
            raise serializers.ValidationError("Task context required")
        
        staff = request.user.staff_profile
        can_assign, error_msg = can_assign_task(staff, task)
        
        if not can_assign:
            raise serializers.ValidationError(error_msg)
        
        return data


class RoomStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for room status updates.
    """
    to_status = serializers.CharField(
        max_length=20,
        help_text="Target room status"
    )
    source = serializers.CharField(
        max_length=20,
        default='HOUSEKEEPING',
        help_text="Source of the status change"
    )
    note = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Additional notes about the status change"
    )
    
    def validate_to_status(self, value):
        """Validate target status is valid"""
        from rooms.models import Room
        
        valid_statuses = dict(Room.ROOM_STATUS_CHOICES)
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {list(valid_statuses.keys())}"
            )
        
        return value
    
    def validate_source(self, value):
        """Validate source is valid"""
        valid_sources = dict(RoomStatusEvent.SOURCE_CHOICES)
        if value not in valid_sources:
            raise serializers.ValidationError(
                f"Invalid source. Must be one of: {list(valid_sources.keys())}"
            )
        
        return value
    
    def validate(self, data):
        """Validate status change permissions"""
        request = self.context.get('request')
        room = self.context.get('room')
        
        if not request or not hasattr(request.user, 'staff_profile'):
            raise serializers.ValidationError("Staff authentication required")
        
        if not room:
            raise serializers.ValidationError("Room context required")
        
        staff = request.user.staff_profile
        to_status = data['to_status']
        source = data['source']
        note = data.get('note', '')
        
        # Check permissions
        can_change, error_msg = can_change_room_status(
            staff=staff,
            room=room,
            to_status=to_status,
            source=source,
            note=note
        )
        
        if not can_change:
            raise serializers.ValidationError(error_msg)
        
        # Require note for manager overrides
        if source == 'MANAGER_OVERRIDE' and not note.strip():
            raise serializers.ValidationError({
                'note': 'Note is required for manager overrides.'
            })
        
        return data


class RoomSummarySerializer(serializers.Serializer):
    """
    Serializer for room summary in dashboard.
    """
    id = serializers.IntegerField()
    room_number = serializers.CharField()
    room_type = serializers.CharField(allow_null=True)
    room_status = serializers.CharField()
    maintenance_required = serializers.BooleanField()
    last_cleaned_at = serializers.DateTimeField(allow_null=True)
    last_inspected_at = serializers.DateTimeField(allow_null=True)
    is_out_of_order = serializers.BooleanField()
    
    class Meta:
        fields = [
            'id', 'room_number', 'room_type', 'room_status',
            'maintenance_required', 'last_cleaned_at', 'last_inspected_at',
            'is_out_of_order'
        ]


class HousekeepingDashboardSerializer(serializers.Serializer):
    """
    Serializer for housekeeping dashboard data.
    """
    counts = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Room counts by status"
    )
    rooms_by_status = serializers.DictField(
        child=RoomSummarySerializer(many=True),
        help_text="Rooms grouped by status"
    )
    my_open_tasks = HousekeepingTaskSerializer(
        many=True,
        help_text="Tasks assigned to requesting staff member"
    )
    open_tasks = HousekeepingTaskSerializer(
        many=True,
        required=False,
        help_text="All open tasks in the hotel"
    )
    total_rooms = serializers.IntegerField(
        help_text="Total number of active rooms"
    )
