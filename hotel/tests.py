import pytz
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command
from django.io import StringIO

from hotel.models import Hotel, RoomBooking, OverstayIncident
from rooms.models import Room, RoomType
from room_bookings.services.overstay import detect_overstays, get_hotel_noon_utc


class OverstayDetectionTestCase(TestCase):
    """Tests for noon-based overstay detection system."""
    
    def setUp(self):
        """Set up test data."""
        # Create a hotel with Dublin timezone
        self.hotel = Hotel.objects.create(
            name="Test Hotel Dublin",
            slug="test-hotel-dublin",
            timezone="Europe/Dublin"  # Has DST transitions
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            capacity=2
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number="101",
            room_type=self.room_type,
            status='CLEAN'
        )
        
        # Test dates
        self.checkout_date = date(2025, 1, 15)  # Wednesday
        
    def _create_in_house_booking(self, check_out_date=None):
        """Helper to create an IN_HOUSE booking."""
        return RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            assigned_room=self.room,
            check_in=date(2025, 1, 10),
            check_out=check_out_date or self.checkout_date,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            adults=1,
            children=0,
            total_amount=Decimal('100.00'),
            currency='EUR',
            status='CONFIRMED',
            # IN_HOUSE status = checked_in_at set, checked_out_at null
            checked_in_at=timezone.now() - timedelta(days=3),
            checked_out_at=None  # Still checked in
        )
    
    def _create_completed_booking(self, check_out_date=None):
        """Helper to create a COMPLETED booking (checked out)."""
        booking = self._create_in_house_booking(check_out_date)
        booking.checked_out_at = timezone.now() - timedelta(hours=1)
        booking.status = 'COMPLETED'
        booking.save()
        return booking

    def test_detect_overstays_before_noon(self):
        """Test that no incident is created before noon on checkout date."""
        booking = self._create_in_house_booking()
        
        # Set time to 10:00 AM on checkout date (before noon)
        test_time = datetime.combine(self.checkout_date, time(10, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 0)
        self.assertEqual(OverstayIncident.objects.count(), 0)
    
    def test_detect_overstays_at_noon(self):
        """Test that incident is created exactly at noon on checkout date."""
        booking = self._create_in_house_booking()
        
        # Set time to exactly 12:00 PM (noon) on checkout date
        test_time = datetime.combine(self.checkout_date, time(12, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 1)
        
        incident = OverstayIncident.objects.get()
        self.assertEqual(incident.booking, booking)
        self.assertEqual(incident.hotel, self.hotel)
        self.assertEqual(incident.expected_checkout_date, self.checkout_date)
        self.assertEqual(incident.status, 'OPEN')
        self.assertEqual(incident.severity, 'MEDIUM')
    
    def test_detect_overstays_after_noon(self):
        """Test that incident is created after noon on checkout date."""
        booking = self._create_in_house_booking()
        
        # Set time to 2:00 PM on checkout date (after noon)
        test_time = datetime.combine(self.checkout_date, time(14, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 1)
        
        incident = OverstayIncident.objects.get()
        self.assertEqual(incident.booking, booking)
        self.assertEqual(incident.status, 'OPEN')
    
    def test_detect_overstays_ignores_completed_bookings(self):
        """Test that completed (checked out) bookings are ignored."""
        completed_booking = self._create_completed_booking()
        
        # Set time to after noon on checkout date
        test_time = datetime.combine(self.checkout_date, time(14, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 0)
        self.assertEqual(OverstayIncident.objects.count(), 0)
    
    def test_detect_overstays_idempotency(self):
        """Test that running detection twice doesn't create duplicates."""
        booking = self._create_in_house_booking()
        
        # Set time to after noon on checkout date
        test_time = datetime.combine(self.checkout_date, time(14, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        # Run detection first time
        incidents_created_1 = detect_overstays(self.hotel, test_time_utc)
        self.assertEqual(incidents_created_1, 1)
        
        # Run detection second time
        incidents_created_2 = detect_overstays(self.hotel, test_time_utc)
        self.assertEqual(incidents_created_2, 0)  # No new incidents
        
        # Should still have only one incident
        self.assertEqual(OverstayIncident.objects.count(), 1)
    
    def test_detect_overstays_acknowledged_incident(self):
        """Test that acknowledged incidents don't generate new ones."""
        booking = self._create_in_house_booking()
        
        # Create an acknowledged incident
        OverstayIncident.objects.create(
            hotel=self.hotel,
            booking=booking,
            expected_checkout_date=self.checkout_date,
            detected_at=timezone.now(),
            status='ACKED',  # Acknowledged
            severity='MEDIUM'
        )
        
        # Set time to after noon on checkout date
        test_time = datetime.combine(self.checkout_date, time(14, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 0)  # No new incidents
        self.assertEqual(OverstayIncident.objects.count(), 1)  # Still have the original
    
    def test_detect_overstays_multiple_bookings(self):
        """Test detection with multiple overstaying bookings."""
        booking1 = self._create_in_house_booking(date(2025, 1, 10))  # 5 days overdue
        booking2 = self._create_in_house_booking(date(2025, 1, 14))  # 1 day overdue
        booking3 = self._create_in_house_booking(date(2025, 1, 16))  # Future checkout
        
        # Set time to afternoon on Jan 15
        test_time = datetime.combine(date(2025, 1, 15), time(15, 0))
        test_time_utc = self.hotel.timezone_obj.localize(test_time).astimezone(pytz.UTC)
        
        incidents_created = detect_overstays(self.hotel, test_time_utc)
        
        self.assertEqual(incidents_created, 2)  # booking1 and booking2 only
        self.assertEqual(OverstayIncident.objects.count(), 2)
    
    def test_get_hotel_noon_utc_winter_time(self):
        """Test noon UTC calculation during winter time (no DST)."""
        # January 15, 2025 - Dublin is UTC+0 (no DST)
        winter_date = date(2025, 1, 15)
        
        noon_utc = get_hotel_noon_utc(self.hotel, winter_date)
        expected_utc = datetime(2025, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
        
        self.assertEqual(noon_utc, expected_utc)
    
    def test_get_hotel_noon_utc_summer_time(self):
        """Test noon UTC calculation during summer time (DST active)."""
        # July 15, 2025 - Dublin is UTC+1 (DST active)
        summer_date = date(2025, 7, 15)
        
        noon_utc = get_hotel_noon_utc(self.hotel, summer_date)
        expected_utc = datetime(2025, 7, 15, 11, 0, 0, tzinfo=pytz.UTC)  # 12:00 Dublin = 11:00 UTC
        
        self.assertEqual(noon_utc, expected_utc)


class OverstayManagementCommandTestCase(TestCase):
    """Tests for the flag_overstay_bookings management command."""
    
    def setUp(self):
        """Set up test data."""
        self.hotel1 = Hotel.objects.create(
            name="Hotel One",
            slug="hotel-one",
            timezone="Europe/Dublin"
        )
        
        self.hotel2 = Hotel.objects.create(
            name="Hotel Two", 
            slug="hotel-two",
            timezone="Europe/Dublin"
        )
        
        # Create room types and rooms
        for hotel in [self.hotel1, self.hotel2]:
            room_type = RoomType.objects.create(
                hotel=hotel,
                name="Standard Room",
                capacity=2
            )
            Room.objects.create(
                hotel=hotel,
                room_number="101",
                room_type=room_type,
                status='CLEAN'
            )
    
    def _create_overstaying_booking(self, hotel):
        """Create a booking that should trigger overstay incident."""
        room_type = RoomType.objects.filter(hotel=hotel).first()
        room = Room.objects.filter(hotel=hotel).first()
        
        return RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            assigned_room=room,
            check_in=date(2025, 1, 10),
            check_out=date(2025, 1, 14),  # Yesterday
            primary_first_name="Test",
            primary_last_name="Guest",
            primary_email="test@example.com", 
            adults=1,
            children=0,
            total_amount=Decimal('100.00'),
            currency='EUR',
            status='CONFIRMED',
            checked_in_at=timezone.now() - timedelta(days=3),
            checked_out_at=None  # Still IN_HOUSE
        )
    
    @patch('room_bookings.services.overstay.detect_overstays')
    def test_management_command_calls_detect_overstays(self, mock_detect):
        """Test that management command calls detect_overstays for each hotel."""
        mock_detect.return_value = 1  # Mock 1 incident created per hotel
        
        out = StringIO()
        call_command('flag_overstay_bookings', stdout=out)
        
        # Should have called detect_overstays for both hotels
        self.assertEqual(mock_detect.call_count, 2)
        
        # Check output
        output = out.getvalue()
        self.assertIn("Hotels processed: 2", output)
        self.assertIn("Incidents created: 2", output)
    
    @patch('room_bookings.services.overstay.detect_overstays')
    def test_management_command_dry_run(self, mock_detect):
        """Test management command in dry run mode."""
        out = StringIO()
        call_command('flag_overstay_bookings', '--dry-run', stdout=out)
        
        # detect_overstays should not be called in dry run mode
        mock_detect.assert_not_called()
        
        output = out.getvalue()
        self.assertIn("DRY RUN MODE", output)
    
    @patch('room_bookings.services.overstay.detect_overstays')
    def test_management_command_handles_errors(self, mock_detect):
        """Test that management command handles errors gracefully."""
        def side_effect(hotel, now_utc):
            if hotel.slug == 'hotel-one':
                raise Exception("Test error")
            return 0
        
        mock_detect.side_effect = side_effect
        
        out = StringIO()
        call_command('flag_overstay_bookings', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Error processing hotel hotel-one", output)
        self.assertIn("Errors: 1", output)
