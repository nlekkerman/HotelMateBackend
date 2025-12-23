"""
THE ONE TRUE CHECKOUT SERVICE

This module contains the centralized checkout logic used by:
- Staff single booking checkout (BookingCheckOutView)
- Booking assignment checkout (BookingAssignmentView) 
- Bulk room checkout (checkout_rooms)

All checkout operations go through checkout_booking() to ensure consistency.
"""

from django.db import transaction
from django.utils import timezone
from guests.models import Guest
from chat.utils import pusher_client
import logging

logger = logging.getLogger(__name__)


def checkout_booking(
    *,
    booking,
    performed_by,
    source="staff_api",
):
    """
    THE ONE TRUE CHECKOUT.
    
    Args:
        booking: RoomBooking instance to check out
        performed_by: Staff user performing the checkout
        source: String identifying the checkout source for logging/events
        
    Returns:
        RoomBooking: Updated booking instance
        
    Raises:
        ValueError: If booking has no assigned room or is already checked out
    """
    
    if not booking.assigned_room:
        raise ValueError("Booking has no assigned room to checkout from")

    if booking.checked_out_at:
        logger.info(f"Booking {booking.booking_id} already checked out - idempotent operation")
        return booking  # idempotent

    room = booking.assigned_room
    hotel = booking.hotel

    with transaction.atomic():
        # Lock booking and room BEFORE running guest queries to prevent race conditions
        booking = booking.__class__.objects.select_for_update().get(id=booking.id)
        room = room.__class__.objects.select_for_update().get(id=room.id)
        
        # 1️⃣ Enhanced guest detection logic - handle corrupted guest-booking links
        # A) All guests linked to booking (regardless of their room field)
        booking_guests = Guest.objects.filter(booking=booking)
        
        # B) All orphaned guests currently in the assigned room with booking IS NULL
        orphaned_guests = Guest.objects.filter(room=room, booking__isnull=True)
        
        # The union queryset is used only to compute affected guest IDs;
        # updates must be performed via a filtered queryset on those IDs.
        affected_guests = booking_guests.union(orphaned_guests)
        affected_guest_ids = list(affected_guests.values_list('id', flat=True))
        
        # Error-level logging for invalid states (orphaned guests in rooms)
        if orphaned_guests.exists():
            orphaned_count = orphaned_guests.count()
            booking_count = booking_guests.count()
            orphaned_ids = list(orphaned_guests.values_list('id', flat=True))
            logger.error(
                f"INVALID STATE: Found {orphaned_count} orphaned guests in room {room.room_number} "
                f"during checkout of booking {booking.booking_id}. "
                f"Booking guests: {booking_count}, Orphaned guests: {orphaned_count}. "
                f"Guest IDs: {orphaned_ids}"
            )
        
        # Detach all affected guests from room
        detached_count = Guest.objects.filter(id__in=affected_guest_ids).update(room=None)
        logger.info(f"Detached {detached_count} guests from room {room.room_number} for booking {booking.booking_id}")

        # Consistency assertion: verify room is completely cleared 
        # If this assertion fails, checkout must abort — a room with remaining guests after checkout is a fatal invariant violation.
        remaining_guests = Guest.objects.filter(room=room)
        if remaining_guests.exists():
            remaining_count = remaining_guests.count()
            remaining_ids = list(remaining_guests.values_list('id', flat=True))
            logger.error(
                f"CONSISTENCY FAILURE: {remaining_count} guests still in room {room.room_number} "
                f"after checkout cleanup for booking {booking.booking_id}. "
                f"Remaining guest IDs: {remaining_ids}"
            )
            raise ValueError(f"Checkout failed: {remaining_count} guests still assigned to room")
        
        logger.info(f"Verified room {room.room_number} completely cleared of guests")

        # 2️⃣ Update booking lifecycle
        booking.checked_out_at = timezone.now()
        booking.status = "COMPLETED"
        booking.save(update_fields=["checked_out_at", "status"])

        # 3️⃣ Update room for turnover workflow
        room.is_occupied = False
        room.room_status = "CHECKOUT_DIRTY"
        room.guest_fcm_token = None  # Clear guest FCM token
        room.save(update_fields=["is_occupied", "room_status", "guest_fcm_token"])

        # 4️⃣ Add turnover note if room supports it
        if hasattr(room, "add_turnover_note"):
            staff_name = (
                f"{performed_by.first_name} {performed_by.last_name}".strip()
                or getattr(performed_by, "email", "Staff")
            )
            room.add_turnover_note(
                f"Checked out at {timezone.now().strftime('%Y-%m-%d %H:%M')} by {staff_name}",
                performed_by,
            )

        # 5️⃣ Cleanup guest sessions and orders
        _cleanup_room_data(room, hotel)

        # 6️⃣ Emit realtime events (after transaction commits)
        transaction.on_commit(
            lambda: _emit_checkout_events(
                booking=booking,
                room=room,
                hotel=hotel,
                source=source,
            )
        )

    logger.info(f"Successfully checked out booking {booking.booking_id} from room {room.room_number}")
    return booking


def _cleanup_room_data(room, hotel):
    """Clean up room-related data during checkout"""
    from chat.models import GuestChatSession, Conversation
    from chat.models import RoomMessage
    from room_services.models import Order, BreakfastOrder
    
    # Delete guest chat sessions for this room
    GuestChatSession.objects.filter(room=room).delete()
    
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


def _emit_checkout_events(*, booking, room, hotel, source):
    """Emit unified realtime events for checkout"""
    try:
        # Import here to avoid circular imports
        from notifications.notification_manager import notification_manager
        
        # Unified notification manager events
        notification_manager.realtime_booking_checked_out(
            booking, room.room_number
        )
        notification_manager.realtime_room_occupancy_updated(room)
        
    except ImportError:
        logger.warning("notification_manager not available, skipping notifications")
    except Exception as e:
        logger.error(f"Failed to emit booking checkout notifications: {e}")

    try:
        # Room status change event
        pusher_client.trigger(
            f"hotel-{hotel.slug}",
            "room-status-changed",
            {
                "room_number": room.room_number,
                "old_status": "OCCUPIED",
                "new_status": "CHECKOUT_DIRTY",
                "source": source,
                "timestamp": timezone.now().isoformat(),
            },
        )
        
        logger.info(f"Emitted realtime events for checkout: booking {booking.booking_id}, room {room.room_number}")
        
    except Exception as e:
        logger.error(f"Failed to emit realtime checkout events: {e}")