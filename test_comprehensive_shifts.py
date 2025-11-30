#!/usr/bin/env python
"""
Comprehensive test for overnight shift and overlap detection logic
"""
import os
import sys
from datetime import datetime, date, time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from attendance.views import (
    shift_to_datetime_range, 
    calculate_shift_hours, 
    is_overnight_shift,
    validate_shift_duration,
    validate_overnight_shift_end_time,
    has_overlaps_for_staff
)

def test_overnight_validation_rules():
    """Test overnight shift validation according to business rules"""
    print("Testing overnight shift validation rules...")
    
    # Test 1: Valid overnight shift (22:00 to 02:00)
    try:
        validate_shift_duration(date(2025, 1, 15), time(22, 0), time(2, 0), max_hours=12.0)
        validate_overnight_shift_end_time(time(22, 0), time(2, 0), max_end_hour=6)
        print("✓ Valid overnight shift (22:00-02:00) passes validation")
    except ValueError as e:
        print(f"❌ Valid overnight shift failed: {e}")
        return False
    
    # Test 2: Overnight shift too long (18:00 to 10:00 = 16 hours)
    try:
        validate_shift_duration(date(2025, 1, 15), time(18, 0), time(10, 0), max_hours=12.0)
        print("❌ Overly long overnight shift should have failed")
        return False
    except ValueError:
        print("✓ Overly long overnight shift (18:00-10:00) correctly rejected")
    
    # Test 3: Overnight shift ending too late (23:00 to 08:00)
    try:
        validate_overnight_shift_end_time(time(23, 0), time(8, 0), max_end_hour=6)
        print("❌ Late-ending overnight shift should have failed")
        return False
    except ValueError:
        print("✓ Late-ending overnight shift (23:00-08:00) correctly rejected")
    
    # Test 4: Early morning shift (not overnight) should pass
    try:
        validate_shift_duration(date(2025, 1, 15), time(0, 0), time(6, 0), max_hours=12.0)
        validate_overnight_shift_end_time(time(0, 0), time(6, 0), max_end_hour=6)
        print("✓ Early morning shift (00:00-06:00) passes validation")
    except ValueError as e:
        print(f"❌ Early morning shift failed: {e}")
        return False
    
    return True

def test_overlap_detection_scenarios():
    """Test overlap detection for various shift scenarios"""
    print("\nTesting overlap detection scenarios...")
    
    # Test 1: No overlaps - different staff, same times
    shifts_no_overlap_diff_staff = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(9, 0),
            "shift_end": time(17, 0)
        },
        {
            "staff": 2,  # Different staff
            "shift_date": "2025-01-15",
            "shift_start": time(9, 0),
            "shift_end": time(17, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_no_overlap_diff_staff)
    if not has_overlap:
        print("✓ Different staff with same times - no overlap detected")
    else:
        print("❌ Different staff should not have overlaps")
        return False
    
    # Test 2: Overlap - same staff, overlapping regular shifts
    shifts_overlap_regular = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(9, 0),
            "shift_end": time(17, 0)
        },
        {
            "staff": 1,  # Same staff
            "shift_date": "2025-01-15",
            "shift_start": time(16, 0),  # Overlaps with first shift
            "shift_end": time(23, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_overlap_regular)
    if has_overlap:
        print("✓ Same staff overlapping regular shifts - overlap detected")
    else:
        print("❌ Same staff overlapping shifts should be detected")
        return False
    
    # Test 3: No overlap - same staff, adjacent shifts (exact boundary)
    shifts_adjacent = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(9, 0),
            "shift_end": time(17, 0)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(17, 0),  # Starts exactly when first ends
            "shift_end": time(23, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_adjacent)
    if not has_overlap:
        print("✓ Adjacent shifts (exact boundary) - no overlap detected")
    else:
        print("❌ Adjacent shifts should not overlap")
        return False
    
    # Test 4: Overlap - true overnight shift overlap (both cross midnight)
    shifts_overlap_overnight = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(22, 0),
            "shift_end": time(2, 0)  # Next day (22:00-02:00)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(23, 0),   # Overlaps: 23:00-01:00 overlaps 22:00-02:00
            "shift_end": time(1, 0)       # Both are overnight shifts from same date
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_overlap_overnight)
    if has_overlap:
        print("✓ Overlapping overnight shifts (both cross midnight) - overlap detected")
    else:
        print("❌ Overlapping overnight shifts should be detected")
        return False
    
    # Test 5: No overlap - different dates
    shifts_different_dates = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(22, 0),
            "shift_end": time(2, 0)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-16",  # Different date
            "shift_start": time(1, 0),
            "shift_end": time(5, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_different_dates)
    if not has_overlap:
        print("✓ Same staff different dates - no overlap detected")
    else:
        print("❌ Different dates should not overlap")
        return False
    
    return True

def test_shift_properties():
    """Test shift property calculations"""
    print("\nTesting shift property calculations...")
    
    # Test is_night_shift flag assignment
    test_cases = [
        # (start, end, expected_is_night_shift, description)
        (time(9, 0), time(17, 0), False, "Regular day shift"),
        (time(22, 0), time(2, 0), True, "Overnight shift crossing midnight"),
        (time(0, 0), time(6, 0), False, "Early morning shift (not overnight)"),
        (time(23, 30), time(3, 15), True, "Late night to early morning"),
    ]
    
    for start_time, end_time, expected_is_night, description in test_cases:
        actual_is_night = is_overnight_shift(start_time, end_time)
        if actual_is_night == expected_is_night:
            print(f"✓ {description} - is_night_shift: {actual_is_night}")
        else:
            print(f"❌ {description} - Expected {expected_is_night}, got {actual_is_night}")
            return False
    
    # Test hour calculations
    hour_test_cases = [
        # (date, start, end, expected_hours, description)
        (date(2025, 1, 15), time(9, 0), time(17, 0), 8.0, "8-hour day shift"),
        (date(2025, 1, 15), time(22, 0), time(2, 0), 4.0, "4-hour overnight"),
        (date(2025, 1, 15), time(23, 30), time(3, 0), 3.5, "3.5-hour overnight"),
        (date(2025, 1, 15), time(0, 0), time(6, 0), 6.0, "6-hour early morning"),
    ]
    
    for test_date, start_time, end_time, expected_hours, description in hour_test_cases:
        actual_hours = calculate_shift_hours(test_date, start_time, end_time)
        if actual_hours == expected_hours:
            print(f"✓ {description} - {actual_hours} hours")
        else:
            print(f"❌ {description} - Expected {expected_hours}, got {actual_hours}")
            return False
    
    return True

def main():
    """Run all comprehensive tests"""
    try:
        success = True
        success &= test_shift_properties()
        success &= test_overnight_validation_rules()
        success &= test_overlap_detection_scenarios()
        
        if success:
            print("\n🎉 All comprehensive overnight shift and overlap tests passed!")
            print("\nSummary of validated functionality:")
            print("✅ Overnight shift identification (end < start)")
            print("✅ Early morning shifts (00:00-06:00) not considered overnight")
            print("✅ Duration validation (max 12 hours)")
            print("✅ Overnight end time validation (max 06:00)")
            print("✅ Overlap detection for same staff same date")
            print("✅ No false positives for different staff or dates")
            print("✅ Adjacent shift boundary handling")
            print("✅ Hour calculations for all shift types")
            return True
        else:
            print("\n❌ Some tests failed - see output above")
            return False
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)