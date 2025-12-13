"""
Booking Integrity Service for HotelMate Phase 3.5
Auto-healing service for booking party and in-house guest integrity.

This service provides functions to detect and repair broken data states:
1. BookingGuest party integrity (PRIMARY missing/multiple, role mismatches)
2. In-house Guest integrity (for checked-in bookings)  
3. Room occupancy flag integrity

All operations are hotel-scoped and use database transactions for atomicity.
"""

import logging
from typing import Dict, List, Any, Optional
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone

from hotel.models import Hotel, RoomBooking, BookingGuest
from guests.models import Guest
from rooms.models import Room

logger = logging.getLogger(__name__)


class BookingIntegrityService:
    """
    Service class for detecting and healing booking data integrity issues.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")


def heal_booking_party(booking: RoomBooking, notify: bool = True) -> Dict[str, Any]:
    """
    Fix BookingGuest party issues for a single booking.
    
    Repairs:
    - Missing PRIMARY BookingGuest
    - Multiple PRIMARY BookingGuests (keeps most recent, demotes others)
    - PRIMARY mismatch with booking.primary_* fields
    - Ensures all party members have is_staying=True
    
    Args:
        booking: RoomBooking instance to heal
        notify: Whether to send realtime notifications (default True)
        
    Returns:
        dict: Report with counts of changes made
        {
            "created": 0,
            "updated": 0, 
            "deleted": 0,
            "demoted": 0,
            "notes": []
        }
    """
    report = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "demoted": 0,
        "notes": []
    }
    
    with transaction.atomic():
        # Get all party members for this booking
        party_members = list(booking.party.all().select_related('booking'))
        primary_members = [guest for guest in party_members if guest.role == 'PRIMARY']
        
        # A) Handle missing PRIMARY
        if not primary_members:
            if booking.primary_first_name and booking.primary_last_name:
                primary_guest = BookingGuest.objects.create(
                    booking=booking,
                    role='PRIMARY',
                    first_name=booking.primary_first_name,
                    last_name=booking.primary_last_name,
                    email=booking.primary_email or '',
                    phone=booking.primary_phone or '',
                    is_staying=True
                )
                report["created"] += 1
                report["notes"].append(f"Created missing PRIMARY guest: {primary_guest.full_name}")
            else:
                report["notes"].append("Cannot create PRIMARY guest: booking missing primary_first_name or primary_last_name")
        
        # B) Handle multiple PRIMARYs (keep most recent, demote others)
        elif len(primary_members) > 1:
            # Keep the most recently created PRIMARY
            primary_to_keep = max(primary_members, key=lambda g: g.created_at)
            primaries_to_demote = [g for g in primary_members if g.id != primary_to_keep.id]
            
            for guest in primaries_to_demote:
                guest.role = 'COMPANION'
                guest.save()
                report["demoted"] += 1
                report["notes"].append(f"Demoted duplicate PRIMARY to COMPANION: {guest.full_name}")
        
        # C) Ensure PRIMARY matches booking primary_* fields
        if primary_members:
            primary_guest = primary_members[0] if len(primary_members) == 1 else max(primary_members, key=lambda g: g.created_at)
            
            needs_update = False
            if primary_guest.first_name != booking.primary_first_name:
                primary_guest.first_name = booking.primary_first_name or primary_guest.first_name
                needs_update = True
            if primary_guest.last_name != booking.primary_last_name:
                primary_guest.last_name = booking.primary_last_name or primary_guest.last_name  
                needs_update = True
            if primary_guest.email != (booking.primary_email or ''):
                primary_guest.email = booking.primary_email or ''
                needs_update = True
            if primary_guest.phone != (booking.primary_phone or ''):
                primary_guest.phone = booking.primary_phone or ''
                needs_update = True
                
            if needs_update:
                primary_guest.save()
                report["updated"] += 1
                report["notes"].append(f"Updated PRIMARY guest to match booking: {primary_guest.full_name}")
        
        # D) Ensure all party members have is_staying=True
        for guest in party_members:
            if not guest.is_staying:
                guest.is_staying = True
                guest.save()
                report["updated"] += 1
                report["notes"].append(f"Set is_staying=True for party member: {guest.full_name}")
    
    # Send notification if changes were made and notify is enabled
    if notify and any(report[k] > 0 for k in ["created", "updated", "deleted", "demoted"]):
        try:
            from notifications.notification_manager import NotificationManager
            notification_manager = NotificationManager()
            notification_manager.realtime_booking_party_healed(booking)
        except Exception as e:
            logger.warning(f"Failed to send party healing notification: {e}")
            report["notes"].append(f"Notification failed: {e}")
    
    return report


def heal_booking_inhouse_guests(booking: RoomBooking, notify: bool = True) -> Dict[str, Any]:
    """
    Fix Guest records for checked-in bookings.
    
    Repairs:
    - Missing PRIMARY in-house Guest
    - Multiple PRIMARY in-house Guests (keeps one, demotes others)
    - Companion Guests without proper primary_guest link
    - Guests with wrong hotel, room, or dates
    - Missing booking_guest links for idempotency
    
    Args:
        booking: RoomBooking instance to heal
        notify: Whether to send realtime notifications (default True)
        
    Returns:
        dict: Report with counts of changes made
    """
    report = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "demoted": 0,
        "notes": []
    }
    
    # Only heal if booking is checked in (has assigned room and checked_in_at)
    if not booking.assigned_room or not booking.checked_in_at:
        report["notes"].append("Booking not checked in - skipping in-house guest healing")
        return report
    
    with transaction.atomic():
        # Get all in-house guests linked to this booking
        inhouse_guests = list(booking.guests.all().select_related('booking', 'room', 'hotel', 'booking_guest'))
        primary_guests = [guest for guest in inhouse_guests if guest.guest_type == 'PRIMARY']
        
        # Get booking party members for reference
        party_members = list(booking.party.all())
        primary_party_member = next((p for p in party_members if p.role == 'PRIMARY'), None)
        
        # A) Ensure exactly 1 PRIMARY in-house Guest
        if not primary_guests:
            # Create PRIMARY from PRIMARY BookingGuest if available
            if primary_party_member:
                primary_guest = Guest.objects.create(
                    hotel=booking.hotel,
                    first_name=primary_party_member.first_name,
                    last_name=primary_party_member.last_name,
                    room=booking.assigned_room,
                    check_in_date=booking.check_in,
                    check_out_date=booking.check_out,
                    booking=booking,
                    guest_type='PRIMARY',
                    booking_guest=primary_party_member
                )
                # Update room occupancy
                booking.assigned_room.is_occupied = True
                booking.assigned_room.save()
                
                report["created"] += 1
                report["notes"].append(f"Created missing PRIMARY in-house guest: {primary_guest}")
        
        elif len(primary_guests) > 1:
            # Keep the first PRIMARY, demote others to COMPANION or detach
            primary_to_keep = primary_guests[0]
            primaries_to_demote = primary_guests[1:]
            
            for guest in primaries_to_demote:
                guest.guest_type = 'COMPANION'
                guest.primary_guest = primary_to_keep
                guest.save()
                report["demoted"] += 1
                report["notes"].append(f"Demoted duplicate PRIMARY to COMPANION: {guest}")
        
        # B) Ensure every COMPANION Guest points to the PRIMARY Guest
        if primary_guests:
            primary_guest = primary_guests[0]
            companion_guests = [g for g in inhouse_guests if g.guest_type == 'COMPANION']
            
            for companion in companion_guests:
                if companion.primary_guest != primary_guest:
                    companion.primary_guest = primary_guest
                    companion.save()
                    report["updated"] += 1
                    report["notes"].append(f"Fixed primary_guest link for companion: {companion}")
        
        # C) Ensure all booking-linked Guests have correct properties
        for guest in inhouse_guests:
            needs_update = False
            
            # Check hotel
            if guest.hotel != booking.hotel:
                guest.hotel = booking.hotel
                needs_update = True
                
            # Check room
            if guest.room != booking.assigned_room:
                guest.room = booking.assigned_room
                needs_update = True
                
            # Check dates
            if guest.check_in_date != booking.check_in:
                guest.check_in_date = booking.check_in
                needs_update = True
                
            if guest.check_out_date != booking.check_out:
                guest.check_out_date = booking.check_out
                needs_update = True
            
            if needs_update:
                guest.save()
                report["updated"] += 1
                report["notes"].append(f"Updated guest properties: {guest}")
        
        # D) Ensure idempotent mapping via booking_guest links
        for party_member in party_members:
            # Check if this party member has a corresponding in-house guest
            corresponding_guest = next(
                (g for g in inhouse_guests if g.booking_guest_id == party_member.id), 
                None
            )
            
            if not corresponding_guest:
                # Create missing in-house guest
                guest_type = 'PRIMARY' if party_member.role == 'PRIMARY' else 'COMPANION'
                primary_guest = primary_guests[0] if primary_guests and guest_type == 'COMPANION' else None
                
                new_guest = Guest.objects.create(
                    hotel=booking.hotel,
                    first_name=party_member.first_name,
                    last_name=party_member.last_name,
                    room=booking.assigned_room,
                    check_in_date=booking.check_in,
                    check_out_date=booking.check_out,
                    booking=booking,
                    guest_type=guest_type,
                    primary_guest=primary_guest,
                    booking_guest=party_member
                )
                report["created"] += 1
                report["notes"].append(f"Created missing in-house guest for party member: {new_guest}")
    
    # Send notification if changes were made and notify is enabled
    if notify and any(report[k] > 0 for k in ["created", "updated", "deleted", "demoted"]) and primary_guests:
        try:
            from notifications.notification_manager import NotificationManager
            notification_manager = NotificationManager()
            notification_manager.realtime_booking_guests_healed(booking, primary_guests[0])
        except Exception as e:
            logger.warning(f"Failed to send guests healing notification: {e}")
            report["notes"].append(f"Notification failed: {e}")
    
    return report


def heal_room_occupancy(hotel: Hotel, notify: bool = True) -> Dict[str, Any]:
    """
    Fix room.is_occupied flags for all rooms in a hotel.
    
    Sets room.is_occupied = room.guests_in_room.exists() for each room,
    saving only if the value changed.
    
    Args:
        hotel: Hotel instance to heal rooms for
        notify: Whether to send realtime notifications (default True)
        
    Returns:
        dict: Report with counts of changes made
    """
    report = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "demoted": 0,
        "notes": []
    }
    
    with transaction.atomic():
        # Get all rooms for this hotel with their guest count
        rooms = Room.objects.filter(hotel=hotel).prefetch_related('guests_in_room')
        
        for room in rooms:
            should_be_occupied = room.guests_in_room.exists()
            
            if room.is_occupied != should_be_occupied:
                room.is_occupied = should_be_occupied
                room.save()
                report["updated"] += 1
                
                status = "occupied" if should_be_occupied else "unoccupied" 
                report["notes"].append(f"Room {room.room_number} marked as {status}")
                
                # Send individual room occupancy notification
                if notify:
                    try:
                        from notifications.notification_manager import NotificationManager
                        notification_manager = NotificationManager()
                        notification_manager.realtime_room_occupancy_updated(room)
                    except Exception as e:
                        logger.warning(f"Failed to send room occupancy notification for room {room.room_number}: {e}")
    
    return report


def heal_all_bookings_for_hotel(hotel: Hotel, notify: bool = True) -> Dict[str, Any]:
    """
    Heal all booking integrity issues for a hotel.
    
    Args:
        hotel: Hotel instance to heal
        notify: Whether to send realtime notifications (default True)
        
    Returns:
        dict: Combined report for all operations
    """
    total_report = {
        "created": 0,
        "updated": 0,
        "deleted": 0,
        "demoted": 0,
        "notes": [],
        "bookings_processed": 0,
        "party_reports": [],
        "inhouse_reports": [],
        "room_report": {}
    }
    
    # Get all bookings for this hotel
    bookings = RoomBooking.objects.filter(hotel=hotel).select_related('hotel', 'assigned_room').prefetch_related('party', 'guests')
    
    for booking in bookings:
        # Heal party integrity (individual notifications handled within function)
        party_report = heal_booking_party(booking, notify=notify)
        total_report["party_reports"].append({
            "booking_id": booking.booking_id,
            "report": party_report
        })
        
        # Heal in-house guests integrity (individual notifications handled within function)
        inhouse_report = heal_booking_inhouse_guests(booking, notify=notify)
        total_report["inhouse_reports"].append({
            "booking_id": booking.booking_id,
            "report": inhouse_report
        })
        
        # Aggregate counts
        for key in ["created", "updated", "deleted", "demoted"]:
            total_report[key] += party_report[key] + inhouse_report[key]
        
        total_report["notes"].extend([f"[{booking.booking_id}] {note}" for note in party_report["notes"]])
        total_report["notes"].extend([f"[{booking.booking_id}] {note}" for note in inhouse_report["notes"]])
        
        total_report["bookings_processed"] += 1
    
    # Heal room occupancy (individual room notifications handled within function)
    room_report = heal_room_occupancy(hotel, notify=notify)
    total_report["room_report"] = room_report
    total_report["updated"] += room_report["updated"]
    total_report["notes"].extend([f"[ROOMS] {note}" for note in room_report["notes"]])
    
    # Send overall healing completion notification if changes were made and notify is enabled
    if notify and any(total_report[k] > 0 for k in ["created", "updated", "deleted", "demoted"]):
        try:
            from notifications.notification_manager import NotificationManager
            notification_manager = NotificationManager()
            notification_manager.realtime_booking_integrity_healed(hotel, total_report)
        except Exception as e:
            logger.warning(f"Failed to send overall healing notification: {e}")
            total_report["notes"].append(f"Overall notification failed: {e}")
    
    return total_report


def assert_booking_integrity(booking: RoomBooking) -> None:
    """
    Assert that a booking has proper integrity.
    Raises AssertionError with useful message if booking is inconsistent.
    
    Used for tests and CI verification.
    
    Args:
        booking: RoomBooking instance to check
        
    Raises:
        AssertionError: If booking has integrity issues
    """
    errors = []
    
    # Check party integrity
    party_members = list(booking.party.all())
    primary_members = [guest for guest in party_members if guest.role == 'PRIMARY']
    
    if not primary_members:
        errors.append("Missing PRIMARY BookingGuest")
    elif len(primary_members) > 1:
        errors.append(f"Multiple PRIMARY BookingGuests found: {len(primary_members)}")
    else:
        primary = primary_members[0]
        if primary.first_name != booking.primary_first_name:
            errors.append(f"PRIMARY guest first_name '{primary.first_name}' != booking.primary_first_name '{booking.primary_first_name}'")
        if primary.last_name != booking.primary_last_name:
            errors.append(f"PRIMARY guest last_name '{primary.last_name}' != booking.primary_last_name '{booking.primary_last_name}'")
    
    # Check that all party members have is_staying=True
    for guest in party_members:
        if not guest.is_staying:
            errors.append(f"Party member {guest.full_name} has is_staying=False")
    
    # Check in-house guest integrity (if checked in)
    if booking.assigned_room and booking.checked_in_at:
        inhouse_guests = list(booking.guests.all())
        primary_inhouse = [g for g in inhouse_guests if g.guest_type == 'PRIMARY']
        
        if not primary_inhouse:
            errors.append("Missing PRIMARY in-house Guest for checked-in booking")
        elif len(primary_inhouse) > 1:
            errors.append(f"Multiple PRIMARY in-house Guests: {len(primary_inhouse)}")
        
        # Check companion links
        if primary_inhouse:
            primary_guest = primary_inhouse[0]
            companions = [g for g in inhouse_guests if g.guest_type == 'COMPANION']
            
            for companion in companions:
                if companion.primary_guest != primary_guest:
                    errors.append(f"Companion {companion} not linked to primary guest")
        
        # Check guest properties
        for guest in inhouse_guests:
            if guest.hotel != booking.hotel:
                errors.append(f"Guest {guest} has wrong hotel: {guest.hotel} != {booking.hotel}")
            if guest.room != booking.assigned_room:
                errors.append(f"Guest {guest} has wrong room: {guest.room} != {booking.assigned_room}")
            if guest.check_in_date != booking.check_in:
                errors.append(f"Guest {guest} has wrong check_in_date")
            if guest.check_out_date != booking.check_out:
                errors.append(f"Guest {guest} has wrong check_out_date")
    
    if errors:
        error_msg = f"Booking {booking.booking_id} integrity issues:\n" + "\n".join(f"- {error}" for error in errors)
        raise AssertionError(error_msg)


def check_hotel_integrity(hotel: Hotel) -> List[Dict[str, Any]]:
    """
    Check integrity for all bookings in a hotel without fixing anything.
    Returns a list of integrity issues found.
    
    Args:
        hotel: Hotel instance to check
        
    Returns:
        List of dictionaries describing integrity issues found
    """
    issues = []
    
    bookings = RoomBooking.objects.filter(hotel=hotel).select_related('hotel', 'assigned_room').prefetch_related('party', 'guests')
    
    for booking in bookings:
        try:
            assert_booking_integrity(booking)
        except AssertionError as e:
            issues.append({
                "booking_id": booking.booking_id,
                "error": str(e)
            })
    
    return issues