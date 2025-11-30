#!/usr/bin/env python
"""
Core logic tests for shift matching functionality.
Tests the find_matching_shift_for_datetime function with mock data.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date, time, timedelta
from django.utils.timezone import make_aware

# Import the function we're testing
from attendance.views import find_matching_shift_for_datetime


class ShiftMatchingLogicTests(unittest.TestCase):
    """Test the core shift matching logic"""

    def setUp(self):
        """Set up mock objects"""
        self.mock_hotel = Mock()
        self.mock_hotel.id = 1
        
        self.mock_staff = Mock()
        self.mock_staff.id = 1

    def create_mock_shift(self, shift_id, shift_date, start_time, end_time):
        """Helper to create mock shift objects"""
        shift = Mock()
        shift.id = shift_id
        shift.shift_date = shift_date
        shift.shift_start = start_time
        shift.shift_end = end_time
        return shift

    @patch('attendance.views.StaffRoster')
    def test_normal_shift_matching(self, mock_roster_model):
        """Test matching within normal shift hours"""
        # Create mock shift: 09:00-17:00 on Jan 1
        mock_shift = self.create_mock_shift(
            1, date(2025, 1, 1), time(9, 0), time(17, 0)
        )
        
        # Mock queryset
        mock_queryset = Mock()
        mock_queryset.filter.return_value = [mock_shift]
        mock_roster_model.objects = mock_queryset
        
        # Test clock-in at 10:00 on Jan 1 (within shift)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        # Should find the matching shift
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        
        # Verify filter was called with correct parameters
        mock_queryset.filter.assert_called_once()
        call_args = mock_queryset.filter.call_args[1]
        self.assertEqual(call_args['hotel'], self.mock_hotel)
        self.assertEqual(call_args['staff'], self.mock_staff)
        self.assertIn(date(2025, 1, 1), call_args['shift_date__in'])
        self.assertIn(date(2024, 12, 31), call_args['shift_date__in'])  # Yesterday for overnight

    @patch('attendance.views.StaffRoster')
    def test_overnight_shift_matching(self, mock_roster_model):
        """Test matching within overnight shift hours"""
        # Create mock overnight shift: 22:00-02:00 on Jan 1
        mock_shift = self.create_mock_shift(
            1, date(2025, 1, 1), time(22, 0), time(2, 0)
        )
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = [mock_shift]
        mock_roster_model.objects = mock_queryset
        
        # Test clock-in at 01:00 on Jan 2 (within overnight shift)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 2), time(1, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        # Should find the matching overnight shift
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    @patch('attendance.views.StaffRoster')
    def test_no_matching_shift(self, mock_roster_model):
        """Test when no shift matches the clock-in time"""
        # Create mock shift: 09:00-17:00
        mock_shift = self.create_mock_shift(
            1, date(2025, 1, 1), time(9, 0), time(17, 0)
        )
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = [mock_shift]
        mock_roster_model.objects = mock_queryset
        
        # Test clock-in at 20:00 (outside shift hours)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(20, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        # Should not find any matching shift
        self.assertIsNone(result)

    @patch('attendance.views.StaffRoster')
    def test_multiple_shifts_picks_earliest(self, mock_roster_model):
        """Test that when multiple shifts match, earliest is picked"""
        # Create overlapping shifts (shouldn't happen with proper validation, but test anyway)
        shift1 = self.create_mock_shift(
            1, date(2025, 1, 1), time(8, 0), time(12, 0)
        )
        shift2 = self.create_mock_shift(
            2, date(2025, 1, 1), time(10, 0), time(14, 0)
        )
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = [shift1, shift2]
        mock_roster_model.objects = mock_queryset
        
        # Clock-in at 11:00 (matches both shifts)
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(11, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        # Should pick the earliest starting shift (shift1)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)

    @patch('attendance.views.StaffRoster')
    def test_empty_shifts_list(self, mock_roster_model):
        """Test when no shifts exist for the date range"""
        mock_queryset = Mock()
        mock_queryset.filter.return_value = []  # No shifts
        mock_roster_model.objects = mock_queryset
        
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        self.assertIsNone(result)

    @patch('attendance.views.StaffRoster')
    def test_shift_with_null_times(self, mock_roster_model):
        """Test handling of shifts with null start/end times"""
        # Create shift with null times (should be filtered out)
        mock_shift = self.create_mock_shift(
            1, date(2025, 1, 1), None, None
        )
        
        mock_queryset = Mock()
        mock_queryset.filter.return_value = [mock_shift]
        mock_roster_model.objects = mock_queryset
        
        clock_dt = make_aware(datetime.combine(date(2025, 1, 1), time(10, 0)))
        
        result = find_matching_shift_for_datetime(
            hotel=self.mock_hotel,
            staff=self.mock_staff,
            current_dt=clock_dt
        )
        
        # Should not match shift with null times
        self.assertIsNone(result)
        
        # Verify filter excludes null times
        call_args = mock_queryset.filter.call_args[1]
        self.assertFalse(call_args['shift_start__isnull'])
        self.assertFalse(call_args['shift_end__isnull'])

    def test_date_range_calculation(self):
        """Test that correct date range (today and yesterday) is used"""
        # Test with mock that we can inspect
        with patch('attendance.views.StaffRoster') as mock_roster_model:
            mock_queryset = Mock()
            mock_queryset.filter.return_value = []
            mock_roster_model.objects = mock_queryset
            
            # Use specific date for predictable testing
            clock_dt = make_aware(datetime.combine(date(2025, 1, 15), time(10, 0)))
            
            find_matching_shift_for_datetime(
                hotel=self.mock_hotel,
                staff=self.mock_staff,
                current_dt=clock_dt
            )
            
            # Verify date range includes today and yesterday
            call_args = mock_queryset.filter.call_args[1]
            date_range = call_args['shift_date__in']
            
            self.assertIn(date(2025, 1, 15), date_range)  # Today
            self.assertIn(date(2025, 1, 14), date_range)  # Yesterday
            self.assertEqual(len(date_range), 2)


if __name__ == '__main__':
    unittest.main()