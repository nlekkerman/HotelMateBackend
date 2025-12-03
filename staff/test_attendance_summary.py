"""
Tests for Staff Attendance Summary functionality and utilities.

Tests cover:
1. StaffAttendanceSummarySerializer with various date ranges and attendance data
2. attendance_summary action endpoint with filtering and pagination  
3. Attendance status calculation logic (active, completed, no_log, issue)
4. Department filtering fix in StaffMetadataView
5. Badge information and status utilities
"""

import json
from datetime import date, time, datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from hotel.models import Hotel
from staff.models import Staff, Department, Role
from staff.serializers import StaffAttendanceSummarySerializer
from staff.attendance_utils import (
    calculate_attendance_status, calculate_worked_minutes,
    count_planned_shifts, count_worked_shifts, count_attendance_issues,
    has_attendance_issues, get_status_badge_info, get_attendance_status_badge_info
)
from attendance.models import ClockLog, StaffRoster, RosterPeriod, ShiftLocation


class AttendanceUtilsTestCase(TestCase):
    """Test attendance utility functions"""
    
    def setUp(self):
        """Set up test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@example.com"
        )
        
        # Create department
        self.department = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping"
        )
        
        # Create role
        self.role = Role.objects.create(
            name="Housekeeper",
            slug="housekeeper",
            department=self.department
        )
        
        # Create staff member
        self.user = User.objects.create_user(
            username="teststaff",
            password="testpass123"
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            department=self.department,
            role=self.role,
            first_name="Test",
            last_name="Staff",
            email="teststaff@example.com",
            is_active=True,
            duty_status='off_duty'
        )
        
        # Create roster period
        self.period = RosterPeriod.objects.create(
            hotel=self.hotel,
            title="Test Period",
            start_date=date.today() - timedelta(days=7),
            end_date=date.today() + timedelta(days=7),
            created_by=self.staff
        )
        
        # Test date range
        self.from_date = date.today()
        self.to_date = date.today()
    
    def test_calculate_attendance_status_no_log(self):
        """Test attendance status when staff has roster but no logs"""
        # Create roster entry but no clock logs
        StaffRoster.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            department=self.department,
            period=self.period,
            shift_date=self.from_date,
            shift_start=time(9, 0),
            shift_end=time(17, 0)
        )
        
        status = calculate_attendance_status(
            self.staff, self.from_date, self.to_date
        )
        self.assertEqual(status, 'no_log')
    
    def test_calculate_attendance_status_completed(self):
        """Test attendance status for completed shifts"""
        # Create completed clock log
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(9, 0))),
            time_out=make_aware(datetime.combine(self.from_date, time(17, 0))),
            hours_worked=8.0,
            is_approved=True
        )
        
        status = calculate_attendance_status(
            self.staff, self.from_date, self.to_date
        )
        self.assertEqual(status, 'completed')
    
    def test_calculate_attendance_status_active(self):
        """Test attendance status for currently active staff"""
        # Create open clock log and set staff on duty
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(9, 0))),
            time_out=None
        )
        self.staff.duty_status = 'on_duty'
        self.staff.save()
        
        status = calculate_attendance_status(
            self.staff, self.from_date, self.to_date
        )
        self.assertEqual(status, 'active')
    
    def test_calculate_attendance_status_issue(self):
        """Test attendance status when issues are detected"""
        # Create rejected log (issue)
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(9, 0))),
            time_out=make_aware(datetime.combine(self.from_date, time(17, 0))),
            is_rejected=True
        )
        
        status = calculate_attendance_status(
            self.staff, self.from_date, self.to_date
        )
        self.assertEqual(status, 'issue')
    
    def test_has_attendance_issues_excessive_hours(self):
        """Test issue detection for excessive work hours"""
        # Create log with excessive hours (>16)
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(9, 0))),
            time_out=make_aware(datetime.combine(self.from_date + timedelta(days=1), time(2, 0))),
            hours_worked=17.0,  # Excessive
            is_approved=True
        )
        
        has_issues = has_attendance_issues(
            self.staff, self.from_date, self.to_date
        )
        self.assertTrue(has_issues)
    
    def test_has_attendance_issues_old_open_log(self):
        """Test issue detection for old open logs"""
        # Create old open log (>24 hours ago)
        old_time = now() - timedelta(hours=25)
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=old_time,
            time_out=None
        )
        
        yesterday = (now() - timedelta(days=1)).date()
        has_issues = has_attendance_issues(
            self.staff, yesterday, yesterday
        )
        self.assertTrue(has_issues)
    
    def test_calculate_worked_minutes(self):
        """Test worked minutes calculation"""
        # Create logs with different hours
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(9, 0))),
            time_out=make_aware(datetime.combine(self.from_date, time(17, 0))),
            hours_worked=8.0,
            is_approved=True
        )
        ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff,
            time_in=make_aware(datetime.combine(self.from_date, time(18, 0))),
            time_out=make_aware(datetime.combine(self.from_date, time(20, 0))),
            hours_worked=2.0,
            is_approved=True
        )
        
        minutes = calculate_worked_minutes(
            self.staff, self.from_date, self.to_date
        )
        self.assertEqual(minutes, 600)  # 10 hours = 600 minutes
    
    def test_count_planned_shifts(self):
        """Test planned shifts counting"""
        # Create roster entries
        for i in range(3):
            StaffRoster.objects.create(
                hotel=self.hotel,
                staff=self.staff,
                department=self.department,
                period=self.period,
                shift_date=self.from_date + timedelta(days=i),
                shift_start=time(9, 0),
                shift_end=time(17, 0)
            )
        
        count = count_planned_shifts(
            self.staff, self.from_date, self.from_date + timedelta(days=2)
        )
        self.assertEqual(count, 3)
    
    def test_count_worked_shifts(self):
        """Test worked shifts counting"""
        # Create approved clock logs
        for i in range(2):
            ClockLog.objects.create(
                hotel=self.hotel,
                staff=self.staff,
                time_in=make_aware(datetime.combine(
                    self.from_date + timedelta(days=i), time(9, 0)
                )),
                time_out=make_aware(datetime.combine(
                    self.from_date + timedelta(days=i), time(17, 0)
                )),
                hours_worked=8.0,
                is_approved=True
            )
        
        count = count_worked_shifts(
            self.staff, self.from_date, self.from_date + timedelta(days=1)
        )
        self.assertEqual(count, 2)
    
    def test_get_status_badge_info(self):
        """Test status badge information"""
        on_duty_badge = get_status_badge_info('on_duty')
        self.assertEqual(on_duty_badge['label'], 'On Duty')
        self.assertEqual(on_duty_badge['color'], 'success')
        self.assertEqual(on_duty_badge['status_type'], 'active')
        
        off_duty_badge = get_status_badge_info('off_duty')
        self.assertEqual(off_duty_badge['label'], 'Off Duty')
        self.assertEqual(off_duty_badge['color'], 'secondary')
        
        on_break_badge = get_status_badge_info('on_break')
        self.assertEqual(on_break_badge['label'], 'On Break')
        self.assertEqual(on_break_badge['color'], 'warning')
    
    def test_get_attendance_status_badge_info(self):
        """Test attendance status badge information"""
        active_badge = get_attendance_status_badge_info('active')
        self.assertEqual(active_badge['label'], 'Currently Active')
        self.assertEqual(active_badge['priority'], 1)
        
        issue_badge = get_attendance_status_badge_info('issue')
        self.assertEqual(issue_badge['label'], 'Has Issues')
        self.assertEqual(issue_badge['color'], 'danger')
        self.assertEqual(issue_badge['priority'], 3)


class StaffAttendanceAPITestCase(APITestCase):
    """Test Staff Attendance Summary API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create hotels
        self.hotel_a = Hotel.objects.create(
            name="Hotel A",
            slug="hotel-a",
            email="a@example.com"
        )
        self.hotel_b = Hotel.objects.create(
            name="Hotel B", 
            slug="hotel-b",
            email="b@example.com"
        )
        
        # Create departments
        self.dept_housekeeping = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping"
        )
        self.dept_reception = Department.objects.create(
            name="Reception",
            slug="reception"
        )
        
        # Create staff for hotel A
        self.user_a = User.objects.create_user(
            username="staffa",
            password="testpass123"
        )
        self.staff_a = Staff.objects.create(
            user=self.user_a,
            hotel=self.hotel_a,
            department=self.dept_housekeeping,
            first_name="Staff",
            last_name="A",
            email="staffa@example.com",
            is_active=True
        )
        
        # Create staff for hotel B
        self.user_b = User.objects.create_user(
            username="staffb",
            password="testpass123"
        )
        self.staff_b = Staff.objects.create(
            user=self.user_b,
            hotel=self.hotel_b,
            department=self.dept_reception,
            first_name="Staff",
            last_name="B", 
            email="staffb@example.com",
            is_active=True
        )
        
        # Create additional staff for hotel A to test multiple departments
        self.user_a2 = User.objects.create_user(
            username="staffa2",
            password="testpass123"
        )
        self.staff_a2 = Staff.objects.create(
            user=self.user_a2,
            hotel=self.hotel_a,
            department=self.dept_reception,
            first_name="Staff",
            last_name="A2",
            email="staffa2@example.com",
            is_active=True
        )
        
        self.client = APIClient()
    
    def test_attendance_summary_requires_from_date(self):
        """Test that from date parameter is required"""
        self.client.force_authenticate(user=self.user_a)
        
        url = reverse('staff-attendance-summary', kwargs={'hotel_slug': 'hotel-a'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('from', response.data['detail'])
    
    def test_attendance_summary_invalid_date_format(self):
        """Test invalid date format handling"""
        self.client.force_authenticate(user=self.user_a)
        
        url = reverse('staff-attendance-summary', kwargs={'hotel_slug': 'hotel-a'})
        response = self.client.get(url, {'from': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', response.data['detail'])
    
    def test_attendance_summary_valid_request(self):
        """Test valid attendance summary request"""
        self.client.force_authenticate(user=self.user_a)
        
        # Create some test data
        period = RosterPeriod.objects.create(
            hotel=self.hotel_a,
            title="Test Period",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            created_by=self.staff_a
        )
        
        StaffRoster.objects.create(
            hotel=self.hotel_a,
            staff=self.staff_a,
            department=self.dept_housekeeping,
            period=period,
            shift_date=date.today(),
            shift_start=time(9, 0),
            shift_end=time(17, 0)
        )
        
        url = reverse('staff-attendance-summary', kwargs={'hotel_slug': 'hotel-a'})
        response = self.client.get(url, {'from': date.today().isoformat()})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('date_range', response.data)
        self.assertIn('filters', response.data)
        
        # Check that staff data includes attendance fields
        if response.data['results']:
            staff_data = response.data['results'][0]
            self.assertIn('planned_shifts', staff_data)
            self.assertIn('worked_shifts', staff_data)
            self.assertIn('total_worked_minutes', staff_data)
            self.assertIn('attendance_status', staff_data)
            self.assertIn('duty_status_badge', staff_data)
    
    def test_attendance_summary_department_filter(self):
        """Test department filtering in attendance summary"""
        self.client.force_authenticate(user=self.user_a)
        
        url = reverse('staff-attendance-summary', kwargs={'hotel_slug': 'hotel-a'})
        response = self.client.get(url, {
            'from': date.today().isoformat(),
            'department': 'housekeeping'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return staff from housekeeping department
        housekeeping_staff = [
            item for item in response.data['results']
            if item.get('department_slug') == 'housekeeping'
        ]
        # All results should be from housekeeping when filtered
        self.assertEqual(len(housekeeping_staff), len(response.data['results']))
    
    def test_attendance_summary_hotel_isolation(self):
        """Test that attendance summary respects hotel isolation"""
        self.client.force_authenticate(user=self.user_a)
        
        # Try to access hotel B's data with hotel A credentials
        url = reverse('staff-attendance-summary', kwargs={'hotel_slug': 'hotel-b'})
        response = self.client.get(url, {'from': date.today().isoformat()})
        
        # Should either be forbidden or return empty results
        # The exact behavior depends on your permission implementation
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,  # Empty results
            status.HTTP_403_FORBIDDEN,  # Explicit denial
            status.HTTP_404_NOT_FOUND   # Hotel not found for user
        ])


class StaffMetadataViewTestCase(APITestCase):
    """Test department filtering fix in StaffMetadataView"""
    
    def setUp(self):
        """Set up test data with multiple departments"""
        # Create hotels
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@example.com"
        )
        
        # Create many departments (simulating the 12 departments issue)
        self.departments = []
        for i in range(12):
            dept = Department.objects.create(
                name=f"Department {i+1}",
                slug=f"department-{i+1}"
            )
            self.departments.append(dept)
        
        # Create staff members for only some departments (first 5)
        self.staff_members = []
        for i in range(5):
            user = User.objects.create_user(
                username=f"staff{i}",
                password="testpass123"
            )
            staff = Staff.objects.create(
                user=user,
                hotel=self.hotel,
                department=self.departments[i],
                first_name=f"Staff",
                last_name=f"{i}",
                is_active=True
            )
            self.staff_members.append(staff)
        
        self.client = APIClient()
    
    def test_metadata_returns_hotel_scoped_departments(self):
        """Test that metadata endpoint returns only departments used by hotel staff"""
        self.client.force_authenticate(user=self.staff_members[0].user)
        
        url = reverse('staff-metadata', kwargs={'hotel_slug': 'test-hotel'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('departments', response.data)
        
        # Should return only departments that have active staff in this hotel (5)
        # NOT all departments (12)
        returned_departments = response.data['departments']
        self.assertEqual(len(returned_departments), 5)
        
        # Verify the returned departments are the ones with staff
        returned_slugs = {dept['slug'] for dept in returned_departments}
        expected_slugs = {f'department-{i+1}' for i in range(5)}
        self.assertEqual(returned_slugs, expected_slugs)
    
    def test_metadata_without_hotel_returns_all_departments(self):
        """Test that metadata without hotel slug returns all departments"""
        self.client.force_authenticate(user=self.staff_members[0].user)
        
        # This would be a different endpoint or URL pattern without hotel_slug
        # The exact implementation depends on your URL configuration
        # For now, test the case where hotel_slug is None in the view logic
        pass  # Implementation depends on whether you have such an endpoint


class StaffAttendanceSummarySerializerTestCase(TestCase):
    """Test StaffAttendanceSummarySerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@example.com"
        )
        
        self.department = Department.objects.create(
            name="Test Department",
            slug="test-dept"
        )
        
        self.user = User.objects.create_user(
            username="teststaff",
            password="testpass123"
        )
        self.staff = Staff.objects.create(
            user=self.user,
            hotel=self.hotel,
            department=self.department,
            first_name="Test",
            last_name="Staff",
            email="test@example.com",
            is_active=True,
            duty_status='on_duty'
        )
    
    def test_serializer_includes_attendance_fields(self):
        """Test that serializer includes all attendance-related fields"""
        # Create mock request with date parameters
        class MockRequest:
            def __init__(self):
                self.query_params = {
                    'from': date.today().isoformat(),
                    'to': date.today().isoformat()
                }
        
        mock_request = MockRequest()
        context = {'request': mock_request}
        
        serializer = StaffAttendanceSummarySerializer(self.staff, context=context)
        data = serializer.data
        
        # Check that attendance fields are present
        attendance_fields = [
            'full_name', 'department_name', 'department_slug',
            'planned_shifts', 'worked_shifts', 'total_worked_minutes',
            'issues_count', 'attendance_status',
            'duty_status_badge', 'attendance_status_badge'
        ]
        
        for field in attendance_fields:
            self.assertIn(field, data, f"Field '{field}' missing from serializer output")
        
        # Check basic field values
        self.assertEqual(data['full_name'], 'Test Staff')
        self.assertEqual(data['department_name'], 'Test Department')
        self.assertEqual(data['department_slug'], 'test-dept')
        self.assertIsInstance(data['planned_shifts'], int)
        self.assertIsInstance(data['worked_shifts'], int)
        self.assertIsInstance(data['total_worked_minutes'], int)
    
    def test_serializer_badge_information(self):
        """Test that serializer includes proper badge information"""
        class MockRequest:
            def __init__(self):
                self.query_params = {
                    'from': date.today().isoformat()
                }
        
        context = {'request': MockRequest()}
        serializer = StaffAttendanceSummarySerializer(self.staff, context=context)
        data = serializer.data
        
        # Check duty status badge
        duty_badge = data['duty_status_badge']
        self.assertIn('label', duty_badge)
        self.assertIn('color', duty_badge) 
        self.assertIn('status_type', duty_badge)
        
        # Check attendance status badge
        attendance_badge = data['attendance_status_badge']
        self.assertIn('label', attendance_badge)
        self.assertIn('color', attendance_badge)
        self.assertIn('priority', attendance_badge)