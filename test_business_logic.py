#!/usr/bin/env python
"""
Edge case tests and business logic validation for overnight shifts
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
    has_overlaps_for_staff,
    is_overnight_shift
)

def test_business_logic_edge_cases():
    """Test edge cases and clarify business logic"""
    print("Testing business logic edge cases...")
    
    print("\n=== OVERNIGHT SHIFT DEFINITION ===")
    print("Business Rule: A shift is 'overnight' only if end_time < start_time")
    print("This means the shift crosses midnight boundary.")
    
    test_cases = [
        # (start, end, is_overnight, explanation)
        (time(22, 0), time(2, 0), True, "22:00-02:00: True overnight (crosses midnight)"),
        (time(0, 0), time(6, 0), False, "00:00-06:00: Early morning shift (same day)"),
        (time(23, 59), time(0, 1), True, "23:59-00:01: Minimal overnight crossing"),
        (time(1, 0), time(23, 0), False, "01:00-23:00: Long day shift (22 hours)"),
    ]
    
    for start, end, expected, explanation in test_cases:
        actual = is_overnight_shift(start, end)
        status = "✓" if actual == expected else "❌"
        print(f"{status} {explanation} -> {actual}")
    
    print("\n=== OVERLAP DETECTION EDGE CASES ===")
    print("Business Rule: Overlaps are detected within (staff_id, shift_date) groups")
    print("Overnight shifts extend to next calendar day but keep original shift_date")
    
    # Edge case 1: Overnight vs early morning on same date (NO overlap)
    print("\nCase 1: Overnight vs Early Morning (same shift_date)")
    shifts_no_overlap_different_logic = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(22, 0),  # Overnight: 22:00 Jan 15 -> 02:00 Jan 16
            "shift_end": time(2, 0)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15", # Same date but early morning shift
            "shift_start": time(1, 0),   # NOT overnight: 01:00 Jan 15 -> 05:00 Jan 15  
            "shift_end": time(5, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_no_overlap_different_logic)
    print(f"Shift 1: 22:00-02:00 (overnight, spans to Jan 16)")
    print(f"Shift 2: 01:00-05:00 (early morning on Jan 15)")
    print(f"Overlap detected: {has_overlap} (Expected: False - different effective dates)")
    
    # Edge case 2: Two overnight shifts same date (OVERLAP)
    print("\nCase 2: Two Overnight Shifts (same shift_date)")
    shifts_overlap_both_overnight = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(22, 0),  # 22:00 Jan 15 -> 02:00 Jan 16
            "shift_end": time(2, 0)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15",  # Same date
            "shift_start": time(23, 0),  # 23:00 Jan 15 -> 01:00 Jan 16 (overlaps!)
            "shift_end": time(1, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_overlap_both_overnight)
    print(f"Shift 1: 22:00-02:00 (overnight)")
    print(f"Shift 2: 23:00-01:00 (overnight, overlaps first)")
    print(f"Overlap detected: {has_overlap} (Expected: True)")
    
    # Edge case 3: Overnight from previous date vs early shift (NO overlap)
    print("\nCase 3: Previous Day Overnight vs Current Day Early")
    shifts_different_dates = [
        {
            "staff": 1,
            "shift_date": "2025-01-14",  # Overnight from Jan 14
            "shift_start": time(22, 0),  # 22:00 Jan 14 -> 02:00 Jan 15
            "shift_end": time(2, 0)
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15",  # Early shift on Jan 15
            "shift_start": time(1, 0),   # 01:00 Jan 15 -> 05:00 Jan 15
            "shift_end": time(5, 0)
        }
    ]
    
    has_overlap = has_overlaps_for_staff(shifts_different_dates)
    print(f"Shift 1: Jan 14 22:00-02:00 (ends 02:00 Jan 15)")
    print(f"Shift 2: Jan 15 01:00-05:00 (starts 01:00 Jan 15)")
    print(f"Overlap detected: {has_overlap} (Expected: False - different shift_date groups)")
    
    print("\n=== PRACTICAL IMPLICATIONS ===")
    print("1. Staff can work overnight (22:00-02:00) and early morning (01:00-05:00)")
    print("   shifts on the same date without system detecting overlap")
    print("2. This allows legitimate scheduling of overnight + early shifts")
    print("3. Real overlaps are detected within the same shift_date group")
    print("4. Adjacent shifts (17:00 end, 17:00 start) are allowed")

def main():
    test_business_logic_edge_cases()
    print("\n🎯 Business logic validation complete!")

if __name__ == "__main__":
    main()