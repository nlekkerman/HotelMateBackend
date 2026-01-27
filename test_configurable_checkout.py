"""
Comprehensive tests for configurable checkout time implementation.

Tests cover:
1. compute_checkout_deadline_at timezone correctness  
2. Changing standard_checkout_time changes checkout_deadline_at
3. Overstay detection triggers relative to configured time (not noon)
4. PATCH endpoint persists and returns updated config
5. Realtime events on config updates
6. Grace period semantics (deadline is TRUE cutoff, grace affects risk levels only)
"""
import pytest
from datetime import datetime, date, time, timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import pytz

from hotel.models import Hotel, HotelAccessConfig, Staff, RoomBooking, OverstayIncident
from room_bookings.services.overstay import compute_checkout_deadline_at, detect_overstays
from guests.models import Guest
from rooms.models import Room, RoomType


class ConfigurableCheckoutTestCase(TestCase):
    """Test configurable checkout time functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create hotel with Dublin timezone
        self.hotel = Hotel.objects.create(
            name="Test Hotel Dublin",
            slug="test-hotel-dublin", 
            timezone="Europe/Dublin"
        )
        
        # Create hotel access config with non-noon checkout time
        self.access_config = HotelAccessConfig.objects.create(
            hotel=self.hotel,
            standard_checkout_time=time(10, 30),  # 10:30 AM instead of noon
            late_checkout_grace_minutes=45,  # 45 minute grace
            approval_sla_minutes=30,
            approval_cutoff_time=time(22, 0),
            approval_cutoff_day_offset=0
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='teststaff',
            email='staff@test.com',
            password='testpass123'
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            hotel=self.hotel,
            first_name='Test',
            last_name='Staff',
            is_active=True
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            number="101",
            status="AVAILABLE"
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890"
        )

    def test_compute_checkout_deadline_at_timezone_correctness(self):
        """Test that compute_checkout_deadline_at handles timezones correctly"""
        # Create booking with checkout tomorrow
        checkout_date = date.today() + timedelta(days=1)
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-001",
            check_in=date.today(),
            check_out=checkout_date,
            status="CONFIRMED",
            booker_first_name="John",
            booker_last_name="Doe",
            booker_email="john@example.com",
            total_amount=100.00
        )
        
        # Compute deadline
        deadline_utc = compute_checkout_deadline_at(booking)
        
        # Verify deadline is correct UTC time
        dublin_tz = pytz.timezone('Europe/Dublin')
        expected_local = datetime.combine(checkout_date, time(10, 30))
        expected_local_aware = dublin_tz.localize(expected_local)
        expected_utc = expected_local_aware.astimezone(pytz.UTC)
        
        self.assertEqual(deadline_utc, expected_utc)
        self.assertTrue(deadline_utc.tzinfo is pytz.UTC)

    def test_changing_checkout_time_changes_deadline(self):
        """Test that updating standard_checkout_time affects computed deadline"""
        checkout_date = date.today() + timedelta(days=1)
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-002",
            check_in=date.today(),
            check_out=checkout_date,
            status="CONFIRMED",
            booker_first_name="Jane",
            booker_last_name="Smith",
            booker_email="jane@example.com",
            total_amount=150.00
        )
        
        # Get initial deadline (10:30 AM)
        initial_deadline = compute_checkout_deadline_at(booking)
        
        # Update checkout time to 2:00 PM
        self.access_config.standard_checkout_time = time(14, 0)
        self.access_config.save()
        
        # Get new deadline
        new_deadline = compute_checkout_deadline_at(booking)
        
        # Should be 3.5 hours later (10:30 AM -> 2:00 PM)
        expected_diff = timedelta(hours=3, minutes=30)
        actual_diff = new_deadline - initial_deadline
        
        self.assertEqual(actual_diff, expected_diff)

    def test_overstay_detection_uses_configured_time(self):
        """Test overstay detection uses configured checkout time, not noon"""
        checkout_date = date.today()  # Today's date
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-003",
            check_in=date.today() - timedelta(days=1),
            check_out=checkout_date,
            status="IN_HOUSE",
            booker_first_name="Bob",
            booker_last_name="Wilson",
            booker_email="bob@example.com",
            total_amount=200.00,
            checked_in_at=timezone.now() - timedelta(days=1),
            assigned_room=self.room
        )
        
        dublin_tz = pytz.timezone('Europe/Dublin')
        
        # Test time just before configured checkout (10:15 AM Dublin time) 
        before_checkout_local = datetime.combine(checkout_date, time(10, 15))
        before_checkout_utc = dublin_tz.localize(before_checkout_local).astimezone(pytz.UTC)
        
        # Should NOT be overstay yet
        incidents_before = detect_overstays(self.hotel, before_checkout_utc)
        self.assertEqual(incidents_before, 0)
        
        # Test time after configured checkout (10:45 AM Dublin time)
        after_checkout_local = datetime.combine(checkout_date, time(10, 45))  
        after_checkout_utc = dublin_tz.localize(after_checkout_local).astimezone(pytz.UTC)
        
        # Should detect overstay 
        incidents_after = detect_overstays(self.hotel, after_checkout_utc)
        self.assertEqual(incidents_after, 1)
        
        # Verify incident was created
        incident = OverstayIncident.objects.filter(booking=booking).first()
        self.assertIsNotNone(incident)
        self.assertEqual(incident.status, 'OPEN')
        
        # Important: This test ensures noon logic is gone
        # If this test passes but a test at 11:30 AM also triggers overstay,
        # then noon logic is still present somewhere
        
        # Test at 11:30 AM (old noon-based logic would not trigger yet)
        before_noon_local = datetime.combine(checkout_date, time(11, 30))
        before_noon_utc = dublin_tz.localize(before_noon_local).astimezone(pytz.UTC)
        
        # Create another booking to test
        booking2 = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-003B",
            check_in=date.today() - timedelta(days=1),
            check_out=checkout_date,
            status="IN_HOUSE",
            booker_first_name="Alice",
            booker_last_name="Brown",
            booker_email="alice@example.com",
            total_amount=200.00,
            checked_in_at=timezone.now() - timedelta(days=1),
            assigned_room=self.room  # Reusing room for simplicity
        )
        
        # Should still detect overstay at 11:30 AM since checkout was 10:30 AM
        incidents_before_noon = detect_overstays(self.hotel, before_noon_utc)
        self.assertEqual(incidents_before_noon, 1)

    def test_access_config_patch_endpoint(self):
        """Test PATCH endpoint persists and returns updated config"""
        self.client.force_login(self.staff_user)
        
        # PATCH new checkout time
        patch_data = {
            'standard_checkout_time': '11:45:00',
            'late_checkout_grace_minutes': 60
        }
        
        response = self.client.patch(
            f'/api/staff/hotel/{self.hotel.slug}/access-config/',
            data=patch_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify response data
        response_data = response.json()
        self.assertEqual(response_data['standard_checkout_time'], '11:45:00')
        self.assertEqual(response_data['late_checkout_grace_minutes'], 60)
        
        # Verify database was updated
        self.access_config.refresh_from_db()
        self.assertEqual(self.access_config.standard_checkout_time, time(11, 45))
        self.assertEqual(self.access_config.late_checkout_grace_minutes, 60)

    @patch('hotel.staff_views.pusher_client')
    def test_realtime_event_on_config_update(self, mock_pusher):
        """Test that config updates emit realtime events"""
        self.client.force_login(self.staff_user)
        
        # PATCH config
        patch_data = {
            'standard_checkout_time': '12:00:00',
            'late_checkout_grace_minutes': 30
        }
        
        response = self.client.patch(
            f'/api/staff/hotel/{self.hotel.slug}/access-config/',
            data=patch_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify pusher was called
        mock_pusher.trigger.assert_called_once()
        args, kwargs = mock_pusher.trigger.call_args
        
        channel, event, data = args
        self.assertEqual(channel, f'{self.hotel.slug}.staff-menu-management')
        self.assertEqual(event, 'access-config-updated')
        self.assertEqual(data['category'], 'hotel_config')
        self.assertEqual(data['event_type'], 'access_config_updated')
        self.assertEqual(data['hotel_slug'], self.hotel.slug)
        self.assertEqual(data['payload']['standard_checkout_time'], '12:00:00')

    def test_deadline_without_grace_period(self):
        """Test that checkout_deadline_at is the TRUE cutoff (no grace included)"""
        checkout_date = date.today()
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-004",
            check_in=date.today() - timedelta(days=1),
            check_out=checkout_date,
            status="CONFIRMED",
            booker_first_name="Grace",
            booker_last_name="Test",
            booker_email="grace@example.com",
            total_amount=100.00
        )
        
        # Compute deadline - should be exactly 10:30 AM, NO grace applied
        deadline_utc = compute_checkout_deadline_at(booking)
        
        dublin_tz = pytz.timezone('Europe/Dublin')
        expected_local = datetime.combine(checkout_date, time(10, 30))  # Exact checkout time
        expected_local_aware = dublin_tz.localize(expected_local)
        expected_utc = expected_local_aware.astimezone(pytz.UTC)
        
        self.assertEqual(deadline_utc, expected_utc)
        
        # Verify grace period is NOT included in deadline
        # (Grace period of 45 minutes should not affect the deadline itself)
        grace_deadline = deadline_utc + timedelta(minutes=45)
        self.assertNotEqual(deadline_utc, grace_deadline)

    def test_validation_constraints(self):
        """Test serializer validation for checkout time config"""
        self.client.force_login(self.staff_user)
        
        # Test negative grace minutes (should fail)
        invalid_data = {
            'late_checkout_grace_minutes': -10
        }
        response = self.client.patch(
            f'/api/staff/hotel/{self.hotel.slug}/access-config/',
            data=invalid_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test excessive grace minutes (should fail) 
        invalid_data = {
            'late_checkout_grace_minutes': 1000  # > 720 minutes (12 hours)
        }
        response = self.client.patch(
            f'/api/staff/hotel/{self.hotel.slug}/access-config/',
            data=invalid_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test valid grace minutes (should succeed)
        valid_data = {
            'late_checkout_grace_minutes': 90  # 1.5 hours
        }
        response = self.client.patch(
            f'/api/staff/hotel/{self.hotel.slug}/access-config/',
            data=valid_data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_dst_transition_handling(self):
        """Test checkout deadline calculation during DST transitions"""
        # Create booking for DST transition date (last Sunday in March 2024)
        # In Dublin, clocks go forward 1 hour at 1:00 AM -> 2:00 AM
        dst_date = date(2024, 3, 31)  # DST transition day in Europe/Dublin
        
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="TEST-DST",
            check_in=dst_date - timedelta(days=1),
            check_out=dst_date,
            status="CONFIRMED",
            booker_first_name="DST",
            booker_last_name="Test",
            booker_email="dst@example.com",
            total_amount=100.00
        )
        
        # Should handle DST transition correctly
        deadline_utc = compute_checkout_deadline_at(booking)
        
        # Verify deadline is timezone-aware and correct
        self.assertTrue(deadline_utc.tzinfo is pytz.UTC)
        
        # Convert back to Dublin time to verify
        dublin_tz = pytz.timezone('Europe/Dublin')
        deadline_dublin = deadline_utc.astimezone(dublin_tz)
        
        self.assertEqual(deadline_dublin.time(), time(10, 30))
        self.assertEqual(deadline_dublin.date(), dst_date)

    def test_no_config_fallback(self):
        """Test fallback to default 11:00 AM when no access config exists"""
        # Create hotel without access config
        hotel_no_config = Hotel.objects.create(
            name="No Config Hotel",
            slug="no-config-hotel",
            timezone="Europe/Dublin"
        )
        
        checkout_date = date.today()
        booking = RoomBooking.objects.create(
            hotel=hotel_no_config,
            booking_id="TEST-FALLBACK",
            check_in=date.today() - timedelta(days=1),
            check_out=checkout_date,
            status="CONFIRMED",
            booker_first_name="Fallback",
            booker_last_name="Test",
            booker_email="fallback@example.com",
            total_amount=100.00
        )
        
        # Should use default 11:00 AM
        deadline_utc = compute_checkout_deadline_at(booking)
        
        dublin_tz = pytz.timezone('Europe/Dublin')
        expected_local = datetime.combine(checkout_date, time(11, 0))  # Default time
        expected_local_aware = dublin_tz.localize(expected_local)
        expected_utc = expected_local_aware.astimezone(pytz.UTC)
        
        self.assertEqual(deadline_utc, expected_utc)


if __name__ == '__main__':
    pytest.main([__file__])