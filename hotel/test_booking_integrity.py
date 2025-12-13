"""
Tests for Phase 3.5 Booking Integrity Auto-Heal System

Tests cover:
1. BookingGuest party integrity issues and healing
2. In-house Guest integrity issues and healing  
3. Room occupancy flag integrity and healing
4. Integration tests for full healing workflow
5. NotificationManager integration
6. Management command functionality
"""

from django.test import TestCase
from django.db import transaction
from django.utils import timezone
from unittest.mock import patch, MagicMock

from hotel.models import Hotel, RoomBooking, BookingGuest
from guests.models import Guest
from rooms.models import Room, RoomType
from staff.models import Department, Role, Staff
from django.contrib.auth.models import User

from hotel.services.booking_integrity import (
    heal_booking_party,
    heal_booking_inhouse_guests,
    heal_room_occupancy,
    heal_all_bookings_for_hotel,
    assert_booking_integrity,
    check_hotel_integrity
)


class BookingIntegrityTestCase(TestCase):
    """Base test case with common setup for booking integrity tests."""
    
    def setUp(self):
        """Set up test hotel, rooms, and basic data."""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            starting_price_from=100.00
        )
        
        # Create rooms
        self.room1 = Room.objects.create(
            hotel=self.hotel,
            room_number=101,
            room_type=self.room_type
        )
        
        self.room2 = Room.objects.create(
            hotel=self.hotel,
            room_number=102,
            room_type=self.room_type
        )
        
        # Create a basic valid booking for reference
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            adults=2,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="123-456-7890"
        )


class BookingPartyIntegrityTests(BookingIntegrityTestCase):
    """Tests for BookingGuest party integrity healing."""
    
    def test_heal_missing_primary_guest(self):
        """Test healing when PRIMARY BookingGuest is missing."""
        # Ensure booking has no party members
        self.booking.party.all().delete()
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 1)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify PRIMARY guest was created correctly
        primary_guest = self.booking.party.filter(role='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        self.assertEqual(primary_guest.first_name, "John")
        self.assertEqual(primary_guest.last_name, "Doe")
        self.assertEqual(primary_guest.email, "john@example.com")
        self.assertTrue(primary_guest.is_staying)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
        
        # Verify notification was called
        mock_nm.return_value.realtime_booking_party_healed.assert_called_once_with(self.booking)
    
    def test_heal_multiple_primary_guests(self):
        """Test healing when multiple PRIMARY BookingGuests exist."""
        # Create multiple PRIMARY guests
        primary1 = BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name="John",
            last_name="Doe",
            is_staying=True
        )
        
        primary2 = BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name="Jane",
            last_name="Doe",
            is_staying=True
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 1)  # One PRIMARY demoted to COMPANION
        
        # Verify only one PRIMARY remains
        primary_guests = self.booking.party.filter(role='PRIMARY')
        self.assertEqual(primary_guests.count(), 1)
        
        # Verify the more recent one was kept
        remaining_primary = primary_guests.first()
        self.assertEqual(remaining_primary.id, primary2.id)  # More recently created
        
        # Verify the other was demoted
        demoted_guest = BookingGuest.objects.get(id=primary1.id)
        self.assertEqual(demoted_guest.role, 'COMPANION')
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_primary_mismatch_with_booking_fields(self):
        """Test healing when PRIMARY guest doesn't match booking primary_* fields."""
        # Create PRIMARY guest with wrong info
        primary_guest = BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name="Wrong",
            last_name="Name",
            email="wrong@example.com",
            is_staying=True
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 1)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify PRIMARY guest was updated to match booking
        primary_guest.refresh_from_db()
        self.assertEqual(primary_guest.first_name, "John")
        self.assertEqual(primary_guest.last_name, "Doe")
        self.assertEqual(primary_guest.email, "john@example.com")
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_party_member_not_staying(self):
        """Test healing when party member has is_staying=False."""
        # Create valid PRIMARY guest
        primary_guest = BookingGuest.objects.create(
            booking=self.booking,
            role='PRIMARY',
            first_name="John",
            last_name="Doe",
            is_staying=True
        )
        
        # Create COMPANION with is_staying=False
        companion = BookingGuest.objects.create(
            booking=self.booking,
            role='COMPANION',
            first_name="Jane",
            last_name="Doe",
            is_staying=False  # This is wrong
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 1)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify companion is now staying
        companion.refresh_from_db()
        self.assertTrue(companion.is_staying)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_booking_party_no_changes_needed(self):
        """Test healing when booking party is already correct."""
        # Create valid PRIMARY guest (automatically created in setUp via _sync_primary_booking_guest)
        primary_guest = self.booking.party.filter(role='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        
        # Verify booking is already correct
        assert_booking_integrity(self.booking)  # Should not raise
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking)
        
        # Verify no changes were made
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify no notification was sent (no changes)
        mock_nm.return_value.realtime_booking_party_healed.assert_not_called()


class InHouseGuestIntegrityTests(BookingIntegrityTestCase):
    """Tests for in-house Guest integrity healing."""
    
    def setUp(self):
        super().setUp()
        
        # Create a checked-in booking
        self.booking.assigned_room = self.room1
        self.booking.checked_in_at = timezone.now()
        self.booking.save()
        
        # Ensure PRIMARY party member exists
        self.primary_party_member = self.booking.party.filter(role='PRIMARY').first()
        if not self.primary_party_member:
            self.primary_party_member = BookingGuest.objects.create(
                booking=self.booking,
                role='PRIMARY',
                first_name="John",
                last_name="Doe",
                is_staying=True
            )
    
    def test_heal_missing_primary_inhouse_guest(self):
        """Test healing when PRIMARY in-house Guest is missing."""
        # Ensure no in-house guests exist
        self.booking.guests.all().delete()
        
        # Verify the problem exists (booking is checked in but no guests)
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_inhouse_guests(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 1)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify PRIMARY in-house guest was created
        primary_guest = self.booking.guests.filter(guest_type='PRIMARY').first()
        self.assertIsNotNone(primary_guest)
        self.assertEqual(primary_guest.first_name, "John")
        self.assertEqual(primary_guest.last_name, "Doe")
        self.assertEqual(primary_guest.hotel, self.hotel)
        self.assertEqual(primary_guest.room, self.room1)
        self.assertEqual(primary_guest.booking_guest, self.primary_party_member)
        
        # Verify room is marked as occupied
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.is_occupied)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
        
        # Verify notification was called
        mock_nm.return_value.realtime_booking_guests_healed.assert_called_once()
    
    def test_heal_multiple_primary_inhouse_guests(self):
        """Test healing when multiple PRIMARY in-house Guests exist."""
        # Create multiple PRIMARY in-house guests
        primary1 = Guest.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Doe",
            room=self.room1,
            check_in_date=self.booking.check_in,
            check_out_date=self.booking.check_out,
            booking=self.booking,
            guest_type='PRIMARY'
        )
        
        primary2 = Guest.objects.create(
            hotel=self.hotel,
            first_name="Jane",
            last_name="Doe",
            room=self.room1,
            check_in_date=self.booking.check_in,
            check_out_date=self.booking.check_out,
            booking=self.booking,
            guest_type='PRIMARY'
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_inhouse_guests(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 1)  # One PRIMARY demoted to COMPANION
        
        # Verify only one PRIMARY remains
        primary_guests = self.booking.guests.filter(guest_type='PRIMARY')
        self.assertEqual(primary_guests.count(), 1)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_companion_without_primary_link(self):
        """Test healing when COMPANION guest doesn't link to PRIMARY."""
        # Create PRIMARY in-house guest
        primary_guest = Guest.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Doe",
            room=self.room1,
            check_in_date=self.booking.check_in,
            check_out_date=self.booking.check_out,
            booking=self.booking,
            guest_type='PRIMARY'
        )
        
        # Create COMPANION without primary_guest link
        companion = Guest.objects.create(
            hotel=self.hotel,
            first_name="Jane",
            last_name="Doe",
            room=self.room1,
            check_in_date=self.booking.check_in,
            check_out_date=self.booking.check_out,
            booking=self.booking,
            guest_type='COMPANION',
            primary_guest=None  # This should link to primary_guest
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_inhouse_guests(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 1)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify companion now links to primary
        companion.refresh_from_db()
        self.assertEqual(companion.primary_guest, primary_guest)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_guest_with_wrong_properties(self):
        """Test healing when Guest has wrong hotel, room, or dates."""
        # Create another hotel and room
        other_hotel = Hotel.objects.create(name="Other Hotel", slug="other-hotel")
        other_room = Room.objects.create(hotel=other_hotel, room_number=201)
        
        # Create PRIMARY guest with wrong properties
        primary_guest = Guest.objects.create(
            hotel=other_hotel,  # Wrong hotel
            first_name="John",
            last_name="Doe",
            room=other_room,  # Wrong room
            check_in_date=self.booking.check_in + timezone.timedelta(days=1),  # Wrong date
            check_out_date=self.booking.check_out + timezone.timedelta(days=1),  # Wrong date
            booking=self.booking,
            guest_type='PRIMARY'
        )
        
        # Verify the problem exists
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_inhouse_guests(self.booking)
        
        # Verify the healing worked
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 1)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Verify guest properties were fixed
        primary_guest.refresh_from_db()
        self.assertEqual(primary_guest.hotel, self.hotel)
        self.assertEqual(primary_guest.room, self.room1)
        self.assertEqual(primary_guest.check_in_date, self.booking.check_in)
        self.assertEqual(primary_guest.check_out_date, self.booking.check_out)
        
        # Verify integrity is now correct
        assert_booking_integrity(self.booking)  # Should not raise
    
    def test_heal_not_checked_in_booking(self):
        """Test healing skips bookings that aren't checked in."""
        # Remove check-in status
        self.booking.assigned_room = None
        self.booking.checked_in_at = None
        self.booking.save()
        
        # Heal the booking
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_inhouse_guests(self.booking)
        
        # Verify no changes were made
        self.assertEqual(report["created"], 0)
        self.assertEqual(report["updated"], 0)
        self.assertEqual(report["deleted"], 0)
        self.assertEqual(report["demoted"], 0)
        
        # Should have explanatory note
        self.assertTrue(any("not checked in" in note for note in report["notes"]))


class RoomOccupancyIntegrityTests(BookingIntegrityTestCase):
    """Tests for room occupancy flag integrity healing."""
    
    def test_heal_room_occupancy_false_positive(self):
        """Test healing when room is marked occupied but has no guests."""
        # Mark room as occupied without guests
        self.room1.is_occupied = True
        self.room1.save()
        
        # Verify problem exists
        self.assertTrue(self.room1.is_occupied)
        self.assertFalse(self.room1.guests_in_room.exists())
        
        # Heal room occupancy
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_room_occupancy(self.hotel)
        
        # Verify the healing worked
        self.assertEqual(report["updated"], 1)
        
        # Verify room is now correctly marked as unoccupied
        self.room1.refresh_from_db()
        self.assertFalse(self.room1.is_occupied)
        
        # Verify notification was sent
        mock_nm.return_value.realtime_room_occupancy_updated.assert_called()
    
    def test_heal_room_occupancy_false_negative(self):
        """Test healing when room is marked unoccupied but has guests."""
        # Create guest in room but mark room as unoccupied
        Guest.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Doe",
            room=self.room1,
            check_in_date=timezone.now().date(),
            check_out_date=(timezone.now() + timezone.timedelta(days=1)).date()
        )
        
        self.room1.is_occupied = False
        self.room1.save()
        
        # Verify problem exists
        self.assertFalse(self.room1.is_occupied)
        self.assertTrue(self.room1.guests_in_room.exists())
        
        # Heal room occupancy
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_room_occupancy(self.hotel)
        
        # Verify the healing worked
        self.assertEqual(report["updated"], 1)
        
        # Verify room is now correctly marked as occupied
        self.room1.refresh_from_db()
        self.assertTrue(self.room1.is_occupied)
        
        # Verify notification was sent
        mock_nm.return_value.realtime_room_occupancy_updated.assert_called()
    
    def test_heal_room_occupancy_no_changes_needed(self):
        """Test healing when room occupancy flags are already correct."""
        # Ensure rooms are correctly marked
        self.room1.is_occupied = False
        self.room1.save()
        self.room2.is_occupied = False  
        self.room2.save()
        
        # Heal room occupancy
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_room_occupancy(self.hotel)
        
        # Verify no changes were made
        self.assertEqual(report["updated"], 0)
        
        # Verify no notifications were sent
        mock_nm.return_value.realtime_room_occupancy_updated.assert_not_called()


class IntegrationTests(BookingIntegrityTestCase):
    """Integration tests for complete healing workflow."""
    
    def test_heal_all_bookings_for_hotel(self):
        """Test healing all bookings for a hotel with multiple issues."""
        # Create a second booking with issues
        booking2 = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            adults=1,
            primary_first_name="Jane",
            primary_last_name="Smith",
            primary_email="jane@example.com",
            assigned_room=self.room2,
            checked_in_at=timezone.now()
        )
        
        # Create issues in booking1 (remove PRIMARY party member)
        self.booking.party.all().delete()
        
        # Create issues in booking2 (missing in-house guest, wrong room occupancy)
        booking2.guests.all().delete()
        self.room2.is_occupied = False
        self.room2.save()
        
        # Heal all bookings
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_all_bookings_for_hotel(self.hotel)
        
        # Verify overall report structure
        self.assertEqual(report["bookings_processed"], 2)
        self.assertGreater(report["created"], 0)
        self.assertGreater(report["updated"], 0)
        
        # Verify both bookings are now healthy
        assert_booking_integrity(self.booking)  # Should not raise
        assert_booking_integrity(booking2)  # Should not raise
        
        # Verify overall healing notification was sent
        mock_nm.return_value.realtime_booking_integrity_healed.assert_called_once()
    
    def test_check_hotel_integrity_function(self):
        """Test the check_hotel_integrity function for CI/testing."""
        # Create a booking with integrity issues
        self.booking.party.all().delete()  # Remove PRIMARY
        
        # Check integrity without fixing
        issues = check_hotel_integrity(self.hotel)
        
        # Verify issues were detected
        self.assertEqual(len(issues), 1)
        self.assertIn(self.booking.booking_id, issues[0]["booking_id"])
        self.assertIn("Missing PRIMARY BookingGuest", issues[0]["error"])
        
        # Fix the issues
        heal_all_bookings_for_hotel(self.hotel, notify=False)
        
        # Check again - should be clean now
        issues = check_hotel_integrity(self.hotel)
        self.assertEqual(len(issues), 0)


class NotificationIntegrationTests(BookingIntegrityTestCase):
    """Tests for NotificationManager integration."""
    
    def test_healing_disables_notifications_properly(self):
        """Test that healing functions respect the notify parameter."""
        # Create issues
        self.booking.party.all().delete()
        
        # Heal with notifications disabled
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            report = heal_booking_party(self.booking, notify=False)
        
        # Verify healing worked
        self.assertEqual(report["created"], 1)
        
        # Verify no notifications were sent
        mock_nm.return_value.realtime_booking_party_healed.assert_not_called()
    
    def test_notification_failure_handling(self):
        """Test that notification failures don't break healing."""
        # Create issues
        self.booking.party.all().delete()
        
        # Mock notification to fail
        with patch('hotel.services.booking_integrity.NotificationManager') as mock_nm:
            mock_nm.return_value.realtime_booking_party_healed.side_effect = Exception("Notification failed")
            
            # Healing should still work despite notification failure
            report = heal_booking_party(self.booking)
        
        # Verify healing worked despite notification failure
        self.assertEqual(report["created"], 1)
        assert_booking_integrity(self.booking)  # Should not raise
        
        # Verify failure was noted in report
        self.assertTrue(any("Notification failed" in note for note in report["notes"]))


class ManagementCommandTests(BookingIntegrityTestCase):
    """Tests for the management command (integration-style tests)."""
    
    @patch('hotel.services.booking_integrity.NotificationManager')
    def test_management_command_dry_run_behavior(self, mock_nm):
        """Test that dry-run mode doesn't make changes or send notifications."""
        from django.core.management import call_command
        from io import StringIO
        
        # Create issues
        self.booking.party.all().delete()
        
        # Run command in dry-run mode
        out = StringIO()
        call_command('heal_booking_integrity', '--hotel', self.hotel.slug, '--dry-run', stdout=out)
        
        # Verify issues still exist (no changes made)
        with self.assertRaises(AssertionError):
            assert_booking_integrity(self.booking)
        
        # Verify no notifications were sent
        mock_nm.return_value.realtime_booking_integrity_healed.assert_not_called()
        
        # Verify output mentions dry run
        output = out.getvalue()
        self.assertIn("DRY RUN", output)


# Additional test utilities for developers
class TestUtilities:
    """Utility functions for creating test scenarios with broken booking states."""
    
    @staticmethod
    def create_booking_with_no_primary_party(hotel):
        """Create a booking with missing PRIMARY BookingGuest."""
        booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=hotel.room_types.first(),
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            adults=1,
            primary_first_name="Test",
            primary_last_name="User",
            primary_email="test@example.com"
        )
        booking.party.all().delete()  # Remove automatically created PRIMARY
        return booking
    
    @staticmethod
    def create_booking_with_multiple_primaries(hotel):
        """Create a booking with multiple PRIMARY BookingGuests."""
        booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=hotel.room_types.first(),
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            adults=1,
            primary_first_name="Test",
            primary_last_name="User",
            primary_email="test@example.com"
        )
        
        # Create additional PRIMARY (first one auto-created)
        BookingGuest.objects.create(
            booking=booking,
            role='PRIMARY',
            first_name="Extra",
            last_name="Primary",
            is_staying=True
        )
        
        return booking
    
    @staticmethod
    def create_checkedin_booking_with_missing_guests(hotel, room):
        """Create a checked-in booking with missing in-house guests."""
        booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=hotel.room_types.first(),
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            adults=1,
            primary_first_name="Test",
            primary_last_name="User",
            primary_email="test@example.com",
            assigned_room=room,
            checked_in_at=timezone.now()
        )
        
        # Remove any auto-created guests
        booking.guests.all().delete()
        
        return booking