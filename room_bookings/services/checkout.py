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
from hotel.models import GuestBookingToken
from chat.utils import pusher_client
import logging

logger = logging.getLogger(__name__)


def _revoke_guest_tokens(booking, reason):
    """
    Revoke all active guest tokens for a booking.
    
    Args:
        booking: RoomBooking instance
        reason: Revocation reason string
    """
    try:
        # Revoke all active guest tokens for this booking
        tokens_updated = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE'
        ).update(
            status='REVOKED',
            revoked_at=timezone.now(),
            revoked_reason=reason
        )
        
        if tokens_updated > 0:
            logger.info(f"Revoked {tokens_updated} guest tokens for booking {booking.booking_id}: {reason}")
        
    except Exception as e:
        logger.error(f"Failed to revoke guest tokens for booking {booking.booking_id}: {e}")
        # Don't fail the entire checkout if token revocation fails


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
        
        # 2b️⃣ Revoke guest booking tokens after checkout
        _revoke_guest_tokens(booking, "Booking checked out")

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

        # 7️⃣ Trigger survey email (after transaction commits)
        transaction.on_commit(
            lambda: _trigger_survey_email(booking)
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


def _trigger_survey_email(booking):
    """Trigger survey email based on hotel configuration"""
    try:
        # GUARD: Do nothing if survey already sent or completed (prevent duplicates)
        if booking.survey_sent_at:
            logger.info(f"Survey already sent for booking {booking.booking_id} at {booking.survey_sent_at}, skipping")
            return
            
        if hasattr(booking, 'survey_response') and booking.survey_response is not None:
            logger.info(f"Survey already completed for booking {booking.booking_id}, skipping")
            return
        
        from hotel.models import HotelSurveyConfig
        from datetime import timedelta
        
        # Get hotel survey configuration
        hotel_config = HotelSurveyConfig.get_or_create_default(booking.hotel)
        
        if hotel_config.send_mode == 'AUTO_IMMEDIATE':
            _send_survey_email_now(booking, hotel_config)
        elif hotel_config.send_mode == 'AUTO_DELAYED':
            _schedule_survey_email(booking, hotel_config)
        elif hotel_config.send_mode == 'MANUAL_ONLY':
            logger.info(f"Survey set to MANUAL_ONLY for booking {booking.booking_id}, skipping auto-send")
        else:
            logger.warning(f"Unknown survey send_mode '{hotel_config.send_mode}' for booking {booking.booking_id}")
            
    except Exception as e:
        logger.error(f"Survey email trigger failed for booking {booking.booking_id}: {e}")
        # Do not break checkout if survey fails


def _send_survey_email_now(booking, hotel_config):
    """Send survey email immediately"""
    from hotel.models import BookingSurveyToken
    from django.conf import settings
    from django.core.mail import send_mail
    from django.utils import timezone
    from datetime import timedelta
    import hashlib
    import secrets
    
    # Check if survey already sent to prevent duplicates
    if booking.survey_sent_at:
        logger.info(f"Survey already sent for booking {booking.booking_id}, skipping")
        return
    
    # Determine target email
    target_email = booking.primary_email or booking.booker_email
    if not target_email:
        logger.warning(f"No email address found for booking {booking.booking_id}, cannot send survey")
        return
    
    try:
        # Generate secure token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(hours=hotel_config.token_expiry_hours)
        
        # Revoke any existing active tokens for this booking
        BookingSurveyToken.objects.filter(
            booking=booking,
            used_at__isnull=True,
            status='ACTIVE'
        ).update(status='REVOKED', revoked_at=timezone.now())
        
        # Create new token with config snapshot
        token = BookingSurveyToken.objects.create(
            booking=booking,
            token_hash=token_hash,
            expires_at=expires_at,
            sent_to_email=target_email,
            config_snapshot_enabled=hotel_config.fields_enabled.copy(),
            config_snapshot_required=hotel_config.fields_required.copy(),
            config_snapshot_send_mode=hotel_config.send_mode
        )
        
        # Send survey email
        base_domain = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
        survey_url = f"{base_domain}/guest/hotel/{booking.hotel.slug}/survey?token={raw_token}"
        
        subject = hotel_config.email_subject_template or f"Share your experience at {booking.hotel.name}"
        
        if hotel_config.email_body_template:
            message = hotel_config.email_body_template.format(
                guest_name=booking.primary_guest_name or 'Guest',
                hotel_name=booking.hotel.name,
                booking_id=booking.booking_id,
                survey_url=survey_url,
                expiry_days=hotel_config.token_expiry_hours // 24
            )
        else:
            message = f"""
Dear {booking.primary_guest_name or 'Guest'},

Thank you for staying with us at {booking.hotel.name}. We'd love to hear about your experience.

Booking: {booking.booking_id}
Dates: {booking.check_in} to {booking.check_out}

Please take a moment to share your feedback: {survey_url}

This survey takes less than a minute and helps us improve our service.

Your feedback link expires in {hotel_config.token_expiry_hours // 24} days.

Best regards,
{booking.hotel.name} Team
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[target_email],
            fail_silently=False,
        )
        
        # Update booking audit fields
        booking.survey_sent_at = timezone.now()
        booking.survey_last_sent_to = target_email
        booking.save(update_fields=['survey_sent_at', 'survey_last_sent_to'])
        
        logger.info(f"Survey email sent immediately to {target_email} for booking {booking.booking_id}")
        
    except Exception as e:
        logger.error(f"Failed to send immediate survey email for booking {booking.booking_id}: {e}")
        # If email fails, revoke the token for security
        if 'token' in locals():
            token.status = 'REVOKED'
            token.revoked_at = timezone.now()
            token.save()


def _schedule_survey_email(booking, hotel_config):
    """Schedule survey email for later delivery"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Check if survey already sent or scheduled to prevent duplicates
    if booking.survey_sent_at or booking.survey_send_at:
        logger.info(f"Survey already sent or scheduled for booking {booking.booking_id}, skipping")
        return
    
    # Schedule for later
    send_at = timezone.now() + timedelta(hours=hotel_config.delay_hours)
    booking.survey_send_at = send_at
    booking.save(update_fields=['survey_send_at'])
    
    logger.info(f"Survey email scheduled for {send_at} for booking {booking.booking_id}")