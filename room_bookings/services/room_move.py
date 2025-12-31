"""
Room Move Service - Additive Only

This service provides room move operations for IN-HOUSE bookings only.
It does NOT modify existing assignment/reassignment/checkout logic.
"""

from django.db import transaction, models
from django.utils import timezone
from room_bookings.services.room_assignment import RoomAssignmentService
from room_bookings.exceptions import RoomAssignmentError


class RoomMoveError(Exception):
    """Room move specific errors"""
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class RoomMoveService:
    """Service for moving IN-HOUSE bookings between rooms"""
    
    @classmethod
    @transaction.atomic
    def move_room_atomic(
        cls,
        *,
        booking_id: str,
        to_room_id: int,
        staff_user,
        reason: str = "",
        notes: str = ""
    ):
        """
        Atomically move an in-house booking to a different room.
        
        Args:
            booking_id: String booking identifier (e.g., "BK-2025-0005")
            to_room_id: Target room ID
            staff_user: Staff instance performing the move
            reason: Reason for the room move
            notes: Additional notes about the move
        
        Returns: Updated RoomBooking instance
        Raises: RoomMoveError for validation failures
        """
        from hotel.models import RoomBooking
        from rooms.models import Room
        
        # Lock booking and both rooms for update to prevent race conditions
        booking = RoomBooking.objects.select_for_update().get(booking_id=booking_id)
        
        # Validate booking is in-house (checked in but not checked out)
        if booking.checked_in_at is None:
            raise RoomMoveError(
                code='BOOKING_NOT_CHECKED_IN',
                message='Booking must be checked in to move rooms'
            )
            
        if booking.checked_out_at is not None:
            raise RoomMoveError(
                code='BOOKING_ALREADY_CHECKED_OUT',
                message='Cannot move room for checked out booking'
            )
        
        # Validate booking has assigned room
        if not booking.assigned_room:
            raise RoomMoveError(
                code='NO_ROOM_ASSIGNED',
                message='Booking has no assigned room to move from'
            )
        
        # Lock both from_room and to_room
        from_room = Room.objects.select_for_update().get(id=booking.assigned_room.id)
        to_room = Room.objects.select_for_update().get(id=to_room_id)
        
        # Idempotent check: if already in target room, return unchanged
        if from_room.id == to_room.id:
            return booking
        
        # Hotel scope validation
        if booking.hotel != to_room.hotel:
            raise RoomMoveError(
                code='HOTEL_MISMATCH',
                message='Target room belongs to different hotel'
            )
        
        # Room availability validation
        if not to_room.is_active:
            raise RoomMoveError(
                code='ROOM_NOT_ACTIVE',
                message='Target room is not active'
            )
            
        if to_room.is_out_of_order:
            raise RoomMoveError(
                code='ROOM_OUT_OF_ORDER',
                message='Target room is out of order'
            )
            
        if to_room.is_occupied:
            raise RoomMoveError(
                code='ROOM_OCCUPIED',
                message='Target room is currently occupied'
            )
        
        # Capacity validation using existing party logic
        cls._validate_room_capacity(booking, to_room)
        
        # Availability validation using existing service
        cls._validate_room_availability(booking, to_room)
        
        # Perform the move
        cls._execute_room_move(
            booking=booking,
            from_room=from_room,
            to_room=to_room,
            staff_user=staff_user,
            reason=reason,
            notes=notes
        )
        
        # Emit realtime events after transaction commits
        transaction.on_commit(
            lambda: cls._emit_room_move_events(booking, from_room, to_room)
        )
        
        return booking
    
    @classmethod
    def _validate_room_capacity(cls, booking, to_room):
        """Validate room capacity using existing party logic"""
        # Use existing party count if available, fallback to adults+children
        if hasattr(booking, 'party') and booking.party.exists():
            party_count = booking.party.filter(is_staying=True).count()
        else:
            party_count = booking.adults + booking.children
            
        if party_count > to_room.room_type.max_occupancy:
            raise RoomMoveError(
                code='ROOM_CAPACITY_EXCEEDED',
                message=f'Party size ({party_count}) exceeds room capacity ({to_room.room_type.max_occupancy})'
            )
    
    @classmethod
    def _validate_room_availability(cls, booking, to_room):
        """Validate room availability using existing service logic"""
        # Use existing availability finder to check for conflicts
        available_rooms = RoomAssignmentService.find_available_rooms_for_booking(booking)
        
        if to_room not in available_rooms:
            raise RoomMoveError(
                code='ROOM_NOT_AVAILABLE',
                message='Target room has conflicting bookings'
            )
    
    @classmethod
    def _execute_room_move(cls, booking, from_room, to_room, staff_user, reason, notes):
        """Execute the actual room move operation"""
        # Update booking assignment
        booking.assigned_room = to_room
        booking.assignment_version += 1
        
        # Set new move audit fields
        booking.room_moved_at = timezone.now()
        booking.room_moved_by = staff_user
        booking.room_moved_from = from_room
        booking.room_move_reason = reason
        booking.room_move_notes = notes
        
        booking.save()
        
        # Update from_room (similar to checkout)
        from_room.is_occupied = False
        from_room.room_status = 'CHECKOUT_DIRTY'  # Reuse existing status
        from_room.guest_fcm_token = None
        from_room.save()
        
        # Update to_room
        to_room.is_occupied = True
        to_room.room_status = 'OCCUPIED'
        to_room.save()
        
        # Clean up room data from from_room (reuse existing cleanup)
        cls._cleanup_from_room(from_room, booking.hotel)
    
    @classmethod
    def _cleanup_from_room(cls, room, hotel):
        """Clean up room data when moving out (reuse existing patterns)"""
        from chat.models import Conversation, RoomMessage
        from room_services.models import Order, BreakfastOrder
        
        # Note: GuestChatSession removed - using token-based auth now
        
        # Delete conversations & messages for this room
        Conversation.objects.filter(room=room).delete()
        RoomMessage.objects.filter(room=room).delete()
        
        # Delete any open room-service & breakfast orders
        Order.objects.filter(
            hotel=hotel,
            room_number=room.room_number
        ).delete()
        BreakfastOrder.objects.filter(
            hotel=hotel,
            room_number=room.room_number
        ).delete()
    
    @classmethod
    def _emit_room_move_events(cls, booking, from_room, to_room):
        """Emit realtime events for room move using existing patterns"""
        try:
            # Import here to avoid circular imports
            from notifications.notification_manager import notification_manager
            
            # Emit booking updated event
            notification_manager.realtime_booking_updated(booking)
            
            # Emit room updated events for both rooms
            notification_manager.realtime_room_occupancy_updated(from_room)
            notification_manager.realtime_room_occupancy_updated(to_room)
            
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("notification_manager not available, skipping room move notifications")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to emit room move notifications: {e}")