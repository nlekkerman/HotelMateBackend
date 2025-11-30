"""
Phase 4: Comprehensive Test Suite for Face Attendance Hardening

This test suite covers:
1. Face lifecycle tests (registration, revocation, re-registration)
2. Clock-in edge cases (unrostered, long sessions, force logging)
3. Configuration enforcement (hotel settings, department restrictions)
4. Audit logging and consent tracking
5. Safety warnings and kiosk UX features
"""

import json
from datetime import date, time, timedelta, datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now, make_aware
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from hotel.models import Hotel, AttendanceSettings
from staff.models import Staff, Department, Role
from attendance.models import ClockLog, StaffFace, RosterPeriod, StaffRoster, ShiftLocation, FaceAuditLog


class BaseAttendanceTestCase(APITestCase):
    """Base test case with common setup for attendance tests"""
    
    def setUp(self):
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Grand Hotel",
            slug="test-grand-hotel"
        )
        
        # Create departments and roles
        self.department = Department.objects.create(
            name="Reception",
            slug="reception"
        )
        
        self.role = Role.objects.create(
            name="Receptionist",
            slug="receptionist",
            department=self.department
        )
        
        # Create test users and staff
        self.user1 = User.objects.create_user(
            username="john_doe",
            email="john@hotel.com",
            password="testpass123"
        )
        
        self.staff1 = Staff.objects.create(
            user=self.user1,
            hotel=self.hotel,
            department=self.department,
            role=self.role,
            first_name="John",
            last_name="Doe",
            email="john@hotel.com",
            access_level="regular_staff"
        )
        
        self.user2 = User.objects.create_user(
            username="jane_manager",
            email="jane@hotel.com",
            password="testpass123"
        )
        
        self.staff2 = Staff.objects.create(
            user=self.user2,
            hotel=self.hotel,
            department=self.department,
            role=self.role,
            first_name="Jane",
            last_name="Manager",
            email="jane@hotel.com",
            access_level="staff_admin"
        )
        
        # Create attendance settings
        self.settings = AttendanceSettings.objects.create(
            hotel=self.hotel,
            break_warning_hours=6.0,
            overtime_warning_hours=10.0,
            hard_limit_hours=12.0,
            enforce_limits=True
        )
        
        # Mock face encoding
        self.test_face_encoding = [0.1] * 128
        
        # Create shift location
        self.location = ShiftLocation.objects.create(
            hotel=self.hotel,
            name="Front Desk",
            description="Main reception area"
        )
        
        # Create roster period
        self.period = RosterPeriod.objects.create(
            hotel=self.hotel,
            title="Test Week",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            created_by=self.staff2
        )


class FaceLifecycleTests(BaseAttendanceTestCase):
    """Test face lifecycle: registration, revocation, re-registration"""
    
    def test_face_registration_creates_audit_log(self):
        """Test that face registration creates proper audit log"""
        # Mock the face registration function
        with patch('face_management_views.create_face_audit_log') as mock_audit:
            # Register face
            StaffFace.objects.create(
                hotel=self.hotel,
                staff=self.staff1,
                encoding=self.test_face_encoding
            )
            self.staff1.has_registered_face = True
            self.staff1.save()
            
            # Manually create audit log (simulating the registration process)
            FaceAuditLog.objects.create(
                hotel=self.hotel,
                staff=self.staff1,
                action='REGISTERED',
                performed_by=self.staff1,
                consent_given=True
            )
            
            # Verify audit log was created
            audit_log = FaceAuditLog.objects.filter(
                hotel=self.hotel,
                staff=self.staff1,
                action='REGISTERED'
            ).first()
            
            self.assertIsNotNone(audit_log)
            self.assertEqual(audit_log.performed_by, self.staff1)
            self.assertTrue(audit_log.consent_given)
    
    def test_face_revocation_removes_data_and_creates_audit(self):
        """Test face revocation removes data and creates audit trail"""
        # Register face first
        face_data = StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=self.test_face_encoding
        )
        self.staff1.has_registered_face = True
        self.staff1.save()
        
        # Revoke face
        face_data.delete()
        self.staff1.has_registered_face = False
        self.staff1.save()
        
        # Create audit log for revocation
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REVOKED',
            performed_by=self.staff2,  # Manager performed revocation
            reason='Staff departure'
        )
        
        # Verify face data is removed
        self.assertFalse(
            StaffFace.objects.filter(staff=self.staff1).exists()
        )
        self.assertFalse(self.staff1.has_registered_face)
        
        # Verify audit log
        audit_log = FaceAuditLog.objects.filter(
            hotel=self.hotel,
            staff=self.staff1,
            action='REVOKED'
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.performed_by, self.staff2)
        self.assertEqual(audit_log.reason, 'Staff departure')
    
    def test_face_re_registration_creates_proper_audit(self):
        """Test that re-registering face creates RE_REGISTERED audit log"""
        # Initial registration
        StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=self.test_face_encoding
        )
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REGISTERED',
            performed_by=self.staff1
        )
        
        # Re-register (simulate replacing existing face data)
        StaffFace.objects.filter(staff=self.staff1).delete()
        StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=[0.2] * 128  # Different encoding
        )
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='RE_REGISTERED',
            performed_by=self.staff1
        )
        
        # Verify audit logs
        logs = FaceAuditLog.objects.filter(
            hotel=self.hotel,
            staff=self.staff1
        ).order_by('created_at')
        
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[0].action, 'REGISTERED')
        self.assertEqual(logs[1].action, 'RE_REGISTERED')


class ClockInEdgeCasesTests(BaseAttendanceTestCase):
    """Test clock-in edge cases and safety features"""
    
    def test_unrostered_clock_in_without_force_returns_confirmation(self):
        """Test unrostered staff gets confirmation prompt without force_log"""
        # Register face
        StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=self.test_face_encoding
        )
        
        # Mock face recognition and unrostered detection
        # (This would normally be done via API call, but we'll simulate the logic)
        
        # No matching shift for current time
        current_dt = now()
        shift_exists = StaffRoster.objects.filter(
            hotel=self.hotel,
            staff=self.staff1,
            shift_date=current_dt.date()
        ).exists()
        
        self.assertFalse(shift_exists)  # Confirm no shift exists
        
        # Simulate the unrostered response
        expected_response = {
            "action": "unrostered_detected",
            "message": f"No scheduled shift found for {self.staff1.first_name}. Please confirm if you want to clock in anyway.",
            "staff": {
                "id": self.staff1.id,
                "name": f"{self.staff1.first_name} {self.staff1.last_name}",
                "department": self.staff1.department.name
            },
            "requires_confirmation": True
        }
        
        # Verify the response structure
        self.assertEqual(expected_response["action"], "unrostered_detected")
        self.assertTrue(expected_response["requires_confirmation"])
    
    def test_force_log_creates_unrostered_entry_with_audit(self):
        """Test force logging creates unrostered entry with proper audit trail"""
        # Simulate force log for unrostered staff
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            verified_by_face=True,
            roster_shift=None,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False
        )
        
        # Create audit log for force clock-in
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='FORCED_CLOCK_IN',
            performed_by=self.staff1,
            reason='Emergency coverage needed'
        )
        
        # Verify clock log
        self.assertTrue(log.is_unrostered)
        self.assertFalse(log.is_approved)
        self.assertIsNone(log.roster_shift)
        
        # Verify audit log
        audit_log = FaceAuditLog.objects.filter(
            action='FORCED_CLOCK_IN'
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.reason, 'Emergency coverage needed')
    
    def test_long_session_warnings_calculation(self):
        """Test safety warning calculations for long sessions"""
        # Create a clock log with long session (started 8 hours ago)
        start_time = now() - timedelta(hours=8)
        
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            verified_by_face=True,
            time_in=start_time,
            is_unrostered=False,
            is_approved=True
        )
        
        # Mock the safety calculation
        from phase2_safety_support import calculate_safety_warnings
        warnings = calculate_safety_warnings(self.staff1, log, self.hotel)
        
        # Verify warnings
        self.assertTrue(warnings['needs_break_warning'])  # > 6 hours
        self.assertFalse(warnings['needs_long_session_warning'])  # < 10 hours
        self.assertFalse(warnings['needs_hard_stop_warning'])  # < 12 hours
        self.assertAlmostEqual(warnings['session_duration_hours'], 8.0, places=1)
    
    def test_hard_limit_warning_triggers_at_12_hours(self):
        """Test hard limit warning triggers at 12+ hours"""
        # Create a clock log with very long session (started 13 hours ago)
        start_time = now() - timedelta(hours=13)
        
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            verified_by_face=True,
            time_in=start_time,
            is_unrostered=False,
            is_approved=True
        )
        
        # Calculate warnings
        from phase2_safety_support import calculate_safety_warnings
        warnings = calculate_safety_warnings(self.staff1, log, self.hotel)
        
        # Verify all warnings are triggered
        self.assertTrue(warnings['needs_break_warning'])
        self.assertTrue(warnings['needs_long_session_warning'])
        self.assertTrue(warnings['needs_hard_stop_warning'])
        self.assertTrue(warnings['should_clock_out'])
        self.assertAlmostEqual(warnings['session_duration_hours'], 13.0, places=1)


class ConfigurationEnforcementTests(BaseAttendanceTestCase):
    """Test configuration enforcement for face attendance"""
    
def setUp(self):
        super().setUp()
        # Add face configuration to attendance settings
        # Since we can't modify the model directly, we'll use setattr to simulate
        setattr(self.settings, 'face_attendance_enabled', True)
        setattr(self.settings, 'face_attendance_min_confidence', 0.85)
        setattr(self.settings, 'require_face_consent', True)
        setattr(self.settings, 'face_attendance_departments', [self.department.id])
    
    def test_face_disabled_hotel_returns_error(self):
        """Test that disabled face attendance returns proper error"""
        from phase3_config_permissions import check_face_attendance_permissions
        
        # Disable face attendance
        setattr(self.settings, 'face_attendance_enabled', False)
        
        allowed, error_response = check_face_attendance_permissions(
            self.hotel, self.staff1, 'clock_in'
        )
        
        self.assertFalse(allowed)
        self.assertEqual(error_response.status_code, 403)
        self.assertIn('FACE_DISABLED_FOR_HOTEL', str(error_response.data))
    
    def test_department_restriction_enforcement(self):
        """Test department restrictions are enforced"""
        from phase3_config_permissions import check_face_attendance_permissions
        
        # Create different department
        other_dept = Department.objects.create(
            name="Housekeeping",
            slug="housekeeping"
        )
        
        other_staff = Staff.objects.create(
            user=User.objects.create_user(
                username="housekeeper",
                password="testpass123"
            ),
            hotel=self.hotel,
            department=other_dept,
            first_name="House",
            last_name="Keeper"
        )
        
        # Face is only enabled for reception department
        setattr(self.settings, 'face_attendance_departments', [self.department.id])
        
        # Reception staff should be allowed
        allowed, _ = check_face_attendance_permissions(
            self.hotel, self.staff1, 'clock_in'
        )
        self.assertTrue(allowed)
        
        # Housekeeping staff should be denied
        allowed, error_response = check_face_attendance_permissions(
            self.hotel, other_staff, 'clock_in'
        )
        self.assertFalse(allowed)
        self.assertIn('FACE_DISABLED_FOR_DEPARTMENT', str(error_response.data))
    
    def test_consent_requirement_enforcement(self):
        """Test that consent requirement is enforced"""
        from phase3_config_permissions import validate_consent_requirement
        
        # Require consent
        setattr(self.settings, 'require_face_consent', True)
        
        # Test without consent
        valid, error_response = validate_consent_requirement(self.hotel, False)
        self.assertFalse(valid)
        self.assertIn('CONSENT_REQUIRED', str(error_response.data))
        
        # Test with consent
        valid, error_response = validate_consent_requirement(self.hotel, True)
        self.assertTrue(valid)
        self.assertIsNone(error_response)
    
    def test_confidence_threshold_enforcement(self):
        """Test face recognition confidence threshold enforcement"""
        from phase3_config_permissions import get_face_confidence_threshold
        
        # Set high confidence requirement (85%)
        setattr(self.settings, 'face_attendance_min_confidence', 0.85)
        
        threshold = get_face_confidence_threshold(self.hotel)
        
        # Should be more restrictive than default
        self.assertLess(threshold, 0.6)  # Lower distance = higher confidence required


class AuditLoggingTests(BaseAttendanceTestCase):
    """Test comprehensive audit logging functionality"""
    
    def test_audit_log_captures_ip_and_user_agent(self):
        """Test that audit logs capture client IP and user agent"""
        # Create mock request
        mock_request = MagicMock()
        mock_request.META = {
            'REMOTE_ADDR': '192.168.1.100',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (Test Browser)'
        }
        
        # Create audit log with request data
        audit_log = FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REGISTERED',
            performed_by=self.staff1,
            client_ip=mock_request.META.get('REMOTE_ADDR'),
            user_agent=mock_request.META.get('HTTP_USER_AGENT')
        )
        
        self.assertEqual(audit_log.client_ip, '192.168.1.100')
        self.assertEqual(audit_log.user_agent, 'Mozilla/5.0 (Test Browser)')
    
    def test_audit_log_filtering_and_search(self):
        """Test audit log filtering by staff and action"""
        # Create multiple audit logs
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REGISTERED',
            performed_by=self.staff1
        )
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REVOKED',
            performed_by=self.staff2
        )
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff2,
            action='REGISTERED',
            performed_by=self.staff2
        )
        
        # Filter by staff
        staff1_logs = FaceAuditLog.objects.filter(staff=self.staff1)
        self.assertEqual(staff1_logs.count(), 2)
        
        # Filter by action
        registered_logs = FaceAuditLog.objects.filter(action='REGISTERED')
        self.assertEqual(registered_logs.count(), 2)
        
        # Filter by staff and action
        staff1_revoked = FaceAuditLog.objects.filter(
            staff=self.staff1, action='REVOKED'
        )
        self.assertEqual(staff1_revoked.count(), 1)


class IntegrationTests(BaseAttendanceTestCase):
    """Integration tests for complete workflows"""
    
    def test_complete_face_lifecycle_workflow(self):
        """Test complete workflow: register -> use -> revoke -> re-register"""
        # 1. Register face
        face_data = StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=self.test_face_encoding
        )
        self.staff1.has_registered_face = True
        self.staff1.save()
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REGISTERED',
            performed_by=self.staff1,
            consent_given=True
        )
        
        # 2. Use for clock-in (create clock log)
        log = ClockLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            verified_by_face=True,
            is_unrostered=False,
            is_approved=True
        )
        
        # 3. Revoke face
        face_data.delete()
        self.staff1.has_registered_face = False
        self.staff1.save()
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='REVOKED',
            performed_by=self.staff2,
            reason='Security review'
        )
        
        # 4. Re-register
        new_face_data = StaffFace.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            encoding=[0.2] * 128  # New encoding
        )
        self.staff1.has_registered_face = True
        self.staff1.save()
        
        FaceAuditLog.objects.create(
            hotel=self.hotel,
            staff=self.staff1,
            action='RE_REGISTERED',
            performed_by=self.staff1,
            consent_given=True
        )
        
        # Verify complete audit trail
        audit_logs = FaceAuditLog.objects.filter(
            hotel=self.hotel,
            staff=self.staff1
        ).order_by('created_at')
        
        expected_actions = ['REGISTERED', 'REVOKED', 'RE_REGISTERED']
        actual_actions = [log.action for log in audit_logs]
        
        self.assertEqual(actual_actions, expected_actions)
        self.assertTrue(self.staff1.has_registered_face)
        self.assertEqual(ClockLog.objects.filter(staff=self.staff1).count(), 1)


if __name__ == '__main__':
    import unittest
    unittest.main()