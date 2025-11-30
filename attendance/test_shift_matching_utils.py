#!/usr/bin/env python
"""
Unit tests for shift matching utility functions.
These tests focus on the core logic without database dependencies.
"""

import unittest
from datetime import datetime, date, time, timedelta
from attendance.views import shift_to_datetime_range, calculate_shift_hours, is_overnight_shift


class ShiftUtilityTests(unittest.TestCase):
    """Test utility functions for shift calculations"""

    def test_shift_to_datetime_range_normal(self):
        """Test datetime range calculation for normal shifts"""
        shift_date = date(2025, 1, 1)
        shift_start = time(9, 0)
        shift_end = time(17, 0)
        
        start_dt, end_dt = shift_to_datetime_range(shift_date, shift_start, shift_end)
        
        expected_start = datetime.combine(shift_date, shift_start)
        expected_end = datetime.combine(shift_date, shift_end)
        
        self.assertEqual(start_dt, expected_start)
        self.assertEqual(end_dt, expected_end)

    def test_shift_to_datetime_range_overnight(self):
        """Test datetime range calculation for overnight shifts"""
        shift_date = date(2025, 1, 1)
        shift_start = time(22, 0)  # 10 PM
        shift_end = time(2, 0)     # 2 AM next day
        
        start_dt, end_dt = shift_to_datetime_range(shift_date, shift_start, shift_end)
        
        expected_start = datetime.combine(shift_date, shift_start)
        expected_end = datetime.combine(shift_date + timedelta(days=1), shift_end)
        
        self.assertEqual(start_dt, expected_start)
        self.assertEqual(end_dt, expected_end)
        # Verify it crosses to next day
        self.assertEqual(end_dt.date(), date(2025, 1, 2))

    def test_calculate_shift_hours_normal(self):
        """Test hour calculation for normal shifts"""
        hours = calculate_shift_hours(date(2025, 1, 1), time(9, 0), time(17, 0))
        self.assertEqual(hours, 8.0)
        
        # Test partial hours
        hours = calculate_shift_hours(date(2025, 1, 1), time(9, 30), time(17, 15))
        self.assertEqual(hours, 7.75)

    def test_calculate_shift_hours_overnight(self):
        """Test hour calculation for overnight shifts"""
        # 22:00 to 02:00 = 4 hours
        hours = calculate_shift_hours(date(2025, 1, 1), time(22, 0), time(2, 0))
        self.assertEqual(hours, 4.0)
        
        # 23:30 to 07:00 = 7.5 hours
        hours = calculate_shift_hours(date(2025, 1, 1), time(23, 30), time(7, 0))
        self.assertEqual(hours, 7.5)

    def test_is_overnight_shift(self):
        """Test overnight shift detection"""
        # Normal shift
        self.assertFalse(is_overnight_shift(time(9, 0), time(17, 0)))
        
        # Overnight shift
        self.assertTrue(is_overnight_shift(time(22, 0), time(2, 0)))
        self.assertTrue(is_overnight_shift(time(23, 30), time(7, 0)))
        
        # Edge case: same time (0 duration)
        self.assertFalse(is_overnight_shift(time(12, 0), time(12, 0)))

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Midnight shifts
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(0, 0), time(8, 0)
        )
        self.assertEqual(start_dt.time(), time(0, 0))
        self.assertEqual(end_dt.time(), time(8, 0))
        self.assertEqual(start_dt.date(), end_dt.date())  # Same day
        
        # Cross midnight at exactly 00:00
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(20, 0), time(0, 0)
        )
        self.assertEqual(end_dt.date(), date(2025, 1, 2))  # Next day
        
        # Very short overnight shift
        hours = calculate_shift_hours(date(2025, 1, 1), time(23, 45), time(0, 15))
        self.assertEqual(hours, 0.5)  # 30 minutes


if __name__ == '__main__':
    unittest.main()