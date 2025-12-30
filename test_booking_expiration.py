"""
Tests for unpaid booking expiration functionality.

Tests cover:
1. Management command expiring PENDING_PAYMENT bookings
2. Availability logic excluding expired PENDING_PAYMENT bookings
3. Staff booking lists excluding non-operational bookings
"""

from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta, date
from unittest.mock import patch
from io import StringIO

from hotel.models import Hotel, RoomBooking
from rooms.models import RoomType
from hotel.services.availability import _booked_for_date


class BookingExpirationTestCase(TestCase):
    """Base test case with common setup for booking expiration tests."""
    
    def setUp(self):
        # Create test hotel and room type
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            city="Test City",
            country="Test Country"
        )
        
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            code="STD",
            base_price=100.00,
            max_occupancy=2
        )
        
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)


class ExpireUnpaidBookingsCommandTest(BookingExpirationTestCase):
    """Test the expire_unpaid_bookings management command."""
    
    def test_command_expires_expired_pending_payment_bookings(self):
        """Test that expired PENDING_PAYMENT bookings are set to CANCELLED_DRAFT."""
        now = timezone.now()
        past_time = now - timedelta(minutes=30)
        
        # Create expired booking
        expired_booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT',
            expires_at=past_time
        )
        
        # Create non-expired booking
        future_time = now + timedelta(minutes=30)
        active_booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Jane",
            primary_last_name="Smith",
            primary_email="jane@example.com",
            primary_phone="+1234567891",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT',
            expires_at=future_time
        )
        
        # Run the command
        out = StringIO()
        call_command('expire_unpaid_bookings', stdout=out)
        
        # Refresh from database
        expired_booking.refresh_from_db()
        active_booking.refresh_from_db()
        
        # Check results
        self.assertEqual(expired_booking.status, 'CANCELLED_DRAFT')
        self.assertIsNotNone(expired_booking.cancelled_at)
        self.assertEqual(active_booking.status, 'PENDING_PAYMENT')
        self.assertIsNone(active_booking.cancelled_at)
        
        # Check command output
        output = out.getvalue()
        self.assertIn('Expired 1 bookings', output)
    
    def test_command_ignores_confirmed_bookings(self):
        """Test that CONFIRMED bookings are not expired even if expires_at is past."""
        now = timezone.now()
        past_time = now - timedelta(minutes=30)
        
        # Create confirmed booking with past expires_at (edge case)
        confirmed_booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='CONFIRMED',
            expires_at=past_time,
            paid_at=now
        )
        
        # Run the command
        out = StringIO()
        call_command('expire_unpaid_bookings', stdout=out)
        
        # Refresh from database
        confirmed_booking.refresh_from_db()
        
        # Check that it wasn't changed
        self.assertEqual(confirmed_booking.status, 'CONFIRMED')
        self.assertIsNone(confirmed_booking.cancelled_at)
        
        # Check command output
        output = out.getvalue()
        self.assertIn('No expired bookings found', output)
    
    def test_command_dry_run_mode(self):
        """Test that dry run mode shows what would be expired without making changes."""
        now = timezone.now()
        past_time = now - timedelta(minutes=30)
        
        # Create expired booking
        expired_booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT',
            expires_at=past_time
        )
        
        # Run the command in dry run mode
        out = StringIO()
        call_command('expire_unpaid_bookings', '--dry-run', stdout=out)
        
        # Refresh from database
        expired_booking.refresh_from_db()
        
        # Check that nothing was changed
        self.assertEqual(expired_booking.status, 'PENDING_PAYMENT')
        self.assertIsNone(expired_booking.cancelled_at)
        
        # Check command output
        output = out.getvalue()
        self.assertIn('DRY RUN MODE', output)
        self.assertIn('Would expire 1 bookings', output)


class AvailabilityExcludeExpiredTest(BookingExpirationTestCase):
    """Test that availability logic excludes expired PENDING_PAYMENT bookings."""
    
    def test_booked_for_date_excludes_expired_pending_payment(self):
        """Test that _booked_for_date excludes expired PENDING_PAYMENT bookings."""
        now = timezone.now()
        past_time = now - timedelta(minutes=30)
        future_time = now + timedelta(minutes=30)
        
        # Create expired PENDING_PAYMENT booking (should not block availability)
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com",
            primary_phone="+1234567890",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT',
            expires_at=past_time
        )
        
        # Create non-expired PENDING_PAYMENT booking (should block availability)
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Jane",
            primary_last_name="Smith",
            primary_email="jane@example.com",
            primary_phone="+1234567891",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT',
            expires_at=future_time
        )
        
        # Create CONFIRMED booking (always blocks availability)
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Bob",
            primary_last_name="Wilson",
            primary_email="bob@example.com",
            primary_phone="+1234567892",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='CONFIRMED',
            expires_at=past_time,  # Even if expired, CONFIRMED always blocks
            paid_at=now
        )
        
        # Check availability - should count 2 bookings (1 non-expired PENDING_PAYMENT + 1 CONFIRMED)
        booked_count = _booked_for_date(self.room_type, self.today)
        self.assertEqual(booked_count, 2)
    
    def test_booked_for_date_includes_pending_payment_without_expires_at(self):
        """Test that PENDING_PAYMENT bookings without expires_at are included (legacy behavior)."""
        # Create PENDING_PAYMENT booking without expires_at
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Legacy",
            primary_last_name="User",
            primary_email="legacy@example.com",
            primary_phone="+1234567893",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT'
            # expires_at is None
        )
        
        # Should still block availability (legacy bookings assumed valid)
        booked_count = _booked_for_date(self.room_type, self.today)
        self.assertEqual(booked_count, 1)


class StaffBookingVisibilityTest(BookingExpirationTestCase):
    """Test that staff booking lists exclude non-operational bookings."""
    
    def test_staff_booking_list_excludes_non_operational_statuses(self):
        """Test the queryset exclusion logic used in staff views."""
        now = timezone.now()
        
        # Create bookings with different statuses
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Draft",
            primary_last_name="User",
            primary_email="draft@example.com",
            primary_phone="+1234567890",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='DRAFT'  # Should be excluded
        )
        
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Pending",
            primary_last_name="User",
            primary_email="pending@example.com",
            primary_phone="+1234567891",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='PENDING_PAYMENT'  # Should be excluded
        )
        
        RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Cancelled",
            primary_last_name="Draft",
            primary_email="cancelled@example.com",
            primary_phone="+1234567892",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='CANCELLED_DRAFT'  # Should be excluded
        )
        
        confirmed_booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=self.today,
            check_out=self.tomorrow,
            primary_first_name="Confirmed",
            primary_last_name="User",
            primary_email="confirmed@example.com",
            primary_phone="+1234567893",
            booker_type="SELF",
            adults=1,
            children=0,
            total_amount=100.00,
            status='CONFIRMED',  # Should be included
            paid_at=now
        )
        
        # Test the queryset used in staff views
        staff_visible_bookings = RoomBooking.objects.filter(
            hotel=self.hotel
        ).exclude(
            status__in=['DRAFT', 'PENDING_PAYMENT', 'CANCELLED_DRAFT']
        )
        
        # Should only see the confirmed booking
        self.assertEqual(staff_visible_bookings.count(), 1)
        self.assertEqual(staff_visible_bookings.first().id, confirmed_booking.id)
        
        # Verify all bookings exist in database
        all_bookings = RoomBooking.objects.filter(hotel=self.hotel)
        self.assertEqual(all_bookings.count(), 4)