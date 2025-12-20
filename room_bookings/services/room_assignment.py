from django.db import transaction, models
from django.utils import timezone
from room_bookings.constants import INVENTORY_BLOCKING_STATUSES, ASSIGNABLE_BOOKING_STATUSES, NON_BLOCKING_STATUSES
from room_bookings.exceptions import RoomAssignmentError

class RoomAssignmentService:
    
    @staticmethod
    def find_available_rooms_for_booking(booking):
        """
        Returns rooms available for assignment to this booking.
        
        Filters:
        - Same hotel as booking
        - Matching room_type 
        - Room.is_bookable() == True
        - No overlap conflicts with INVENTORY_BLOCKING_STATUSES bookings
        
        Returns: QuerySet of Room objects sorted by room_number
        """
        from rooms.models import Room
        from hotel.models import RoomBooking
        
        # Get conflicting room IDs (rooms with overlapping bookings)
        # Blocks inventory if: status='CONFIRMED' AND checked_out_at IS NULL
        # OR checked_in_at IS NOT NULL AND checked_out_at IS NULL (in-house guest)
        blocking_filter = models.Q(
            status__in=INVENTORY_BLOCKING_STATUSES,  # CONFIRMED
            checked_out_at__isnull=True  # Not checked out
        ) | models.Q(
            checked_in_at__isnull=False,  # Checked in
            checked_out_at__isnull=True   # Not checked out
        )
        
        conflicting_rooms = RoomBooking.objects.filter(
            assigned_room__isnull=False,
            # Overlap logic: (existing.check_in < booking.check_out) AND (existing.check_out > booking.check_in)
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).filter(
            blocking_filter  # Apply timestamp-based blocking logic
        ).exclude(
            status__in=NON_BLOCKING_STATUSES  # Exclude cancelled/completed/no-show
        ).exclude(
            id=booking.id  # Don't conflict with self
        ).values_list('assigned_room_id', flat=True)
        
        return Room.objects.filter(
            hotel=booking.hotel,
            room_type=booking.room_type,
            # Replicate Room.is_bookable() logic as DB-filterable conditions
            room_status__in=['READY_FOR_GUEST'],
            is_active=True,
            is_out_of_order=False,
            maintenance_required=False
        ).exclude(
            id__in=conflicting_rooms
        ).order_by('room_number')
    
    @staticmethod 
    def assert_room_can_be_assigned(booking, room):
        """
        Validates that room can be safely assigned to booking.
        Raises RoomAssignmentError with structured error codes.
        """
        # Hotel scope validation
        if booking.hotel != room.hotel:
            raise RoomAssignmentError(
                code='HOTEL_MISMATCH',
                message=f'Room {room.room_number} belongs to different hotel'
            )
            
        # Defensive check: RoomType should be hotel-scoped
        if booking.room_type.hotel != booking.hotel:
            raise RoomAssignmentError(
                code='ROOM_TYPE_HOTEL_MISMATCH',
                message=f'Booking room type belongs to different hotel'
            )
        
        # Booking status validation
        if booking.status not in ASSIGNABLE_BOOKING_STATUSES:
            raise RoomAssignmentError(
                code='BOOKING_STATUS_NOT_ASSIGNABLE',
                message=f'Booking status {booking.status} is not assignable'
            )
            
        # Check-in status validation (use timestamp-based "in-house" concept)
        # In-house means: checked_in_at is not None AND checked_out_at is None
        if booking.checked_in_at is not None and booking.checked_out_at is None:
            raise RoomAssignmentError(
                code='BOOKING_ALREADY_CHECKED_IN',
                message='Cannot assign room to in-house guest (already checked in)'
            )
            
        # Room type validation
        if room.room_type != booking.room_type:
            raise RoomAssignmentError(
                code='ROOM_TYPE_MISMATCH', 
                message=f'Room type {room.room_type} does not match booking type {booking.room_type}'
            )
            
        # Room bookability validation
        if not room.is_bookable():
            raise RoomAssignmentError(
                code='ROOM_NOT_BOOKABLE',
                message=f'Room {room.room_number} is not bookable (status: {room.room_status})'
            )
            
        # Overlap conflict validation (using timestamp-based blocking)
        from hotel.models import RoomBooking
        blocking_filter = models.Q(
            status__in=INVENTORY_BLOCKING_STATUSES,  # CONFIRMED
            checked_out_at__isnull=True  # Not checked out
        ) | models.Q(
            checked_in_at__isnull=False,  # Checked in
            checked_out_at__isnull=True   # Not checked out
        )
        
        conflicting_bookings = RoomBooking.objects.filter(
            assigned_room=room,
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).filter(
            blocking_filter  # Apply timestamp-based blocking logic
        ).exclude(
            status__in=NON_BLOCKING_STATUSES  # Exclude cancelled/completed/no-show
        ).exclude(id=booking.id)
        
        if conflicting_bookings.exists():
            raise RoomAssignmentError(
                code='ROOM_OVERLAP_CONFLICT',
                message=f'Room {room.room_number} has overlapping bookings',
                details={'conflicting_booking_ids': list(conflicting_bookings.values_list('id', flat=True))}
            )
    
    @classmethod
    @transaction.atomic
    def assign_room_atomic(cls, booking_id, room_id, staff_user, notes=None):
        """
        Atomically assign room to booking with full validation and audit logging.
        
        Args:
            booking_id: String booking identifier (e.g., "BK-2025-0005")
            room_id: Numeric room ID
            staff_user: Staff instance
            notes: Optional assignment notes
        
        Returns: Updated RoomBooking instance
        Raises: RoomAssignmentError for validation failures
        """
        from hotel.models import RoomBooking
        from rooms.models import Room
        
        # Lock booking and room for update to prevent concurrent modifications
        booking = RoomBooking.objects.select_for_update().get(booking_id=booking_id)
        room = Room.objects.select_for_update().get(id=room_id)
        
        # CRITICAL: Also lock potentially conflicting bookings to prevent race conditions
        # This ensures two concurrent assignments serialize on the conflict check
        blocking_filter = models.Q(
            status__in=INVENTORY_BLOCKING_STATUSES,
            checked_out_at__isnull=True
        ) | models.Q(
            checked_in_at__isnull=False,
            checked_out_at__isnull=True
        )
        
        potentially_conflicting = RoomBooking.objects.select_for_update().filter(
            assigned_room=room,
            check_in__lt=booking.check_out,
            check_out__gt=booking.check_in
        ).filter(
            blocking_filter
        ).exclude(
            status__in=NON_BLOCKING_STATUSES
        ).exclude(id=booking.id)
        
        # Force evaluation of the locking query
        list(potentially_conflicting)
        
        # Re-run all validations inside transaction (critical for concurrent safety)
        cls.assert_room_can_be_assigned(booking, room)
        
        # Idempotent check: if already assigned to same room, return existing
        if booking.assigned_room_id == room_id:
            return booking
            
        # Handle reassignment (allowed only before check-in)
        if booking.assigned_room_id and booking.assigned_room_id != room_id:
            # Use proper in-house check: checked_in_at exists AND not checked_out_at
            if booking.checked_in_at and not booking.checked_out_at:
                raise RoomAssignmentError(
                    code='BOOKING_ALREADY_CHECKED_IN',
                    message='Cannot reassign room for in-house guest'
                )
            
            # Log reassignment audit
            booking.room_reassigned_at = timezone.now()
            booking.room_reassigned_by = staff_user
            booking.assignment_version += 1
        
        # Perform assignment
        booking.assigned_room = room
        booking.room_assigned_at = timezone.now()
        booking.room_assigned_by = staff_user
        booking.assignment_notes = notes or ''
        booking.assignment_version += 1
        booking.save()
        
        return booking