#!/usr/bin/env python
"""
Simple test for overnight shift utilities without database dependencies
"""
import os
import sys
from datetime import datetime, date, time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from attendance.views import shift_to_datetime_range, calculate_shift_hours, is_overnight_shift

def test_shift_to_datetime_range():
    """Test the shift_to_datetime_range function"""
    print("Testing shift_to_datetime_range...")
    
    # Test regular shift
    shift_date = date(2025, 1, 15)
    start_time = time(9, 0)
    end_time = time(17, 0)
    
    start_dt, end_dt = shift_to_datetime_range(shift_date, start_time, end_time)
    
    expected_start = datetime(2025, 1, 15, 9, 0)
    expected_end = datetime(2025, 1, 15, 17, 0)
    
    assert start_dt == expected_start, f"Expected {expected_start}, got {start_dt}"
    assert end_dt == expected_end, f"Expected {expected_end}, got {end_dt}"
    print("✓ Regular shift conversion works")
    
    # Test overnight shift
    start_time = time(22, 0)
    end_time = time(2, 0)  # Next day
    
    start_dt, end_dt = shift_to_datetime_range(shift_date, start_time, end_time)
    
    expected_start = datetime(2025, 1, 15, 22, 0)
    expected_end = datetime(2025, 1, 16, 2, 0)  # Next day
    
    assert start_dt == expected_start, f"Expected {expected_start}, got {start_dt}"
    assert end_dt == expected_end, f"Expected {expected_end}, got {end_dt}"
    print("✓ Overnight shift conversion works")

def test_calculate_shift_hours():
    """Test the calculate_shift_hours function"""
    print("\nTesting calculate_shift_hours...")
    
    # Test regular shift: 9 AM to 5 PM = 8 hours
    shift_date = date(2025, 1, 15)
    start_time = time(9, 0)
    end_time = time(17, 0)
    
    hours = calculate_shift_hours(shift_date, start_time, end_time)
    assert hours == 8.0, f"Expected 8.0 hours, got {hours}"
    print("✓ Regular 8-hour shift calculation works")
    
    # Test overnight shift: 10 PM to 2 AM = 4 hours
    start_time = time(22, 0)
    end_time = time(2, 0)
    
    hours = calculate_shift_hours(shift_date, start_time, end_time)
    assert hours == 4.0, f"Expected 4.0 hours, got {hours}"
    print("✓ Overnight 4-hour shift calculation works")
    
    # Test overnight shift with 30-minute segments
    start_time = time(23, 30)
    end_time = time(3, 0)
    
    hours = calculate_shift_hours(shift_date, start_time, end_time)
    assert hours == 3.5, f"Expected 3.5 hours, got {hours}"
    print("✓ Overnight 3.5-hour shift calculation works")

def test_is_overnight_shift():
    """Test the is_overnight_shift function"""
    print("\nTesting is_overnight_shift...")
    
    # Test regular shift
    start_time = time(9, 0)
    end_time = time(17, 0)
    
    is_overnight = is_overnight_shift(start_time, end_time)
    assert not is_overnight, f"Expected False for regular shift, got {is_overnight}"
    print("✓ Regular shift correctly identified as non-overnight")
    
    # Test overnight shift
    start_time = time(22, 0)
    end_time = time(2, 0)
    
    is_overnight = is_overnight_shift(start_time, end_time)
    assert is_overnight, f"Expected True for overnight shift, got {is_overnight}"
    print("✓ Overnight shift correctly identified")
    
    # Test edge case: midnight to 6 AM (NOT overnight - same day)
    start_time = time(0, 0)
    end_time = time(6, 0)
    
    is_overnight = is_overnight_shift(start_time, end_time)
    assert not is_overnight, f"Expected False for early morning shift (00:00-06:00), got {is_overnight}"
    print("✓ Early morning shift (midnight to 6 AM) correctly identified as non-overnight")
    
    # Test true overnight case: 11 PM to 1 AM
    start_time = time(23, 0)
    end_time = time(1, 0)
    
    is_overnight = is_overnight_shift(start_time, end_time)
    assert is_overnight, f"Expected True for overnight shift (23:00-01:00), got {is_overnight}"
    print("✓ True overnight shift (11 PM to 1 AM) correctly identified")

def main():
    """Run all tests"""
    try:
        test_shift_to_datetime_range()
        test_calculate_shift_hours()
        test_is_overnight_shift()
        
        print("\n🎉 All overnight shift utility tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)