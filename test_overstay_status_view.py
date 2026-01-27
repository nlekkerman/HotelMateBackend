#!/usr/bin/env python
"""
Tests for OverstayStatusView to prevent regression of incident ordering bug.

Tests ensure the API always returns the latest ACTIVE (OPEN/ACKED) incident,
not arbitrary incidents due to unordered queries.
"""
import os
import sys
import django
from datetime import datetime, date, time, timedelta
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone

from hotel.models import Hotel, HotelAccessConfig, RoomBooking, OverstayIncident
from hotel.overstay_views import OverstayStatusView
from rooms.models import Room, RoomType
from guests.models import Guest


class OverstayStatusViewTestCase(TestCase):
    """Tests for OverstayStatusView incident ordering and selection."""
    
    def setUp(self):
        """Set up test data."""
        # Create test hotel with timezone
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            timezone='Europe/Dublin',
            city='Dublin',
            country='Ireland'
        )
        
        # Create hotel access config with 11:00 AM checkout
        self.access_config = HotelAccessConfig.objects.create(
            hotel=self.hotel,
            standard_checkout_time=time(11, 0),
            late_checkout_grace_minutes=30
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name='Standard',
            max_occupancy=2,
            base_price=100.00
        )
        
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number='101',
            room_type=self.room_type,
            max_occupancy=2
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        
        # Setup request factory
        self.factory = RequestFactory()
        self.view = OverstayStatusView()
        
    def _create_overdue_booking(self, checkout_date=None):
        """Create an IN_HOUSE booking that's overdue."""
        if checkout_date is None:
            checkout_date = timezone.now().date()  # Today (overdue)
            
        booking = RoomBooking.objects.create(
            hotel=self.hotel,
            guest=self.guest,
            room_type=self.room_type,
            assigned_room=self.room,
            check_in=checkout_date,
            check_out=checkout_date,
            status='IN_HOUSE',
            checked_in_at=timezone.now() - timedelta(hours=2),
            primary_first_name='John',
            primary_last_name='Doe',
            booking_id=f'TEST-{checkout_date.strftime("%Y%m%d")}-001',
            booker_first_name='John',
            booker_last_name='Doe',
            booker_email='john@example.com',
            total_amount=100.00
        )
        return booking
        
    def _create_incident(self, booking, status='OPEN', detected_at=None, expected_checkout_date=None):
        """Create an OverstayIncident."""
        if detected_at is None:
            detected_at = timezone.now()
        if expected_checkout_date is None:
            expected_checkout_date = booking.check_out
            
        return OverstayIncident.objects.create(
            hotel=self.hotel,
            booking=booking,
            expected_checkout_date=expected_checkout_date,
            detected_at=detected_at,
            status=status,
            severity='MEDIUM',
            meta={'test': True}
        )
        
    def _make_request(self, booking_id):
        """Make API request to OverstayStatusView."""
        request = self.factory.get('/')
        request.user = self.user
        response = self.view.get(request, self.hotel.slug, booking_id)
        return response
    
    def test_returns_latest_active_incident_when_multiple_exist(self):
        """Test that API returns the latest ACTIVE incident when multiple exist."""
        booking = self._create_overdue_booking()
        
        # Create incidents in this order:
        # 1. RESOLVED (older) - should be ignored
        # 2. OPEN (newer) - should be returned
        
        older_time = timezone.now() - timedelta(hours=2)
        newer_time = timezone.now() - timedelta(hours=1)
        
        resolved_incident = self._create_incident(
            booking, 
            status='RESOLVED', 
            detected_at=older_time
        )
        
        open_incident = self._create_incident(
            booking, 
            status='OPEN', 
            detected_at=newer_time
        )
        
        # Make API request
        response = self._make_request(booking.booking_id)
        
        # Should return OPEN incident, not RESOLVED
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertTrue(data['is_overstay'])
        self.assertEqual(data['incident_state'], 'ACTIVE')
        self.assertIn('overstay', data)
        self.assertEqual(data['overstay']['status'], 'OPEN')
        self.assertEqual(
            data['overstay']['detected_at'], 
            open_incident.detected_at.isoformat()
        )
    
    def test_returns_latest_when_multiple_active_incidents(self):
        """Test ordering works when multiple OPEN/ACKED incidents exist."""
        booking = self._create_overdue_booking()
        
        # Create two OPEN incidents (edge case - shouldn't normally happen)
        older_open = self._create_incident(
            booking, 
            status='OPEN', 
            detected_at=timezone.now() - timedelta(hours=2)
        )
        
        newer_open = self._create_incident(
            booking, 
            status='OPEN', 
            detected_at=timezone.now() - timedelta(hours=1)
        )
        
        # Should return the newer one
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertEqual(data['overstay']['status'], 'OPEN')
        self.assertEqual(
            data['overstay']['detected_at'],
            newer_open.detected_at.isoformat()
        )
    
    def test_returns_acked_incident_when_latest_active(self):
        """Test that ACKED incidents are returned as active."""
        booking = self._create_overdue_booking()
        
        acked_incident = self._create_incident(booking, status='ACKED')
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertEqual(data['incident_state'], 'ACTIVE')
        self.assertEqual(data['overstay']['status'], 'ACKED')
    
    def test_missing_incident_state_when_no_active_incident(self):
        """Test incident_state is MISSING when no active incident exists."""
        booking = self._create_overdue_booking()
        
        # Create only resolved incident
        self._create_incident(booking, status='RESOLVED')
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertTrue(data['is_overstay'])  # Still overdue by time
        self.assertEqual(data['incident_state'], 'MISSING')  # No active incident
        self.assertNotIn('overstay', data)  # No overstay details
    
    def test_missing_incident_state_when_no_incidents_exist(self):
        """Test incident_state is MISSING when no incidents exist at all."""
        booking = self._create_overdue_booking()
        
        # No incidents created
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertTrue(data['is_overstay'])  # Still overdue by time
        self.assertEqual(data['incident_state'], 'MISSING')  # No incidents
        self.assertNotIn('overstay', data)  # No overstay details
    
    def test_computes_hours_overdue_correctly(self):
        """Test that hours_overdue is computed from checkout deadline."""
        booking = self._create_overdue_booking()
        
        # Create incident
        incident = self._create_incident(booking)
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        # Should have positive hours_overdue since booking is overdue
        self.assertIn('overstay', data)
        self.assertGreater(data['overstay']['hours_overdue'], 0)
        self.assertIsInstance(data['overstay']['hours_overdue'], float)
    
    def test_not_overstay_when_not_in_house(self):
        """Test that completed bookings are not considered overstays."""
        booking = self._create_overdue_booking()
        booking.status = 'COMPLETED'
        booking.checked_out_at = timezone.now()
        booking.save()
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertFalse(data['is_overstay'])
        self.assertEqual(data['incident_state'], 'MISSING')
    
    def test_not_overstay_when_no_room_assigned(self):
        """Test that bookings without assigned rooms are not overstays."""
        booking = self._create_overdue_booking()
        booking.assigned_room = None
        booking.save()
        
        response = self._make_request(booking.booking_id)
        
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        self.assertFalse(data['is_overstay'])
        

def run_tests():
    """Run the tests."""
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(OverstayStatusViewTestCase)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    if run_tests():
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)