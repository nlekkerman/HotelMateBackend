"""
Overstay management services for room bookings.

Business logic for detecting, acknowledging, and extending overstays.
Timezone-safe and hotel-scoped operations.
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import pytz
import stripe

from hotel.models import Hotel, RoomBooking, OverstayIncident, BookingExtension, HotelAccessConfig
from rooms.models import Room
from rooms.models import Room, RoomType
from notifications.pusher_utils import pusher_client

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def compute_checkout_deadline_at(booking) -> datetime:
    """
    Compute the TRUE checkout deadline for a booking using hotel configuration.
    
    ❗ INVARIANT: Checkout/overstay logic must NEVER use hardcoded times (12:00/noon).
    ❗ All checkout deadline calculations MUST go through this function.
    
    Args:
        booking: RoomBooking instance with check_out date and hotel
        
    Returns:
        timezone-aware UTC datetime representing the configured checkout deadline
        (WITHOUT grace period - grace only affects risk level calculations)
    """
    hotel = booking.hotel
    
    # Get checkout time from hotel access config
    try:
        access_config = hotel.access_config
        checkout_time = access_config.standard_checkout_time
    except (AttributeError, HotelAccessConfig.DoesNotExist):
        # Fallback to default 11:00 AM if no config
        from datetime import time
        checkout_time = time(11, 0)
        logger.warning(f"No access config for hotel {hotel.id}, using default 11:00 AM checkout")
    
    # Use hotel's timezone object (single source of truth)
    hotel_tz = hotel.timezone_obj
    
    # Create naive datetime for checkout time on checkout date
    checkout_naive = datetime.combine(booking.check_out, checkout_time)
    
    # Localize to hotel timezone (handles DST)
    checkout_local = hotel_tz.localize(checkout_naive)
    
    # Convert to UTC
    checkout_utc = checkout_local.astimezone(pytz.UTC)
    
    return checkout_utc


def detect_overstays(hotel: Hotel, now_utc: datetime) -> int:
    """
    Detect and flag new overstays using hotel's configured checkout deadline.
    Only creates incidents for bookings not already flagged.
    
    Args:
        hotel: Hotel instance
        now_utc: Current UTC datetime for detection timestamp
        
    Returns:
        Number of new overstays detected and flagged
    """
    detected_count = 0
    current_date_utc = now_utc.date()
    
    # Find IN_HOUSE bookings that should have checked out
    # IN_HOUSE = checked_in_at is not null AND checked_out_at is null
    in_house_bookings = RoomBooking.objects.filter(
        hotel=hotel,
        checked_in_at__isnull=False,  # Must be checked in
        checked_out_at__isnull=True,  # Still checked in (not checked out)
        assigned_room__isnull=False,  # Must have assigned room
        check_out__lte=current_date_utc  # Checkout date has passed (today or earlier)
    ).select_related('assigned_room', 'hotel', 'room_type')
    
    for booking in in_house_bookings:
        try:
            with transaction.atomic():
                # Lock booking for update with skip_locked for concurrency safety
                locked_booking = RoomBooking.objects.select_for_update(
                    skip_locked=True
                ).filter(id=booking.id).first()
                
                # Skip if locked by another process
                if not locked_booking:
                    continue
                
                # Re-check IN_HOUSE status after lock (race condition protection)
                if not locked_booking.checked_in_at or locked_booking.checked_out_at:
                    continue
                
                # Check if checkout deadline has passed using hotel configuration
                checkout_deadline_utc = compute_checkout_deadline_at(locked_booking)
                
                if now_utc >= checkout_deadline_utc:
                    # Check if already has active incident
                    existing_incident = OverstayIncident.objects.filter(
                        booking=locked_booking,
                        status__in=['OPEN', 'ACKED']
                    ).first()
                    
                    if not existing_incident:
                        # Create new incident
                        incident = OverstayIncident.objects.create(
                            hotel=hotel,
                            booking=locked_booking,
                            expected_checkout_date=locked_booking.check_out,
                            detected_at=now_utc,
                            status='OPEN',
                            severity='MEDIUM',
                            meta={
                                'room_number': locked_booking.assigned_room.room_number,
                                'guest_name': f"{locked_booking.primary_first_name} {locked_booking.primary_last_name}",
                                'room_type': locked_booking.room_type.name if locked_booking.room_type else None
                            }
                        )
                        
                        # Emit realtime event
                        _emit_overstay_flagged(incident)
                        detected_count += 1
                        
                        logger.info(f"Flagged overstay: booking {locked_booking.booking_id}, room {locked_booking.assigned_room.room_number}")
                        
        except Exception as e:
            logger.error(f"Error processing booking {booking.booking_id}: {e}")
            # Continue processing other bookings
            continue
    
    if detected_count > 0:
        logger.info(f"Hotel {hotel.slug}: detected {detected_count} new overstays")
    
    return detected_count


def acknowledge_overstay(hotel: Hotel, booking: RoomBooking, staff_user, note: str, dismiss: bool = False) -> Dict:
    """
    Acknowledge overstay incident.
    Creates incident if none exists, updates existing one otherwise.
    
    Args:
        hotel: Hotel instance
        booking: RoomBooking instance
        staff_user: Staff user acknowledging
        note: Acknowledgment note
        dismiss: Whether to dismiss the overstay (mark as false positive)
        
    Returns:
        Dict with incident data and allowed actions
    """
    now_utc = timezone.now()
    
    # Get active incident or create new one
    # Only target OPEN incidents for acknowledgment (not RESOLVED/DISMISSED)
    incident = OverstayIncident.objects.filter(
        booking=booking,
        status='OPEN'
    ).first()
    
    created = False
    if not incident:
        # Create new incident if no OPEN incident exists
        incident = OverstayIncident.objects.create(
            hotel=hotel,
            booking=booking,
            expected_checkout_date=booking.check_out,
            detected_at=now_utc,
            status='OPEN',
            severity='MEDIUM',
            meta={
                'room_number': booking.assigned_room.room_number if booking.assigned_room else None,
                'guest_name': f"{booking.primary_first_name} {booking.primary_last_name}",
                'room_type': booking.room_type.name if booking.room_type else None
            }
        )
        created = True
    
    # Update acknowledgment or dismissal
    if dismiss:
        incident.status = 'DISMISSED'
        incident.dismissed_at = now_utc
        incident.dismissed_by = staff_user
        incident.dismissed_reason = note
    else:
        incident.status = 'ACKED'
        incident.acknowledged_at = now_utc
        incident.acknowledged_by = staff_user
        incident.acknowledged_note = note
    
    incident.save()
    
    # Emit realtime event
    _emit_overstay_acknowledged(incident, staff_user, dismiss)
    
    # Determine allowed actions
    allowed_actions = []
    if incident.status == 'ACKED':
        allowed_actions.extend(['EXTEND_OVERSTAY', 'DISMISS_OVERSTAY'])
    elif incident.status == 'OPEN':
        allowed_actions.extend(['EXTEND_OVERSTAY', 'DISMISS_OVERSTAY'])
    
    return {
        'booking_id': booking.booking_id,
        'overstay': {
            'status': incident.status,
            'detected_at': incident.detected_at.isoformat(),
            'acknowledged_at': incident.acknowledged_at.isoformat() if incident.acknowledged_at else None,
            'acknowledged_note': incident.acknowledged_note,
            'dismissed_at': incident.dismissed_at.isoformat() if incident.dismissed_at else None,
            'dismissed_reason': incident.dismissed_reason
        },
        'allowed_actions': allowed_actions
    }


def extend_overstay(hotel: Hotel, booking: RoomBooking, staff_user, new_checkout_date: Optional[date] = None, 
                   add_nights: Optional[int] = None, idempotency_key: Optional[str] = None) -> Dict:
    """
    Extend booking and resolve overstay with idempotency support.
    
    Args:
        hotel: Hotel instance
        booking: RoomBooking instance
        staff_user: Staff user performing extension
        new_checkout_date: New checkout date (exclusive with add_nights)
        add_nights: Number of nights to add (exclusive with new_checkout_date)
        idempotency_key: Optional idempotency key for duplicate prevention
        
    Returns:
        Dict with extension details, pricing, payment info
        
    Raises:
        ValueError: For validation errors
        ConflictError: For room conflicts
    """
    with transaction.atomic():
        # Lock booking for update
        booking = RoomBooking.objects.select_for_update().get(id=booking.id)
        now_utc = timezone.now()
        
        # Check for existing extension with same idempotency key
        if idempotency_key:
            existing_extension = BookingExtension.objects.filter(
                booking=booking,
                idempotency_key=idempotency_key
            ).first()
            
            if existing_extension:
                # Return previous successful response
                return _build_extension_response(existing_extension, booking)
        
        # Calculate new checkout date
        if new_checkout_date:
            final_checkout_date = new_checkout_date
            nights_added = (new_checkout_date - booking.check_out).days
        elif add_nights:
            final_checkout_date = booking.check_out + timedelta(days=add_nights)
            nights_added = add_nights
        else:
            raise ValueError("Either new_checkout_date or add_nights must be provided")
        
        if nights_added <= 0:
            raise ValueError("Extension must add at least 1 night")
        
        # Check for room conflicts
        conflicts = _check_room_conflicts(booking, booking.check_out, final_checkout_date)
        if conflicts:
            suggestions = get_room_suggestions(hotel, booking.check_out, final_checkout_date, 
                                             booking.room_type)
            raise ConflictError("Extension conflicts with an incoming reservation for this room.", 
                               conflicts, suggestions)
        
        # Calculate pricing
        pricing = _calculate_extension_pricing(booking, booking.check_out, final_checkout_date, nights_added)
        
        # Create payment intent
        payment_intent_id = _create_payment_intent(pricing['amount_delta'], pricing['currency'])
        
        # Create extension record
        extension = BookingExtension.objects.create(
            hotel=hotel,
            booking=booking,
            created_by=staff_user,
            old_checkout_date=booking.check_out,
            new_checkout_date=final_checkout_date,
            added_nights=nights_added,
            pricing_snapshot=pricing,
            amount_delta=Decimal(pricing['amount_delta']),
            currency=pricing['currency'],
            payment_intent_id=payment_intent_id,
            idempotency_key=idempotency_key,
            status='PENDING_PAYMENT'
        )
        
        # Update booking checkout date
        old_checkout = booking.check_out
        booking.check_out = final_checkout_date
        booking.save(update_fields=['check_out', 'updated_at'])
        
        # Resolve overstay incident if applicable
        _resolve_overstay_if_applicable(booking, staff_user, now_utc)
        
        # Emit realtime events
        _emit_overstay_extended(booking, extension, old_checkout, final_checkout_date)
        _emit_booking_updated(booking, ['checkout_date'], final_checkout_date)
        
        logger.info(f"Extended booking {booking.booking_id}: {old_checkout} -> {final_checkout_date}")
        
        return _build_extension_response(extension, booking)


def get_room_suggestions(hotel: Hotel, start_date: date, end_date: date, room_type: Optional[RoomType] = None) -> List[Dict]:
    """
    Find available rooms for conflict resolution.
    
    Args:
        hotel: Hotel instance
        start_date: Start date for availability check
        end_date: End date for availability check (exclusive)
        room_type: Preferred room type
        
    Returns:
        List of available room dictionaries
    """
    # First try same room type
    available_rooms = []
    
    if room_type:
        same_type_rooms = Room.objects.filter(
            hotel=hotel,
            room_type=room_type,
            is_active=True,
            is_out_of_order=False
        ).exclude(
            # Exclude rooms with conflicting bookings
            room_bookings__check_in__lt=end_date,
            room_bookings__check_out__gt=start_date,
            room_bookings__status__in=['CONFIRMED', 'IN_HOUSE']
        ).distinct()
        
        for room in same_type_rooms[:3]:  # Limit suggestions
            available_rooms.append({
                'room_id': room.id,
                'room_number': str(room.room_number),
                'room_type': room_type.name
            })
    
    # If no same-type rooms, suggest any available
    if len(available_rooms) < 3:
        any_rooms = Room.objects.filter(
            hotel=hotel,
            is_active=True,
            is_out_of_order=False
        ).exclude(
            room_bookings__check_in__lt=end_date,
            room_bookings__check_out__gt=start_date,
            room_bookings__status__in=['CONFIRMED', 'IN_HOUSE']
        ).select_related('room_type').distinct()[:5]
        
        for room in any_rooms:
            if len(available_rooms) >= 5:
                break
            if not any(r['room_id'] == room.id for r in available_rooms):
                available_rooms.append({
                    'room_id': room.id,
                    'room_number': str(room.room_number),
                    'room_type': room.room_type.name if room.room_type else 'Unknown'
                })
    
    return available_rooms


def _check_room_conflicts(booking: RoomBooking, start_date: date, end_date: date) -> List[Dict]:
    """Check for room conflicts in the extension period."""
    if not booking.assigned_room:
        return []
    
    conflicting_bookings = RoomBooking.objects.filter(
        assigned_room=booking.assigned_room,
        check_in__lt=end_date,
        check_out__gt=start_date,
        status__in=['CONFIRMED', 'IN_HOUSE']
    ).exclude(id=booking.id)
    
    conflicts = []
    for conflict_booking in conflicting_bookings:
        conflicts.append({
            'room_id': booking.assigned_room.id,
            'conflicting_booking_id': conflict_booking.booking_id,
            'starts': conflict_booking.check_in.isoformat(),
            'ends': conflict_booking.check_out.isoformat()
        })
    
    return conflicts


def _calculate_extension_pricing(booking: RoomBooking, start_date: date, end_date: date, nights_added: int) -> Dict:
    """Calculate pricing for extension using original booking's rate."""
    # This is a simplified pricing calculation
    # In a real implementation, you'd use the hotel's pricing service
    
    # Get the original nightly rate from the booking
    if hasattr(booking, 'total_amount') and booking.total_amount:
        original_nights = (booking.check_out - booking.check_in).days
        if original_nights > 0:
            nightly_rate = booking.total_amount / original_nights
        else:
            nightly_rate = Decimal('120.00')  # Fallback rate
    else:
        nightly_rate = Decimal('120.00')  # Fallback rate
    
    # Build nightly breakdown
    nightly_breakdown = []
    current_date = start_date
    
    for i in range(nights_added):
        nightly_breakdown.append({
            'date': current_date.isoformat(),
            'amount': str(nightly_rate)
        })
        current_date += timedelta(days=1)
    
    total_amount = nightly_rate * nights_added
    
    return {
        'currency': booking.currency if hasattr(booking, 'currency') else 'EUR',
        'added_nights': nights_added,
        'nightly': nightly_breakdown,
        'amount_delta': str(total_amount)
    }


def _create_payment_intent(amount_delta: str, currency: str) -> str:
    """Create Stripe payment intent for extension payment."""
    try:
        # Convert to cents for Stripe
        amount_cents = int(float(amount_delta) * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            confirmation_method='manual',  # Requires frontend confirmation
            capture_method='automatic'
        )
        
        return intent.id
    except Exception as e:
        logger.error(f"Failed to create payment intent: {e}")
        return f"pi_mock_{timezone.now().timestamp()}"  # Mock ID for development


def _resolve_overstay_if_applicable(booking: RoomBooking, staff_user, now_utc: datetime):
    """Resolve overstay incident if booking is no longer overstay."""
    # Check if there's an active incident
    incident = OverstayIncident.objects.filter(
        booking=booking,
        status__in=['OPEN', 'ACKED']
    ).first()
    
    if not incident:
        return
    
    # Check if booking is still overstay under configured checkout deadline
    checkout_deadline_utc = compute_checkout_deadline_at(booking)
    
    # Resolve if new checkout date is in future OR today but before checkout deadline
    should_resolve = (
        booking.check_out > now_utc.date() or
        (booking.check_out == now_utc.date() and now_utc < checkout_deadline_utc)
    )
    
    if should_resolve:
        incident.status = 'RESOLVED'
        incident.resolved_at = now_utc
        incident.resolved_by = staff_user
        incident.resolution_note = f"Booking extended to {booking.check_out}"
        incident.save()


def _build_extension_response(extension: BookingExtension, booking: RoomBooking) -> Dict:
    """Build standardized extension response."""
    # Get overstay incident if exists
    incident = OverstayIncident.objects.filter(booking=booking).first()
    overstay_data = None
    
    if incident:
        overstay_data = {
            'status': incident.status,
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None
        }
    
    return {
        'booking_id': booking.booking_id,
        'old_checkout_date': extension.old_checkout_date.isoformat(),
        'new_checkout_date': extension.new_checkout_date.isoformat(),
        'pricing': extension.pricing_snapshot,
        'payment': {
            'payment_required': True,
            'payment_intent_id': extension.payment_intent_id
        },
        'overstay': overstay_data
    }


def _emit_overstay_flagged(incident: OverstayIncident):
    """Emit realtime event for overstay flagged."""
    try:
        channel = f"{incident.hotel.slug}-staff-overstays"
        event_data = {
            'type': 'booking_overstay_flagged',
            'payload': {
                'hotel_slug': incident.hotel.slug,
                'booking_id': incident.booking.booking_id,
                'expected_checkout_date': incident.expected_checkout_date.isoformat(),
                'detected_at': incident.detected_at.isoformat(),
                'severity': incident.severity
            },
            'meta': {
                'event_id': f"evt_{incident.id}",
                'ts': timezone.now().isoformat()
            }
        }
        
        pusher_client.trigger(channel, 'booking_overstay_flagged', event_data)
    except Exception as e:
        logger.error(f"Failed to emit overstay_flagged event: {e}")


def _emit_overstay_acknowledged(incident: OverstayIncident, staff_user, dismissed: bool):
    """Emit realtime event for overstay acknowledged."""
    try:
        channel = f"{incident.hotel.slug}-staff-overstays"
        event_data = {
            'type': 'booking_overstay_acknowledged',
            'payload': {
                'hotel_slug': incident.hotel.slug,
                'booking_id': incident.booking.booking_id,
                'acknowledged_by': str(staff_user.id),
                'acknowledged_note': incident.acknowledged_note if not dismissed else incident.dismissed_reason,
                'dismissed': dismissed
            },
            'meta': {
                'event_id': f"evt_{incident.id}_ack",
                'ts': timezone.now().isoformat()
            }
        }
        
        pusher_client.trigger(channel, 'booking_overstay_acknowledged', event_data)
    except Exception as e:
        logger.error(f"Failed to emit overstay_acknowledged event: {e}")


def _emit_overstay_extended(booking: RoomBooking, extension: BookingExtension, old_checkout: date, new_checkout: date):
    """Emit realtime event for overstay extended."""
    try:
        channel = f"{booking.hotel.slug}-staff-overstays"
        event_data = {
            'type': 'booking_overstay_extended',
            'payload': {
                'hotel_slug': booking.hotel.slug,
                'booking_id': booking.booking_id,
                'old_checkout_date': old_checkout.isoformat(),
                'new_checkout_date': new_checkout.isoformat(),
                'added_nights': extension.added_nights,
                'amount_delta': str(extension.amount_delta),
                'currency': extension.currency
            },
            'meta': {
                'event_id': f"evt_{extension.id}",
                'ts': timezone.now().isoformat()
            }
        }
        
        pusher_client.trigger(channel, 'booking_overstay_extended', event_data)
    except Exception as e:
        logger.error(f"Failed to emit overstay_extended event: {e}")


def _emit_booking_updated(booking: RoomBooking, changes: List[str], new_checkout_date: date):
    """Emit realtime event for booking updated."""
    try:
        channel = f"{booking.hotel.slug}-staff-bookings"
        event_data = {
            'type': 'booking_updated',
            'payload': {
                'hotel_slug': booking.hotel.slug,
                'booking_id': booking.booking_id,
                'changes': changes,
                'new_checkout_date': new_checkout_date.isoformat()
            },
            'meta': {
                'event_id': f"evt_{booking.id}_updated",
                'ts': timezone.now().isoformat()
            }
        }
        
        pusher_client.trigger(channel, 'booking_updated', event_data)
    except Exception as e:
        logger.error(f"Failed to emit booking_updated event: {e}")


class ConflictError(Exception):
    """Exception raised when extension conflicts with existing bookings."""
    
    def __init__(self, message: str, conflicts: List[Dict], suggestions: List[Dict]):
        self.message = message
        self.conflicts = conflicts
        self.suggestions = suggestions
        super().__init__(self.message)