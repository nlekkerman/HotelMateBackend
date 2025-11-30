"""
Phase 3 Tests: Link Clock Logs with Roster Shifts

Test suite for connecting planned roster shifts with actual attendance logs,
including automatic shift association during face clock-in and management
tools for reconciliation.
"""

import json
from datetime import date, time, timedelta, datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from hotel.models import Hotel
from staff.models import Staff, Department, Role
from .models import ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftLocation
from .views import find_matching_shift_for_datetime, shift_to_datetime_range


class ClockRosterLinkingTestCase(APITestCase):
    """Base test case for clock log and roster shift linking"""

    def setUp(self):
        """Create test data for clock-roster linking tests"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@example.com"
        )
        
        # Create department and role
        self.department = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping",
            hotel=self.hotel
        )
        
        self.role = Role.objects.create(
            name="Housekeeper",
            hotel=self.hotel
        )
        
        # Create user and staff
        self.user = User.objects.create_user(
            username="teststaff",
            email="teststaff@example.com",
            password="testpass123"
        )
        
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            first_name="Test",
            last_name="Staff",
            department=self.department,
            role=self.role,
            is_active=True
        )
        
        # Create roster period
        self.period = RosterPeriod.objects.create(
            hotel=self.hotel,
            title="Test Week",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            created_by=self.staff,
            published=True
        )
        
        # Create shift location
        self.location = ShiftLocation.objects.create(
            hotel=self.hotel,
            name="Main Reception",
            color="#0d6efd"
        )
        
        # Authenticate client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Base URL for clock logs
        self.clock_logs_url = f'/staff/{self.hotel.slug}/attendance/clock-logs/'


class ShiftMatchingHelperTests(ClockRosterLinkingTestCase):
    """Test the find_matching_shift_for_datetime helper function"""

    def test_normal_shift_matching(self):
        """Test clock-in within normal shift hours gets matched"""
        # Create normal shift: 09:00-17:00
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Test clock-in at 10:00 on the same day
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNotNone(matched_shift)
        self.assertEqual(matched_shift.id, shift.id)
        self.assertEqual(matched_shift.shift_date, date(2025, 1, 1))
    
    def test_overnight_shift_matching(self):
        """Test overnight shift matching across midnight boundary"""
        # Create overnight shift: 22:00-02:00 (next day)
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),  # January 1st
            shift_start=time(22, 0),      # 10 PM
            shift_end=time(2, 0),         # 2 AM next day
            location=self.location,
            is_night_shift=True
        )
        
        # Test clock-in at 01:00 on January 2nd (within overnight shift)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 2), time(1, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNotNone(matched_shift)
        self.assertEqual(matched_shift.id, shift.id)
        self.assertEqual(matched_shift.shift_date, date(2025, 1, 1))  # Original shift date
    
    def test_no_matching_shift(self):
        """Test when no shift exists for the clock-in time"""
        # Create shift: 09:00-17:00
        StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Test clock-in at 20:00 (outside shift hours)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(20, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNone(matched_shift)
    
    def test_multiple_shifts_picks_earliest(self):
        """Test that when multiple shifts match (edge case), earliest is picked"""
        # This shouldn't happen with proper overlap detection, but test anyway
        shift1 = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(8, 0),
            shift_end=time(12, 0),
            location=self.location
        )
        
        shift2 = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(10, 0),  # Overlaps with shift1
            shift_end=time(14, 0),
            location=self.location
        )
        
        # Clock-in at 11:00 (matches both shifts)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(11, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNotNone(matched_shift)
        # Should pick the earliest starting shift (shift1)
        self.assertEqual(matched_shift.id, shift1.id)


class FaceClockInLinkingTests(ClockRosterLinkingTestCase):
    """Test automatic shift linking during face clock-in"""

    def setUp(self):
        super().setUp()
        
        # Register face for staff
        self.face_encoding = [0.1] * 128  # Mock 128-dim face encoding
        StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            encoding=self.face_encoding
        )
    
    def test_face_clock_in_links_to_shift(self):
        """Test that face clock-in automatically links to matching shift"""
        # Create shift for today: 09:00-17:00
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=now().date(),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Mock face clock-in during shift hours
        with self.settings(USE_TZ=True):
            # Create a mock time within shift hours (10:00 AM)
            from unittest.mock import patch
            mock_time = make_aware(datetime.combine(now().date(), time(10, 0)))
            
            with patch('attendance.views.now', return_value=mock_time):
                response = self.client.post(
                    f'{self.clock_logs_url}face-clock-in/{self.hotel.slug}/',
                    data={'descriptor': self.face_encoding},
                    format='json'
                )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that clock log was created and linked to shift
        log = ClockLog.objects.filter(
            hotel=self.hotel,
            staff=self.staff,
            time_out__isnull=True
        ).first()
        
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.roster_shift)
        self.assertEqual(log.roster_shift.id, shift.id)
        self.assertTrue(log.verified_by_face)
    
    def test_face_clock_in_without_shift(self):
        """Test that face clock-in works even without matching shift"""
        # No shifts created for today
        
        response = self.client.post(
            f'{self.clock_logs_url}face-clock-in/{self.hotel.slug}/',
            data={'descriptor': self.face_encoding},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that clock log was created but not linked to any shift
        log = ClockLog.objects.filter(
            hotel=self.hotel,
            staff=self.staff,
            time_out__isnull=True
        ).first()
        
        self.assertIsNotNone(log)
        self.assertIsNone(log.roster_shift)
        self.assertTrue(log.verified_by_face)
    
    def test_face_clock_out_preserves_shift_link(self):
        """Test that clocking out doesn't change the roster_shift"""
        # Create shift and clock in first
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=now().date(),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Create existing clock-in log with shift link
        existing_log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            verified_by_face=True,
            roster_shift=shift
        )
        
        # Clock out
        response = self.client.post(
            f'{self.clock_logs_url}face-clock-in/{self.hotel.slug}/',
            data={'descriptor': self.face_encoding},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh log and check shift link is preserved
        existing_log.refresh_from_db()
        self.assertIsNotNone(existing_log.time_out)
        self.assertEqual(existing_log.roster_shift.id, shift.id)


class ClockLogSerializerTests(ClockRosterLinkingTestCase):
    """Test ClockLogSerializer with roster_shift fields"""

    def test_serializer_includes_roster_shift_fields(self):
        """Test that serializer includes both input and output roster_shift fields"""
        from .serializers import ClockLogSerializer
        
        # Create shift and clock log
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            roster_shift=shift
        )
        
        serializer = ClockLogSerializer(log)
        data = serializer.data
        
        # Check that roster_shift read field is populated
        self.assertIn('roster_shift', data)
        self.assertIsNotNone(data['roster_shift'])
        self.assertEqual(data['roster_shift']['id'], shift.id)
        self.assertEqual(data['roster_shift']['date'], shift.shift_date)
        self.assertEqual(data['roster_shift']['location'], self.location.name)
        
        # Check that roster_shift_id is in serializer fields
        self.assertIn('roster_shift_id', ClockLogSerializer.Meta.fields)
    
    def test_serializer_write_roster_shift_id(self):
        """Test that roster_shift_id write field works for manual assignment"""
        from .serializers import ClockLogSerializer
        
        # Create shift
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Create log data with roster_shift_id
        log_data = {
            'hotel': self.hotel.id,
            'staff': self.staff.id,
            'roster_shift_id': shift.id
        }
        
        serializer = ClockLogSerializer(data=log_data)
        self.assertTrue(serializer.is_valid())
        
        log = serializer.save()
        self.assertEqual(log.roster_shift.id, shift.id)


class ManagementActionsTests(ClockRosterLinkingTestCase):
    """Test management actions for shift attachment and reconciliation"""

    def test_auto_attach_shift_action(self):
        """Test auto-attach-shift action for single log"""
        # Create shift and unlinked clock log
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Create log during shift hours but without link
        log_time = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=log_time
        )
        
        # Call auto-attach-shift action
        url = f'{self.clock_logs_url}{log.id}/auto-attach-shift/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Shift attached', response.data['detail'])
        self.assertEqual(response.data['roster_shift_id'], shift.id)
        
        # Verify log is now linked
        log.refresh_from_db()
        self.assertEqual(log.roster_shift.id, shift.id)
    
    def test_auto_attach_shift_no_match(self):
        """Test auto-attach-shift when no matching shift exists"""
        # Create log without any shifts
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff
        )
        
        url = f'{self.clock_logs_url}{log.id}/auto-attach-shift/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('No matching shift found', response.data['detail'])
        self.assertIsNone(response.data['roster_shift_id'])
        
        # Verify log remains unlinked
        log.refresh_from_db()
        self.assertIsNone(log.roster_shift)
    
    def test_relink_day_action(self):
        """Test relink-day action for bulk reconciliation"""
        target_date = date(2025, 1, 1)
        
        # Create shifts
        shift1 = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=target_date,
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Create second staff member and shift
        user2 = User.objects.create_user(
            username="staff2",
            email="staff2@example.com",
            password="testpass123"
        )
        
        staff2 = Staff.objects.create(
            user=user2,
            hotel=self.hotel,
            first_name="Staff",
            last_name="Two",
            department=self.department,
            role=self.role,
            is_active=True
        )
        
        shift2 = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=staff2,
            department=self.department,
            period=self.period,
            shift_date=target_date,
            shift_start=time(13, 0),
            shift_end=time(21, 0),
            location=self.location
        )
        
        # Create unlinked logs during shift hours
        log1 = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(target_date, time(10, 0)))
        )
        
        log2 = ClockLog.objects.create(
            hotel=self.hotel,
            staff=staff2,
            time_in=make_aware(datetime.combine(target_date, time(14, 0)))
        )
        
        # Create log outside shift hours (shouldn't be linked)
        log3 = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(target_date, time(22, 0)))
        )
        
        # Call relink-day action
        url = f'{self.clock_logs_url}relink-day/'
        response = self.client.post(url, data={'date': '2025-01-01'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_logs'], 2)  # log1 and log2 linked
        
        # Verify correct linking
        log1.refresh_from_db()
        log2.refresh_from_db()
        log3.refresh_from_db()
        
        self.assertEqual(log1.roster_shift.id, shift1.id)
        self.assertEqual(log2.roster_shift.id, shift2.id)
        self.assertIsNone(log3.roster_shift)  # Outside shift hours
    
    def test_relink_day_specific_staff(self):
        """Test relink-day action with specific staff filter"""
        target_date = date(2025, 1, 1)
        
        # Create shift for main staff
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=target_date,
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=self.location
        )
        
        # Create second staff member
        user2 = User.objects.create_user(
            username="staff2",
            email="staff2@example.com", 
            password="testpass123"
        )
        
        staff2 = Staff.objects.create(
            user=user2,
            hotel=self.hotel,
            first_name="Staff",
            last_name="Two",
            department=self.department,
            role=self.role,
            is_active=True
        )
        
        # Create logs for both staff members
        log1 = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(target_date, time(10, 0)))
        )
        
        log2 = ClockLog.objects.create(
            hotel=self.hotel,
            staff=staff2,
            time_in=make_aware(datetime.combine(target_date, time(10, 0)))
        )
        
        # Call relink-day for specific staff only
        url = f'{self.clock_logs_url}relink-day/'
        response = self.client.post(url, data={
            'date': '2025-01-01',
            'staff_id': self.staff.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_logs'], 1)  # Only log1 processed
        
        # Verify only main staff log was linked
        log1.refresh_from_db()
        log2.refresh_from_db()
        
        self.assertEqual(log1.roster_shift.id, shift.id)
        self.assertIsNone(log2.roster_shift)  # Not processed
    
    def test_relink_day_invalid_date(self):
        """Test relink-day with invalid date format"""
        url = f'{self.clock_logs_url}relink-day/'
        
        # Missing date
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('date is required', response.data['detail'])
        
        # Invalid date format
        response = self.client.post(url, data={'date': 'invalid-date'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid date format', response.data['detail'])


class OvernightShiftLinkingTests(ClockRosterLinkingTestCase):
    """Test overnight shift linking scenarios"""

    def test_overnight_shift_clock_in_same_day(self):
        """Test clocking in during start of overnight shift (same day)"""
        # Create overnight shift: Jan 1 22:00 - Jan 2 02:00
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(22, 0),
            shift_end=time(2, 0),
            location=self.location,
            is_night_shift=True
        )
        
        # Clock in at 22:30 on Jan 1 (start of shift)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(22, 30)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNotNone(matched_shift)
        self.assertEqual(matched_shift.id, shift.id)
    
    def test_overnight_shift_clock_in_next_day(self):
        """Test clocking in during end of overnight shift (next day)"""
        # Create overnight shift: Jan 1 22:00 - Jan 2 02:00
        shift = StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=date(2025, 1, 1),
            shift_start=time(22, 0),
            shift_end=time(2, 0),
            location=self.location,
            is_night_shift=True
        )
        
        # Clock in at 01:00 on Jan 2 (end of shift, next day)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 2), time(1, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,
            staff=self.staff,
            current_dt=clock_dt
        )
        
        self.assertIsNotNone(matched_shift)
        self.assertEqual(matched_shift.id, shift.id)
        # Original shift date should be preserved
        self.assertEqual(matched_shift.shift_date, date(2025, 1, 1))
    
    def test_overnight_shift_datetime_range_helper(self):
        """Test that shift_to_datetime_range helper works correctly for overnight shifts"""
        # Test normal shift
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(9, 0), time(17, 0)
        )
        
        expected_start = datetime.combine(date(2025, 1, 1), time(9, 0))
        expected_end = datetime.combine(date(2025, 1, 1), time(17, 0))
        
        self.assertEqual(start_dt, expected_start)
        self.assertEqual(end_dt, expected_end)
        
        # Test overnight shift
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(22, 0), time(2, 0)
        )
        
        expected_start = datetime.combine(date(2025, 1, 1), time(22, 0))
        expected_end = datetime.combine(date(2025, 1, 2), time(2, 0))  # Next day
        
        self.assertEqual(start_dt, expected_start)
        self.assertEqual(end_dt, expected_end)


class SecurityAndPermissionTests(ClockRosterLinkingTestCase):
    """Test security and permission aspects of clock-roster linking"""

    def setUp(self):
        super().setUp()
        
        # Create second hotel and staff for cross-hotel testing
        self.hotel_b = Hotel.objects.create(
            name="Hotel B",
            slug="hotel-b",
            email="hotelb@example.com"
        )
        
        self.department_b = Department.objects.create(
            name="Reception",
            slug="reception",
            hotel=self.hotel_b
        )
        
        self.role_b = Role.objects.create(
            name="Receptionist",
            hotel=self.hotel_b
        )
        
        self.user_b = User.objects.create_user(
            username="staffb",
            email="staffb@example.com",
            password="testpass123"
        )
        
        self.staff_b = Staff.objects.create(
            user=self.user_b,
            hotel=self.hotel_b,
            first_name="Staff",
            last_name="B",
            department=self.department_b,
            role=self.role_b,
            is_active=True
        )
    
    def test_cross_hotel_shift_isolation(self):
        """Test that shifts from other hotels are not matched"""
        # Create shift in hotel B
        period_b = RosterPeriod.objects.create(
            hotel=self.hotel_b,
            title="Hotel B Week",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 7),
            created_by=self.staff_b
        )
        
        location_b = ShiftLocation.objects.create(
            hotel=self.hotel_b,
            name="Hotel B Reception",
            color="#ff0000"
        )
        
        shift_b = StaffRoster.objects.create(
            hotel=self.hotel_b,
            staff=self.staff_b,
            department=self.department_b,
            period=period_b,
            shift_date=date(2025, 1, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            location=location_b
        )
        
        # Try to match staff from hotel A against hotel B shift
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        
        matched_shift = find_matching_shift_for_datetime(
            hotel=self.hotel,  # Hotel A
            staff=self.staff,  # Staff A
            current_dt=clock_dt
        )
        
        # Should not match shift from hotel B
        self.assertIsNone(matched_shift)
    
    def test_management_action_hotel_scoping(self):
        """Test that management actions respect hotel scoping"""
        # Create log in hotel A
        log_a = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff
        )
        
        # Try to access from hotel A context (should work)
        url = f'{self.clock_logs_url}{log_a.id}/auto-attach-shift/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to access hotel A log from hotel B context (should fail)
        hotel_b_url = f'/staff/{self.hotel_b.slug}/attendance/clock-logs/{log_a.id}/auto-attach-shift/'
        response = self.client.post(hotel_b_url)
        # Should fail due to hotel scoping (404 or 403)
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])