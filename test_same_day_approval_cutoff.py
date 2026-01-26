"""
Tests for 22:00 approval cutoff rule.

Verifies that all bookings (same-day and future) can be approved until 
22:00 on check-in day, with SLA deadline used only for warnings.
"""
import pytz
from datetime import datetime, timedelta, time
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from hotel.models import Hotel, RoomBooking, HotelAccessConfig
from staff.models import Staff
from apps.booking.services.booking_deadlines import compute_approval_deadline, compute_approval_cutoff
from hotel.management.commands.auto_expire_overdue_bookings import Command as ExpireCommand


class ApprovalCutoffRuleTest(TestCase):
    """Test 22:00 approval cutoff rule for all bookings."""
    
    def setUp(self):
        """Set up test data."""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            city="Dublin",
            country="Ireland",
            timezone="Europe/Dublin"
        )
        
        # Create hotel access config with default SLA
        HotelAccessConfig.objects.create(
            hotel=self.hotel,
            approval_sla_minutes=30  # 30 min SLA for warnings only
        )
        
        self.user = User.objects.create_user(
            username="teststaff",
            email="test@example.com",
            password="testpass123"
        )
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            first_name="Test",
            last_name="Staff",
            role="reception"
        )

    def _create_booking(self, check_in_date, paid_at_time, **kwargs):
        """Helper to create booking with specific check-in date and payment time."""
        defaults = {
            'hotel': self.hotel,
            'booking_id': f'BK-{timezone.now().timestamp():.0f}',
            'status': 'PENDING_APPROVAL',
            'check_in': check_in_date,
            'check_out': check_in_date + timedelta(days=1),
            'adults': 2,
            'children': 0,
            'total_amount': 100.00,
            'currency': 'EUR',
            'primary_first_name': 'John',
            'primary_last_name': 'Doe',
            'primary_email': 'john@example.com',
            'payment_provider': 'stripe',
            'paid_at': paid_at_time,
        }
        defaults.update(kwargs)
        return RoomBooking.objects.create(**defaults)

    def test_approval_cutoff_is_22_00_on_checkin_day(self):
        """Test that approval cutoff is always 22:00 on check-in day."""
        # Test various check-in dates
        test_dates = [
            timezone.now().date(),  # Today
            timezone.now().date() + timedelta(days=1),  # Tomorrow
            timezone.now().date() + timedelta(days=7),  # Next week
        ]
        
        for check_in_date in test_dates:
            paid_time = timezone.now() - timedelta(minutes=5)
            booking = self._create_booking(check_in_date, paid_time)
            
            cutoff = compute_approval_cutoff(booking)
            
            # Convert to Dublin timezone to verify it's 22:00 on check-in day
            dublin_tz = pytz.timezone('Europe/Dublin')
            cutoff_local = cutoff.astimezone(dublin_tz)
            
            self.assertEqual(cutoff_local.date(), check_in_date)
            self.assertEqual(cutoff_local.time(), time(22, 0))

    def test_sla_deadline_vs_cutoff_separation(self):
        """Test that SLA deadline and cutoff are properly separated."""
        # Create booking made early in the day
        today = timezone.now().date()
        paid_time = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)  # 10:00 AM
        
        booking = self._create_booking(today, paid_time)
        
        # SLA deadline should be 30min after payment (10:30 AM)
        deadline = compute_approval_deadline(booking)
        expected_deadline = paid_time + timedelta(minutes=30)
        self.assertEqual(deadline, expected_deadline)
        
        # Cutoff should be 22:00 on check-in day
        cutoff = compute_approval_cutoff(booking)
        dublin_tz = pytz.timezone('Europe/Dublin')
        cutoff_local = cutoff.astimezone(dublin_tz)
        
        self.assertEqual(cutoff_local.date(), today)
        self.assertEqual(cutoff_local.time(), time(22, 0))
        
        # Cutoff should be much later than deadline
        self.assertGreater(cutoff, deadline)

    def test_booking_not_expired_after_sla_before_cutoff(self):
        """Test booking is NOT expired when past SLA deadline but before 22:00 cutoff."""
        # Create booking that paid hours ago (way past 30min SLA)
        today = timezone.now().date()
        paid_time = timezone.now() - timedelta(hours=6)  # 6 hours ago
        
        booking = self._create_booking(today, paid_time)
        
        # Verify SLA deadline has passed but cutoff hasn't
        deadline = compute_approval_deadline(booking)
        cutoff = compute_approval_cutoff(booking)
        now = timezone.now()
        
        self.assertLess(deadline, now)  # SLA deadline passed
        self.assertGreater(cutoff, now)  # 22:00 cutoff still in future
        
        # Run expire command - should not expire this booking
        command = ExpireCommand()
        options = {'dry_run': False, 'max_bookings': 200}
        command.handle(**options)
        
        # Booking should still be PENDING_APPROVAL (not expired)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'PENDING_APPROVAL')
        self.assertIsNone(booking.expired_at)

    def test_booking_expires_after_22_00_cutoff(self):
        """Test booking expires after 22:00 on check-in day."""
        # Create booking for yesterday (past 22:00 cutoff)
        yesterday = timezone.now().date() - timedelta(days=1)
        paid_time = timezone.now() - timedelta(days=1, hours=12)  # Yesterday noon
        
        booking = self._create_booking(
            yesterday, 
            paid_time,
            payment_intent_id='pi_test_12345'
        )
        
        # Verify cutoff has passed
        cutoff = compute_approval_cutoff(booking)
        now = timezone.now()
        self.assertLess(cutoff, now)
        
        # Run expire command - should expire this booking
        command = ExpireCommand()
        options = {'dry_run': False, 'max_bookings': 200}
        command.handle(**options)
        
        # Booking should be expired
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'EXPIRED')
        self.assertIsNotNone(booking.expired_at)
        self.assertEqual(booking.auto_expire_reason_code, 'APPROVAL_TIMEOUT')

    def test_future_and_same_day_bookings_same_rule(self):
        """Test that future and same-day bookings follow identical cutoff rules."""
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        # Same-day booking made hours ago
        same_day_booking = self._create_booking(
            today, 
            timezone.now() - timedelta(hours=8)  # 8 hours ago, way past SLA
        )
        
        # Future booking made hours ago
        future_booking = self._create_booking(
            next_week,
            timezone.now() - timedelta(hours=8)  # 8 hours ago, way past SLA
        )
        
        # Both should have cutoff at 22:00 on their respective check-in days
        same_day_cutoff = compute_approval_cutoff(same_day_booking)
        future_cutoff = compute_approval_cutoff(future_booking)
        
        dublin_tz = pytz.timezone('Europe/Dublin')
        
        same_day_cutoff_local = same_day_cutoff.astimezone(dublin_tz)
        future_cutoff_local = future_cutoff.astimezone(dublin_tz)
        
        # Both should be 22:00 on their check-in day
        self.assertEqual(same_day_cutoff_local.date(), today)
        self.assertEqual(same_day_cutoff_local.time(), time(22, 0))
        
        self.assertEqual(future_cutoff_local.date(), next_week)
        self.assertEqual(future_cutoff_local.time(), time(22, 0))
        
        # If it's before 22:00 today, neither should expire
        now = timezone.now()
        if now < same_day_cutoff:
            command = ExpireCommand()
            options = {'dry_run': False, 'max_bookings': 200}
            command.handle(**options)
            
            same_day_booking.refresh_from_db()
            future_booking.refresh_from_db()
            
            # Neither should be expired
            self.assertEqual(same_day_booking.status, 'PENDING_APPROVAL')
            self.assertEqual(future_booking.status, 'PENDING_APPROVAL')

    def test_timezone_handling_for_different_hotels(self):
        """Test that timezone conversion works correctly for different hotel timezones."""
        # Create hotel in different timezone
        tokyo_hotel = Hotel.objects.create(
            name="Tokyo Hotel",
            slug="tokyo-hotel", 
            city="Tokyo",
            country="Japan",
            timezone="Asia/Tokyo"
        )
        
        HotelAccessConfig.objects.create(
            hotel=tokyo_hotel,
            approval_sla_minutes=30
        )
        
        # Create booking for check-in today in Tokyo timezone
        tokyo_tz = pytz.timezone('Asia/Tokyo')
        now_tokyo = timezone.now().astimezone(tokyo_tz)
        today_tokyo = now_tokyo.date()
        
        booking = RoomBooking.objects.create(
            hotel=tokyo_hotel,
            booking_id='BK-TOKYO-TEST',
            status='PENDING_APPROVAL',
            check_in=today_tokyo,
            check_out=today_tokyo + timedelta(days=1),
            adults=2,
            children=0,
            total_amount=10000.00,
            currency='JPY',
            primary_first_name='Taro',
            primary_last_name='Tanaka',
            primary_email='taro@example.com',
            payment_provider='stripe',
            paid_at=timezone.now(),
        )
        
        # Cutoff should be 22:00 on check-in day in Tokyo time
        cutoff = compute_approval_cutoff(booking)
        cutoff_tokyo = cutoff.astimezone(tokyo_tz)
        
        self.assertEqual(cutoff_tokyo.date(), today_tokyo)
        self.assertEqual(cutoff_tokyo.time(), time(22, 0))

    def test_cutoff_edge_case_late_payment(self):
        """Test booking made after 22:00 on check-in day expires immediately."""
        # Create booking for today, but "paid" after 22:00 
        today = timezone.now().date()
        
        # Mock a payment made at 23:30 today (after cutoff)
        dublin_tz = pytz.timezone('Europe/Dublin')
        late_payment_local = dublin_tz.localize(
            datetime.combine(today, time(23, 30))
        )
        late_payment_utc = late_payment_local.astimezone(timezone.utc)
        
        booking = self._create_booking(
            today, 
            late_payment_utc,
            payment_intent_id='pi_test_late'
        )
        
        # Cutoff should be 22:00 today
        cutoff = compute_approval_cutoff(booking)
        
        # Payment was after cutoff, so should expire immediately
        self.assertLess(cutoff, late_payment_utc)
        
        # Run expire command
        command = ExpireCommand()
        options = {'dry_run': False, 'max_bookings': 200}
        command.handle(**options)
        
        # Should be expired
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'EXPIRED')

    def test_booking_made_weeks_ago_same_rule(self):
        """Test booking made weeks ago follows same 22:00 rule."""
        # Booking for tomorrow, but made 2 weeks ago
        tomorrow = timezone.now().date() + timedelta(days=1)
        weeks_ago_payment = timezone.now() - timedelta(weeks=2)
        
        booking = self._create_booking(tomorrow, weeks_ago_payment)
        
        # Should still have cutoff at 22:00 on check-in day (tomorrow)
        cutoff = compute_approval_cutoff(booking)
        
        dublin_tz = pytz.timezone('Europe/Dublin')
        cutoff_local = cutoff.astimezone(dublin_tz)
        
        self.assertEqual(cutoff_local.date(), tomorrow)
        self.assertEqual(cutoff_local.time(), time(22, 0))
        
        # Should not expire until tomorrow 22:00, regardless of when it was made
        now = timezone.now()
        self.assertGreater(cutoff, now)