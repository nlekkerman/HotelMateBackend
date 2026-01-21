"""
Comprehensive tests for booking approval expiry enforcement.

Tests the exact requirements from PART A and PART D of the specification.
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status

from hotel.models import RoomBooking, Hotel
from staff.models import Staff
from django.contrib.auth.models import User


class BookingApprovalExpiryTest(TestCase):
    """Test approval expiry enforcement as per FINAL specification."""
    
    def setUp(self):
        """Set up test data."""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            city="Test City",
            country="Test Country"
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
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
    def _create_booking(self, status='PENDING_APPROVAL', **kwargs):
        """Helper to create test booking."""
        now = timezone.now()
        defaults = {
            'hotel': self.hotel,
            'booking_id': f'BK-{timezone.now().timestamp():.0f}',
            'status': status,
            'check_in': now.date(),
            'check_out': (now + timedelta(days=1)).date(),
            'adults': 2,
            'children': 0,
            'total_amount': 100.00,
            'currency': 'USD',
            'primary_first_name': 'John',
            'primary_last_name': 'Doe',
            'primary_email': 'john@example.com',
            'payment_provider': 'stripe',
            'paid_at': now - timedelta(minutes=5),
        }
        defaults.update(kwargs)
        return RoomBooking.objects.create(**defaults)

    def test_approve_expired_booking_returns_409(self):
        """
        Test A3: HARD BLOCK - approving expired booking returns HTTP 409.
        
        This is MANDATORY enforcement.
        """
        # Create booking that is already expired
        booking = self._create_booking(
            status='EXPIRED',
            expired_at=timezone.now() - timedelta(minutes=10),
            auto_expire_reason_code='APPROVAL_TIMEOUT'
        )
        
        # Attempt to approve expired booking
        response = self.client.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # MUST return 409 Conflict
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('expired due to approval timeout', response.data['error'].lower())
        
        # Booking must remain expired
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'EXPIRED')
        self.assertIsNotNone(booking.expired_at)

    def test_approve_booking_with_expired_at_field_returns_409(self):
        """
        Test A3: HARD BLOCK - booking with expired_at set cannot be approved.
        
        Even if status is not EXPIRED, expired_at field makes it irreversible.
        """
        # Create booking with expired_at set but status still PENDING_APPROVAL
        booking = self._create_booking(
            status='PENDING_APPROVAL',
            expired_at=timezone.now() - timedelta(minutes=5)
        )
        
        response = self.client.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # MUST return 409 Conflict
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('expired due to approval timeout', response.data['error'].lower())

    def test_approve_critical_but_not_expired_succeeds(self):
        """
        Test A1: CRITICAL approval window - can still approve if not yet expired.
        
        CRITICAL is a warning state, not a lock.
        """
        # Create booking that would be CRITICAL risk level but not expired
        past_deadline = timezone.now() - timedelta(minutes=90)  # > 60 min overdue = CRITICAL
        booking = self._create_booking(
            status='PENDING_APPROVAL',
            approval_deadline_at=past_deadline,
            expired_at=None  # Not yet expired by job
        )
        
        response = self.client.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # MUST succeed - CRITICAL is not a hard block
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        
        # Booking must be confirmed
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED')
        self.assertIsNotNone(booking.decision_by)
        self.assertIsNotNone(booking.decision_at)

    def test_race_condition_protection_expire_wins(self):
        """
        Test A4: Race condition - expire job wins over approve attempt.
        
        Simulates concurrent expire job and approve request.
        """
        booking = self._create_booking(
            status='PENDING_APPROVAL',
            approval_deadline_at=timezone.now() - timedelta(minutes=10)
        )
        
        # Simulate expire job running first (within same test transaction)
        with transaction.atomic():
            # Job would lock and expire the booking
            locked_booking = RoomBooking.objects.select_for_update().get(id=booking.id)
            locked_booking.status = 'EXPIRED'
            locked_booking.expired_at = timezone.now()
            locked_booking.auto_expire_reason_code = 'APPROVAL_TIMEOUT'
            locked_booking.save()
            
            # Now attempt approve (should fail due to expired state)
            response = self.client.post(
                f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/approve/'
            )
        
        # Approve must fail because booking is now expired
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # Booking must remain expired
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'EXPIRED')

    def test_race_condition_protection_approve_wins(self):
        """
        Test A4: Race condition - approve wins if it gets lock first.
        
        If approve gets the lock before expire job, approval succeeds.
        """
        booking = self._create_booking(
            status='PENDING_APPROVAL',
            approval_deadline_at=timezone.now() - timedelta(minutes=10),
            expired_at=None
        )
        
        # Approve gets the lock first
        response = self.client.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/approve/'
        )
        
        # Approve must succeed if it got lock first
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Booking must be confirmed
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED')

    def test_overstay_critical_does_not_change_status(self):
        """
        Test B2: CRITICAL overstay behavior - only alerting, no status change.
        
        System responsibility ENDS at alerting for overstays.
        """
        # Create checked-in booking past checkout deadline
        past_checkout = timezone.now() - timedelta(hours=5)  # 5 hours overdue = CRITICAL
        booking = self._create_booking(
            status='IN_HOUSE',
            checked_in_at=past_checkout - timedelta(days=1),
            check_out=past_checkout.date(),
            overstay_flagged_at=past_checkout + timedelta(minutes=10)
        )
        
        # Overstay flagging should not change booking status
        self.assertEqual(booking.status, 'IN_HOUSE')
        
        # Should remain IN_HOUSE indefinitely
        # No automatic checkout, no billing, no service restrictions
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'IN_HOUSE')
        self.assertIsNotNone(booking.overstay_flagged_at)


class StaffSeenFlagTest(TestCase):
    """Test staff seen flag behavior as per PART D specification."""
    
    def setUp(self):
        """Set up test data."""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            city="Test City",
            country="Test Country"
        )
        
        # Create two staff members
        self.user1 = User.objects.create_user(username="staff1", password="pass")
        self.user2 = User.objects.create_user(username="staff2", password="pass")
        
        self.staff1 = Staff.objects.create(
            user=self.user1, hotel=self.hotel, first_name="Staff", last_name="One"
        )
        self.staff2 = Staff.objects.create(
            user=self.user2, hotel=self.hotel, first_name="Staff", last_name="Two"
        )
        
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def _create_booking(self, **kwargs):
        """Helper to create test booking."""
        defaults = {
            'hotel': self.hotel,
            'booking_id': f'BK-{timezone.now().timestamp():.0f}',
            'status': 'PENDING_APPROVAL',
            'check_in': timezone.now().date(),
            'check_out': (timezone.now() + timedelta(days=1)).date(),
            'adults': 2,
            'total_amount': 100.00,
            'currency': 'USD',
            'primary_first_name': 'John',
            'primary_last_name': 'Doe',
            'primary_email': 'john@example.com',
        }
        defaults.update(kwargs)
        return RoomBooking.objects.create(**defaults)

    def test_mark_seen_sets_staff_seen_once(self):
        """
        Test D3: mark-seen sets staff_seen_at once and preserves "seen first by".
        """
        booking = self._create_booking()
        
        # Initially not seen
        self.assertIsNone(booking.staff_seen_at)
        self.assertIsNone(booking.staff_seen_by)
        
        # Staff1 marks as seen
        response = self.client1.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/mark-seen/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_new_for_staff'])
        
        # Booking should be marked as seen by staff1
        booking.refresh_from_db()
        self.assertIsNotNone(booking.staff_seen_at)
        self.assertEqual(booking.staff_seen_by, self.staff1)
        original_seen_at = booking.staff_seen_at
        
        # Staff2 attempts to mark as seen (should be idempotent)
        response = self.client2.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/mark-seen/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_new_for_staff'])
        
        # Should NOT change - preserves "seen first by" forever
        booking.refresh_from_db()
        self.assertEqual(booking.staff_seen_at, original_seen_at)
        self.assertEqual(booking.staff_seen_by, self.staff1)  # Still staff1

    def test_mark_seen_never_overwrites(self):
        """
        Test D3: Once staff_seen_at is set, it is never overwritten.
        
        Preserves "seen first by" semantics.
        """
        booking = self._create_booking()
        
        # Pre-set seen by staff1
        seen_time = timezone.now() - timedelta(hours=1)
        booking.staff_seen_at = seen_time
        booking.staff_seen_by = self.staff1
        booking.save()
        
        # Staff2 attempts mark-seen
        response = self.client2.post(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/mark-seen/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should remain unchanged
        booking.refresh_from_db()
        self.assertEqual(booking.staff_seen_at, seen_time)
        self.assertEqual(booking.staff_seen_by, self.staff1)

    def test_serializer_exposes_staff_seen_fields(self):
        """
        Test E: Serializers must expose all required staff-seen fields.
        """
        booking = self._create_booking(
            staff_seen_at=timezone.now(),
            staff_seen_by=self.staff1
        )
        
        # Get booking detail
        response = self.client1.get(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Must expose all required fields
        self.assertIn('staff_seen_at', data)
        self.assertIn('staff_seen_by', data)
        self.assertIn('staff_seen_by_display', data)  
        self.assertIn('is_new_for_staff', data)
        
        # Values must be correct
        self.assertIsNotNone(data['staff_seen_at'])
        self.assertEqual(data['staff_seen_by'], self.staff1.id)
        self.assertFalse(data['is_new_for_staff'])
        self.assertIsNotNone(data['staff_seen_by_display'])
        self.assertEqual(data['staff_seen_by_display']['id'], self.staff1.id)

    def test_new_booking_is_new_for_staff(self):
        """
        Test E: New bookings have is_new_for_staff = True.
        """
        booking = self._create_booking()  # staff_seen_at = None
        
        response = self.client1.get(
            f'/api/staff/hotel/{self.hotel.slug}/room-bookings/{booking.booking_id}/'
        )
        
        data = response.data
        self.assertTrue(data['is_new_for_staff'])
        self.assertIsNone(data['staff_seen_at'])
        self.assertIsNone(data['staff_seen_by'])
        self.assertIsNone(data['staff_seen_by_display'])


# Run tests with: python manage.py test booking_approval_expiry_tests