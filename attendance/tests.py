"""
Comprehensive security tests for attendance/roster system multi-hotel isolation.

These tests ensure that:
1. Staff members can only access their own hotel's data
2. Cross-hotel data leakage is prevented
3. Permission classes work correctly
4. Face recognition endpoints are secure
5. Copy operations respect hotel boundaries
6. Payload injection attacks are blocked
"""

import json
from datetime import date, time, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from hotel.models import Hotel
from staff.models import Staff, Department, Role
from .models import (
    ClockLog, StaffFace, RosterPeriod, StaffRoster, 
    ShiftLocation, DailyPlan, DailyPlanEntry
)


class MultiHotelSecurityTestCase(APITestCase):
    """Base test case with multi-hotel setup"""
    
    def setUp(self):
        """Create test hotels and staff members"""
        # Create hotels
        self.hotel_a = Hotel.objects.create(
            name="Hotel Alpha",
            slug="hotel-alpha",
            email="alpha@example.com"
        )
        self.hotel_b = Hotel.objects.create(
            name="Hotel Beta", 
            slug="hotel-beta",
            email="beta@example.com"
        )
        
        # Create departments and roles
        self.department_a = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping",
            hotel=self.hotel_a
        )
        self.department_b = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping", 
            hotel=self.hotel_b
        )
        
        self.role_staff = Role.objects.create(
            name="Staff Member",
            slug="staff"
        )
        
        # Create users and staff profiles
        self.user_a = User.objects.create_user(
            username="staff_a",
            email="staff_a@example.com",
            password="testpass123"
        )
        self.staff_a = Staff.objects.create(
            user=self.user_a,
            first_name="Alice",
            last_name="Alpha",
            hotel=self.hotel_a,
            department=self.department_a,
            role=self.role_staff,
            employee_id="EMP001"
        )
        
        self.user_b = User.objects.create_user(
            username="staff_b",
            email="staff_b@example.com", 
            password="testpass123"
        )
        self.staff_b = Staff.objects.create(
            user=self.user_b,
            first_name="Bob",
            last_name="Beta",
            hotel=self.hotel_b,
            department=self.department_b,
            role=self.role_staff,
            employee_id="EMP002"
        )
        
        # Create test data for each hotel
        self.period_a = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Week 1 Alpha",
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 7),
            created_by=self.staff_a
        )
        
        self.period_b = RosterPeriod.objects.create(
            hotel=self.hotel_b,
            title="Week 1 Beta",
            start_date=date(2025, 12, 1), 
            end_date=date(2025, 12, 7),
            created_by=self.staff_b
        )
        
        self.shift_a = StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 2),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            department=self.department_a
        )
        
        self.shift_b = StaffRoster.objects.create(
            hotel=self.hotel_b,
            staff=self.staff_b, 
            period=self.period_b,
            shift_date=date(2025, 12, 2),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            department=self.department_b
        )


class AttendancePermissionTests(MultiHotelSecurityTestCase):
    """Test permission enforcement across attendance endpoints"""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are rejected"""
        endpoints = [
            f'/api/attendance/{self.hotel_a.slug}/periods/',
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_staff_user_access_denied(self):
        """Test that users without staff profile are rejected"""
        regular_user = User.objects.create_user(
            username="regular_user",
            password="testpass123"
        )
        
        self.client.force_authenticate(user=regular_user)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/periods/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("staff member", response.data['detail'].lower())
    
    def test_cross_hotel_access_denied(self):
        """Test that staff cannot access other hotel's data"""
        self.client.force_authenticate(user=self.user_a)
        
        # Staff A trying to access Hotel B's data
        response = self.client.get(f'/api/attendance/{self.hotel_b.slug}/periods/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("access to this hotel", response.data['detail'].lower())
    
    def test_same_hotel_access_allowed(self):
        """Test that staff can access their own hotel's data"""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RosterPeriodSecurityTests(MultiHotelSecurityTestCase):
    """Test security for roster period endpoints"""
    
    def test_period_list_scoped_to_hotel(self):
        """Test that period list only shows own hotel's periods"""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see Hotel A's period
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Week 1 Alpha')
    
    def test_period_create_enforces_hotel(self):
        """Test that created periods are assigned to correct hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'title': 'New Period',
            'start_date': '2025-12-8',
            'end_date': '2025-12-14',
            # Attempt to inject Hotel B's ID
            'hotel': self.hotel_b.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/periods/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify period was created for Hotel A, not Hotel B
        period = RosterPeriod.objects.get(id=response.data['id'])
        self.assertEqual(period.hotel.id, self.hotel_a.id)
        self.assertEqual(period.created_by.id, self.staff_a.id)
    
    def test_period_detail_cross_hotel_blocked(self):
        """Test that accessing other hotel's period details is blocked"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access Hotel B's period via Hotel A's URL
        response = self.client.get(
            f'/api/attendance/{self.hotel_a.slug}/periods/{self.period_b.id}/'
        )
        
        # Should return 404 because period doesn't exist in Hotel A's scope
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StaffRosterSecurityTests(MultiHotelSecurityTestCase):
    """Test security for staff roster endpoints"""
    
    def test_roster_list_scoped_to_hotel(self):
        """Test that roster list only shows own hotel's shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/shifts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see Hotel A's shifts
        shift_hotels = [shift['hotel'] for shift in response.data]
        self.assertTrue(all(hotel == self.hotel_a.id for hotel in shift_hotels))
    
    def test_roster_create_enforces_hotel(self):
        """Test that created shifts are assigned to correct hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-03',
            'shift_start': '10:00',
            'shift_end': '18:00',
            'department': self.department_a.id,
            # Attempt to inject Hotel B's ID
            'hotel': self.hotel_b.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify shift was created for Hotel A, not Hotel B
        shift = StaffRoster.objects.get(id=response.data['id'])
        self.assertEqual(shift.hotel.id, self.hotel_a.id)
    
    def test_bulk_save_enforces_hotel_security(self):
        """Test that bulk save operations respect hotel boundaries"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'hotel': self.hotel_a.id,
            'period': self.period_a.id,
            'shifts': [
                {
                    'staff': self.staff_a.id,
                    'shift_date': '2025-12-04',
                    'shift_start': '09:00',
                    'shift_end': '17:00',
                    'department': self.department_a.id,
                    # Attempt injection
                    'hotel': self.hotel_b.id
                }
            ]
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/bulk-save/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify all created shifts belong to Hotel A
        created_shifts = response.data['created']
        for shift_data in created_shifts:
            shift = StaffRoster.objects.get(id=shift_data['id'])
            self.assertEqual(shift.hotel.id, self.hotel_a.id)


class FaceRecognitionSecurityTests(MultiHotelSecurityTestCase):
    """Test security for face recognition endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create face data for testing
        self.face_descriptor = [0.1] * 128  # Mock 128-dim face descriptor
    
    def test_register_face_hotel_validation(self):
        """Test that face registration validates hotel access"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to register face for Hotel B (should fail)
        response = self.client.post(
            f'/api/attendance/register-face/{self.hotel_b.slug}/',
            {'descriptor': self.face_descriptor}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("access to this hotel", response.data['error'])
    
    def test_face_clock_in_hotel_validation(self):
        """Test that face clock-in validates hotel access"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to clock in at Hotel B (should fail)
        response = self.client.post(
            f'/api/attendance/face-clock-in/{self.hotel_b.slug}/',
            {'descriptor': self.face_descriptor}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("access to this hotel", response.data['error'])
    
    def test_face_detect_hotel_validation(self):
        """Test that face detection validates hotel access"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to detect face at Hotel B (should fail)
        response = self.client.post(
            f'/api/attendance/detect/{self.hotel_b.slug}/',
            {'descriptor': self.face_descriptor}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("access to this hotel", response.data['error'])


class ClockLogSecurityTests(MultiHotelSecurityTestCase):
    """Test security for clock log endpoints"""
    
    def test_clock_log_list_scoped_to_hotel(self):
        """Test that clock logs are scoped to user's hotel"""
        # Create clock logs for both hotels
        ClockLog.objects.create(hotel=self.hotel_a, staff=self.staff_a)
        ClockLog.objects.create(hotel=self.hotel_b, staff=self.staff_b)
        
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/clock-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see Hotel A's logs
        log_hotels = [log['hotel'] for log in response.data]
        self.assertTrue(all(hotel == self.hotel_a.id for hotel in log_hotels))
    
    def test_currently_clocked_in_hotel_validation(self):
        """Test that currently clocked in endpoint validates hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access Hotel B's currently clocked in staff
        response = self.client.get(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/currently-clocked-in/',
            {'hotel_slug': self.hotel_b.slug}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_status_endpoint_hotel_validation(self):
        """Test that status endpoint validates hotel access"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to check status for Hotel B
        response = self.client.get(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/status/',
            {'hotel_slug': self.hotel_b.slug}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ShiftLocationSecurityTests(MultiHotelSecurityTestCase):
    """Test security for shift location endpoints"""
    
    def setUp(self):
        super().setUp()
        self.location_a = ShiftLocation.objects.create(
            hotel=self.hotel_a,
            name="Reception A",
            color="#ff0000"
        )
        self.location_b = ShiftLocation.objects.create(
            hotel=self.hotel_b,
            name="Reception B", 
            color="#00ff00"
        )
    
    def test_location_list_scoped_to_hotel(self):
        """Test that locations are scoped to user's hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see Hotel A's locations
        location_names = [loc['name'] for loc in response.data]
        self.assertIn("Reception A", location_names)
        self.assertNotIn("Reception B", location_names)
    
    def test_location_create_enforces_hotel(self):
        """Test that created locations are assigned to correct hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'name': 'New Location',
            'color': '#0000ff',
            # Attempt injection
            'hotel': self.hotel_b.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/locations/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify location was created for Hotel A
        location = ShiftLocation.objects.get(id=response.data['id'])
        self.assertEqual(location.hotel.id, self.hotel_a.id)


class DailyPlanSecurityTests(MultiHotelSecurityTestCase):
    """Test security for daily plan endpoints"""
    
    def setUp(self):
        super().setUp()
        self.plan_a = DailyPlan.objects.create(
            hotel=self.hotel_a,
            date=date(2025, 12, 2)
        )
        self.plan_b = DailyPlan.objects.create(
            hotel=self.hotel_b,
            date=date(2025, 12, 2)
        )
    
    def test_daily_plan_list_scoped_to_hotel(self):
        """Test that daily plans are scoped to user's hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.get(f'/api/attendance/{self.hotel_a.slug}/daily-plans/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see Hotel A's plans
        plan_hotels = [plan['hotel'] for plan in response.data]
        self.assertTrue(all(hotel == self.hotel_a.id for hotel in plan_hotels))
    
    def test_daily_plan_entry_cross_hotel_blocked(self):
        """Test that accessing other hotel's plan entries is blocked"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access Hotel B's plan entries via Hotel A's URL
        response = self.client.get(
            f'/api/attendance/{self.hotel_a.slug}/daily-plans/{self.plan_b.id}/entries/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CopyOperationSecurityTests(MultiHotelSecurityTestCase):
    """Test security for roster copy operations"""
    
    def test_copy_roster_bulk_hotel_validation(self):
        """Test that bulk copy validates hotel ownership"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to copy from Hotel B's period to Hotel A's period
        data = {
            'source_period_id': self.period_b.id,
            'target_period_id': self.period_a.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-roster-bulk/',
            data
        )
        
        # Should fail because source period belongs to Hotel B
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_copy_day_all_hotel_scoped(self):
        """Test that day copy is scoped to hotel"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'source_date': '2025-12-02',
            'target_date': '2025-12-03'
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-roster-day-all/',
            data
        )
        
        # Should succeed and only copy Hotel A's shifts
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_copy_week_staff_hotel_validation(self):
        """Test that staff week copy validates hotel access"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'staff_id': self.staff_a.id,
            'source_period_id': self.period_a.id,
            'target_period_id': self.period_b.id  # Different hotel
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-week-staff/',
            data
        )
        
        # Should fail because target period belongs to Hotel B
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PayloadInjectionSecurityTests(MultiHotelSecurityTestCase):
    """Test protection against payload injection attacks"""
    
    def test_roster_period_hotel_injection_blocked(self):
        """Test that hotel field injection is blocked in roster periods"""
        self.client.force_authenticate(user=self.user_a)
        
        # Attempt to create period with injected hotel
        malicious_data = {
            'title': 'Malicious Period',
            'start_date': '2025-12-15',
            'end_date': '2025-12-21',
            'hotel': self.hotel_b.id,  # Injection attempt
            'hotel_id': self.hotel_b.id,  # Alternative injection
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/periods/',
            malicious_data
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            # Verify period was created for Hotel A, not Hotel B
            period = RosterPeriod.objects.get(id=response.data['id'])
            self.assertEqual(period.hotel.id, self.hotel_a.id)
    
    def test_staff_roster_hotel_injection_blocked(self):
        """Test that hotel field injection is blocked in staff rosters"""
        self.client.force_authenticate(user=self.user_a)
        
        malicious_data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-05',
            'shift_start': '09:00',
            'shift_end': '17:00',
            'department': self.department_a.id,
            'hotel': self.hotel_b.id,  # Injection attempt
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            malicious_data
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            # Verify shift was created for Hotel A, not Hotel B
            shift = StaffRoster.objects.get(id=response.data['id'])
            self.assertEqual(shift.hotel.id, self.hotel_a.id)


class OvernightShiftAndOverlapTests(MultiHotelSecurityTestCase):
    """Test overnight shifts and overlap detection functionality"""
    
    def test_overnight_shift_validation_valid(self):
        """Test that valid overnight shifts are accepted"""
        self.client.force_authenticate(user=self.user_a)
        
        # Valid overnight shift: 10 PM to 2 AM next day
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-03',
            'shift_start': '22:00',
            'shift_end': '02:00',  # Next day
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify shift was created with correct properties
        shift = StaffRoster.objects.get(id=response.data['id'])
        self.assertTrue(shift.is_night_shift)
        self.assertEqual(shift.expected_hours, 4.0)  # 22:00-02:00 = 4 hours
    
    def test_overnight_shift_exceeds_max_duration(self):
        """Test that overnight shifts exceeding max duration are rejected"""
        self.client.force_authenticate(user=self.user_a)
        
        # Invalid overnight shift: 18:00 to 10:00 next day (16 hours)
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-03',
            'shift_start': '18:00',
            'shift_end': '10:00',  # 16 hours - too long
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('exceeds maximum', str(response.data))
    
    def test_overnight_shift_invalid_end_time(self):
        """Test that overnight shifts ending too late are rejected"""
        self.client.force_authenticate(user=self.user_a)
        
        # Invalid overnight shift: ends at 8 AM (too late)
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-03',
            'shift_start': '23:00',
            'shift_end': '08:00',  # Too late for overnight
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot end after', str(response.data))
    
    def test_overlap_same_staff_same_day_regular_shifts(self):
        """Test that overlapping regular shifts for same staff are blocked"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create first shift: 09:00-17:00
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 4),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            department=self.department_a
        )
        
        # Try to create overlapping shift: 16:00-23:00
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-04',
            'shift_start': '16:00',  # Overlaps with existing 09:00-17:00
            'shift_end': '23:00',
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        # Should be blocked due to overlap
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_overlap_overnight_shifts(self):
        """Test that overlapping overnight shifts are detected"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create first overnight shift: 22:00-02:00
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 4),
            shift_start=time(22, 0),
            shift_end=time(2, 0),  # Next day
            department=self.department_a,
            is_night_shift=True
        )
        
        # Try to create overlapping overnight shift: 01:00-05:00
        data = {
            'staff': self.staff_a.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-04',
            'shift_start': '01:00',  # Overlaps with 22:00-02:00
            'shift_end': '05:00',
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        # Should be blocked due to overlap
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_no_overlap_different_staff_same_times(self):
        """Test that different staff can work same times without conflict"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create shift for staff A
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 4),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            department=self.department_a
        )
        
        # Create second staff member for hotel A
        user_a2 = User.objects.create_user(
            username="staff_a2",
            password="testpass123"
        )
        staff_a2 = Staff.objects.create(
            user=user_a2,
            first_name="Alice2",
            last_name="Alpha2",
            hotel=self.hotel_a,
            department=self.department_a,
            role=self.role_staff,
            employee_id="EMP003"
        )
        
        # Create same-time shift for different staff - should be allowed
        data = {
            'staff': staff_a2.id,
            'period': self.period_a.id,
            'shift_date': '2025-12-04',
            'shift_start': '09:00',  # Same as staff A
            'shift_end': '17:00',    # Same as staff A
            'department': self.department_a.id,
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/',
            data
        )
        
        # Should be allowed - different staff
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_bulk_save_blocks_overlaps(self):
        """Test that bulk save blocks overlapping shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'hotel': self.hotel_a.id,
            'period': self.period_a.id,
            'shifts': [
                {
                    'staff': self.staff_a.id,
                    'shift_date': '2025-12-05',
                    'shift_start': '09:00',
                    'shift_end': '17:00',
                    'department': self.department_a.id,
                },
                {
                    'staff': self.staff_a.id,
                    'shift_date': '2025-12-05',
                    'shift_start': '16:00',  # Overlaps with first shift
                    'shift_end': '23:00',
                    'department': self.department_a.id,
                }
            ]
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/bulk-save/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlapping shifts', response.data['detail'].lower())
    
    def test_bulk_save_accepts_valid_overnight_shifts(self):
        """Test that bulk save accepts valid overnight shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        data = {
            'hotel': self.hotel_a.id,
            'period': self.period_a.id,
            'shifts': [
                {
                    'staff': self.staff_a.id,
                    'shift_date': '2025-12-05',
                    'shift_start': '22:00',
                    'shift_end': '02:00',  # Overnight
                    'department': self.department_a.id,
                }
            ]
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shifts/bulk-save/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify overnight shift properties
        shift_id = response.data['created'][0]['id']
        shift = StaffRoster.objects.get(id=shift_id)
        self.assertTrue(shift.is_night_shift)
        self.assertEqual(shift.expected_hours, 4.0)
    
    def test_copy_day_blocks_overlapping_shifts(self):
        """Test that copy day operation blocks overlapping shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create source shift
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 2),  # Source date
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            department=self.department_a
        )
        
        # Create target date shift that would overlap
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=self.period_a,
            shift_date=date(2025, 12, 3),  # Target date
            shift_start=time(14, 0),
            shift_end=time(22, 0),
            department=self.department_a
        )
        
        # Try to copy - should fail due to overlap
        data = {
            'source_date': '2025-12-02',
            'target_date': '2025-12-03'
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-roster-day-all/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlapping shifts', response.data['detail'].lower())
    
    def test_copy_bulk_blocks_overlapping_shifts(self):
        """Test that bulk copy operation blocks overlapping shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create target period with existing shift
        target_period = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Week 2 Alpha",
            start_date=date(2025, 12, 8),
            end_date=date(2025, 12, 14),
            created_by=self.staff_a
        )
        
        # Create existing shift in target period
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=target_period,
            shift_date=date(2025, 12, 9),  # Monday in target week
            shift_start=time(14, 0),
            shift_end=time(22, 0),
            department=self.department_a
        )
        
        # Try to copy from source period (shift on same date would overlap)
        data = {
            'source_period_id': self.period_a.id,
            'target_period_id': target_period.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-roster-bulk/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlapping shifts', response.data['detail'].lower())
    
    def test_copy_week_staff_blocks_overlapping_shifts(self):
        """Test that copy week staff operation blocks overlapping shifts"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create target period with existing shift for same staff
        target_period = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Week 2 Alpha",
            start_date=date(2025, 12, 8),
            end_date=date(2025, 12, 14),
            created_by=self.staff_a
        )
        
        # Create existing shift in target period for same staff
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            period=target_period,
            shift_date=date(2025, 12, 9),  # Monday
            shift_start=time(14, 0),
            shift_end=time(22, 0),
            department=self.department_a
        )
        
        # Try to copy staff week - should fail due to overlap
        data = {
            'staff_id': self.staff_a.id,
            'source_period_id': self.period_a.id,
            'target_period_id': target_period.id
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/shift-copy/copy-week-staff/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('overlapping shifts', response.data['detail'].lower())


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: UNROSTERED APPROVAL, BREAK/OVERTIME ALERTS & PERIOD FINALIZATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class UnrosteredClockInTestCase(MultiHotelSecurityTestCase):
    """Test unrostered clock-in approval flow"""
    
    def setUp(self):
        super().setUp()
        
        # Create attendance settings for hotel_a
        from hotel.models import AttendanceSettings
        self.attendance_settings_a = AttendanceSettings.objects.create(
            hotel=self.hotel_a,
            break_warning_hours=6.0,
            overtime_warning_hours=10.0,
            hard_limit_hours=12.0,
            enforce_limits=True
        )
        
        # Create roster period but no shifts for testing unrostered scenario
        self.period_a = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Test Week",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
            created_by=self.manager_a
        )
    
    def test_face_clock_in_with_no_roster_returns_unrostered_detection(self):
        """Test that face clock-in detects unrostered scenario"""
        # Mock face recognition descriptor
        descriptor = [0.1] * 128
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/face-clock/',
            {'descriptor': descriptor}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'unrostered_detected')
        self.assertTrue(response.data['requires_confirmation'])
        self.assertIn('confirmation_endpoint', response.data)
    
    def test_unrostered_confirm_creates_pending_approval_log(self):
        """Test unrostered confirmation creates log pending approval"""
        data = {
            'staff_id': self.staff_a.id,
            'confirmed': True
        }
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/unrostered-confirm/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action'], 'unrostered_clock_in_created')
        
        # Check log was created correctly
        log = ClockLog.objects.get(id=response.data['log']['id'])
        self.assertTrue(log.is_unrostered)
        self.assertFalse(log.is_approved)
        self.assertFalse(log.is_rejected)
        self.assertIsNone(log.roster_shift)
        
        # Check staff is marked as on duty
        self.staff_a.refresh_from_db()
        self.assertTrue(self.staff_a.is_on_duty)
    
    def test_manager_can_approve_unrostered_log(self):
        """Test manager approval of unrostered clock-in"""
        # Create unrostered log
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False
        )
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/{log.id}/approve/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check log was approved
        log.refresh_from_db()
        self.assertTrue(log.is_approved)
        self.assertFalse(log.is_rejected)
    
    def test_manager_can_reject_unrostered_log(self):
        """Test manager rejection of unrostered clock-in"""
        # Create unrostered log (still open)
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False
        )
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/{log.id}/reject/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check log was rejected and closed
        log.refresh_from_db()
        self.assertFalse(log.is_approved)
        self.assertTrue(log.is_rejected)
        self.assertIsNotNone(log.time_out)  # Should be auto-clocked out
        
        # Check staff is no longer on duty
        self.staff_a.refresh_from_db()
        self.assertFalse(self.staff_a.is_on_duty)
    
    def test_cannot_approve_log_from_different_hotel(self):
        """Test cross-hotel security for approval actions"""
        # Create log in hotel_a
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False
        )
        
        # Try to approve from hotel_b context
        self.client.force_authenticate(user=self.user_manager_b)
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_b.slug}/clock-logs/{log.id}/approve/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BreakOvertimeAlertTestCase(MultiHotelSecurityTestCase):
    """Test break and overtime alert system"""
    
    def setUp(self):
        super().setUp()
        
        # Create attendance settings
        from hotel.models import AttendanceSettings
        self.attendance_settings_a = AttendanceSettings.objects.create(
            hotel=self.hotel_a,
            break_warning_hours=1.0,  # 1 hour for faster testing
            overtime_warning_hours=2.0,
            hard_limit_hours=3.0,
            enforce_limits=True
        )
    
    def test_check_open_log_alerts_sends_warnings(self):
        """Test that alert system sends appropriate warnings"""
        from django.utils.timezone import now
        from .utils import check_open_log_alerts_for_hotel
        
        # Create log that started 2.5 hours ago (should trigger break + overtime warnings)
        past_time = now() - timedelta(hours=2.5)
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_approved=True,
            is_rejected=False
        )
        log.time_in = past_time
        log.save()
        
        # Run alert check
        alerts_sent = check_open_log_alerts_for_hotel(self.hotel_a)
        
        self.assertEqual(alerts_sent['break_warnings'], 1)
        self.assertEqual(alerts_sent['overtime_warnings'], 1)
        self.assertEqual(alerts_sent['hard_limit_warnings'], 0)  # Not reached yet
        
        # Check flags were set
        log.refresh_from_db()
        self.assertTrue(log.break_warning_sent)
        self.assertTrue(log.overtime_warning_sent)
        self.assertFalse(log.hard_limit_warning_sent)
    
    def test_staff_can_acknowledge_hard_limit_and_stay(self):
        """Test staff acknowledgment of hard limit warning"""
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_approved=True,
            hard_limit_warning_sent=True
        )
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/{log.id}/stay-clocked-in/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'stay_acknowledged')
        
        # Check acknowledgment was recorded
        log.refresh_from_db()
        self.assertEqual(log.long_session_ack_mode, 'stay')
    
    def test_staff_can_force_clock_out_after_hard_limit(self):
        """Test staff choosing to clock out after hard limit warning"""
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_approved=True,
            hard_limit_warning_sent=True
        )
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/{log.id}/force-clock-out/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'clock_out_completed')
        
        # Check log was closed
        log.refresh_from_db()
        self.assertEqual(log.long_session_ack_mode, 'clocked_out')
        self.assertIsNotNone(log.time_out)
        
        # Check staff status updated
        self.staff_a.refresh_from_db()
        self.assertFalse(self.staff_a.is_on_duty)
    
    def test_alerts_not_sent_for_unapproved_logs(self):
        """Test that alerts are not sent for unapproved/rejected logs"""
        from django.utils.timezone import now
        from .utils import check_open_log_alerts_for_hotel
        
        # Create old log that is not approved
        past_time = now() - timedelta(hours=5)
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_approved=False,  # Not approved
            is_rejected=False
        )
        log.time_in = past_time
        log.save()
        
        # Run alert check
        alerts_sent = check_open_log_alerts_for_hotel(self.hotel_a)
        
        # No alerts should be sent for unapproved logs
        self.assertEqual(alerts_sent['break_warnings'], 0)
        self.assertEqual(alerts_sent['overtime_warnings'], 0)
        self.assertEqual(alerts_sent['hard_limit_warnings'], 0)


class PeriodFinalizationTestCase(MultiHotelSecurityTestCase):
    """Test roster period finalization system"""
    
    def setUp(self):
        super().setUp()
        
        self.period_a = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Test Week",
            start_date=date.today() - timedelta(days=7),
            end_date=date.today() - timedelta(days=1),
            created_by=self.manager_a,
            published=True
        )
    
    def test_finalize_period_succeeds_with_no_unresolved_logs(self):
        """Test successful period finalization when no unresolved logs exist"""
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/finalize/',
            {'confirm': True}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('finalized successfully', response.data['detail'])
        
        # Check period was finalized
        self.period_a.refresh_from_db()
        self.assertTrue(self.period_a.is_finalized)
        self.assertIsNotNone(self.period_a.finalized_at)
        self.assertEqual(self.period_a.finalized_by, self.manager_a)
    
    def test_finalize_period_fails_with_unresolved_logs(self):
        """Test finalization failure when unresolved unrostered logs exist"""
        # Create unresolved unrostered log within period
        log_date = self.period_a.start_date + timedelta(days=1)
        ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False
        )
        # Manually set time_in to be within period
        log = ClockLog.objects.latest('id')
        log.time_in = log.time_in.replace(
            year=log_date.year,
            month=log_date.month,
            day=log_date.day
        )
        log.save()
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/finalize/',
            {'confirm': True}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot finalize period', response.data['error'])
        self.assertIn('unresolved unrostered', response.data['error'])
    
    def test_admin_can_force_finalize_with_unresolved_logs(self):
        """Test admin force finalization with unresolved logs"""
        # Create unresolved log
        log_date = self.period_a.start_date + timedelta(days=1)
        ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False
        )
        log = ClockLog.objects.latest('id')
        log.time_in = log.time_in.replace(
            year=log_date.year,
            month=log_date.month,
            day=log_date.day
        )
        log.save()
        
        # Make user admin
        self.user_manager_a.is_staff = True
        self.user_manager_a.save()
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/finalize/',
            {'confirm': True, 'force': True}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check period was finalized despite unresolved logs
        self.period_a.refresh_from_db()
        self.assertTrue(self.period_a.is_finalized)
    
    def test_unfinalize_period_admin_only(self):
        """Test that only admins can unfinalize periods"""
        # Finalize first
        self.period_a.is_finalized = True
        self.period_a.finalized_by = self.manager_a
        self.period_a.save()
        
        # Try to unfinalize as regular manager (should fail)
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/unfinalize/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Make user admin and try again
        self.user_manager_a.is_staff = True
        self.user_manager_a.save()
        
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/unfinalize/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check period was unfinalized
        self.period_a.refresh_from_db()
        self.assertFalse(self.period_a.is_finalized)
        self.assertIsNone(self.period_a.finalized_by)
        self.assertIsNone(self.period_a.finalized_at)
    
    def test_finalization_status_endpoint(self):
        """Test finalization status check endpoint"""
        response = self.client.get(
            f'/api/attendance/{self.hotel_a.slug}/roster-periods/{self.period_a.id}/finalization-status/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_finalized'])
        self.assertTrue(response.data['can_finalize'])
        self.assertIsNone(response.data['validation_error'])
    
    def test_cannot_approve_logs_in_finalized_period(self):
        """Test that logs cannot be approved when period is finalized"""
        # Finalize period
        self.period_a.is_finalized = True
        self.period_a.save()
        
        # Create log within finalized period
        log_date = self.period_a.start_date + timedelta(days=1)
        log = ClockLog.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            is_unrostered=True,
            is_approved=False
        )
        log.time_in = log.time_in.replace(
            year=log_date.year,
            month=log_date.month,
            day=log_date.day
        )
        log.save()
        
        # Try to approve log
        response = self.client.post(
            f'/api/attendance/{self.hotel_a.slug}/clock-logs/{log.id}/approve/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('period is finalized', response.data['error'])


class AttendanceSettingsTestCase(MultiHotelSecurityTestCase):
    """Test attendance settings model and utilities"""
    
    def test_get_attendance_settings_creates_defaults(self):
        """Test that attendance settings are auto-created with defaults"""
        from .utils import get_attendance_settings
        
        settings = get_attendance_settings(self.hotel_a)
        
        self.assertIsNotNone(settings)
        self.assertEqual(settings.hotel, self.hotel_a)
        self.assertEqual(settings.break_warning_hours, 6.0)
        self.assertEqual(settings.overtime_warning_hours, 10.0)
        self.assertEqual(settings.hard_limit_hours, 12.0)
        self.assertTrue(settings.enforce_limits)
    
    def test_attendance_settings_hotel_isolation(self):
        """Test that attendance settings are isolated per hotel"""
        from hotel.models import AttendanceSettings
        
        # Create different settings for each hotel
        settings_a = AttendanceSettings.objects.create(
            hotel=self.hotel_a,
            break_warning_hours=4.0,
            overtime_warning_hours=8.0
        )
        
        settings_b = AttendanceSettings.objects.create(
            hotel=self.hotel_b,
            break_warning_hours=6.0,
            overtime_warning_hours=12.0
        )
        
        # Verify settings are isolated
        self.assertEqual(self.hotel_a.attendance_settings.break_warning_hours, 4.0)
        self.assertEqual(self.hotel_b.attendance_settings.break_warning_hours, 6.0)
        
        # Verify one-to-one relationship
        self.assertEqual(AttendanceSettings.objects.filter(hotel=self.hotel_a).count(), 1)
        self.assertEqual(AttendanceSettings.objects.filter(hotel=self.hotel_b).count(), 1)


# Run tests with: python manage.py test attendance.tests
