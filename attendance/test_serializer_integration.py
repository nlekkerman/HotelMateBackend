#!/usr/bin/env python
"""
Integration tests for ClockLogSerializer with roster_shift fields.
Focused tests for serializer functionality.
"""

import unittest
from unittest.mock import Mock, patch
from attendance.serializers import ClockLogSerializer
from datetime import date, time


class ClockLogSerializerIntegrationTests(unittest.TestCase):
    """Test ClockLogSerializer with roster_shift functionality"""

    def setUp(self):
        """Set up mock objects for testing"""
        # Mock hotel
        self.mock_hotel = Mock()
        self.mock_hotel.id = 1
        self.mock_hotel.slug = 'test-hotel'
        
        # Mock department
        self.mock_department = Mock()
        self.mock_department.name = 'Housekeeping'
        self.mock_department.slug = 'housekeeping'
        
        # Mock staff
        self.mock_staff = Mock()
        self.mock_staff.id = 1
        self.mock_staff.first_name = 'Test'
        self.mock_staff.last_name = 'Staff'
        self.mock_staff.department = self.mock_department
        
        # Mock location
        self.mock_location = Mock()
        self.mock_location.name = 'Main Reception'
        
        # Mock roster shift
        self.mock_shift = Mock()
        self.mock_shift.id = 1
        self.mock_shift.shift_date = date(2025, 1, 1)
        self.mock_shift.shift_start = time(9, 0)
        self.mock_shift.shift_end = time(17, 0)
        self.mock_shift.location = self.mock_location
        self.mock_shift.department = self.mock_department
        
        # Mock clock log
        self.mock_log = Mock()
        self.mock_log.id = 1
        self.mock_log.hotel = self.mock_hotel
        self.mock_log.staff = self.mock_staff
        self.mock_log.roster_shift = self.mock_shift
        self.mock_log.hours_worked = 8.0

    def test_serializer_fields_include_roster_shift(self):
        """Test that serializer includes roster_shift fields"""
        fields = ClockLogSerializer.Meta.fields
        
        # Check that both input and output fields are present
        self.assertIn('roster_shift_id', fields)
        self.assertIn('roster_shift', fields)
        self.assertIn('hours_worked', fields)

    def test_get_roster_shift_with_linked_shift(self):
        """Test get_roster_shift method when shift is linked"""
        serializer = ClockLogSerializer()
        result = serializer.get_roster_shift(self.mock_log)
        
        expected = {
            "id": 1,
            "date": date(2025, 1, 1),
            "start": time(9, 0),
            "end": time(17, 0),
            "location": "Main Reception",
            "department": "Housekeeping",
        }
        
        self.assertEqual(result, expected)

    def test_get_roster_shift_without_linked_shift(self):
        """Test get_roster_shift method when no shift is linked"""
        self.mock_log.roster_shift = None
        
        serializer = ClockLogSerializer()
        result = serializer.get_roster_shift(self.mock_log)
        
        self.assertIsNone(result)

    def test_get_roster_shift_with_missing_location(self):
        """Test get_roster_shift method when shift has no location"""
        self.mock_shift.location = None
        
        serializer = ClockLogSerializer()
        result = serializer.get_roster_shift(self.mock_log)
        
        self.assertIsNone(result['location'])
        self.assertEqual(result['department'], 'Housekeeping')

    def test_get_department_method(self):
        """Test get_department method returns correct structure"""
        serializer = ClockLogSerializer()
        result = serializer.get_department(self.mock_log)
        
        expected = {
            'name': 'Housekeeping',
            'slug': 'housekeeping',
        }
        
        self.assertEqual(result, expected)

    def test_get_department_no_department(self):
        """Test get_department when staff has no department"""
        self.mock_staff.department = None
        
        serializer = ClockLogSerializer()
        result = serializer.get_department(self.mock_log)
        
        expected = {'name': 'N/A', 'slug': None}
        self.assertEqual(result, expected)

    def test_get_staff_name_method(self):
        """Test get_staff_name method"""
        serializer = ClockLogSerializer()
        result = serializer.get_staff_name(self.mock_log)
        
        self.assertEqual(result, 'Test Staff')

    @patch('attendance.serializers.StaffRoster')
    def test_roster_shift_id_queryset_filtering(self, mock_roster_model):
        """Test that roster_shift_id field uses correct queryset"""
        # Access the field to trigger queryset evaluation
        serializer = ClockLogSerializer()
        roster_shift_field = serializer.fields['roster_shift_id']
        
        # Verify it's configured correctly
        self.assertTrue(roster_shift_field.write_only)
        self.assertTrue(roster_shift_field.allow_null)
        self.assertFalse(roster_shift_field.required)
        self.assertEqual(roster_shift_field.source, 'roster_shift')


if __name__ == '__main__':
    unittest.main()