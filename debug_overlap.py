#!/usr/bin/env python
"""
Debug overnight shift overlap detection
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
    has_overlaps_for_staff
)

def debug_overnight_overlap():
    """Debug the overnight shift overlap case"""
    
    shifts_overlap_overnight = [
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(22, 0),
            "shift_end": time(2, 0)  # Next day
        },
        {
            "staff": 1,
            "shift_date": "2025-01-15",
            "shift_start": time(1, 0),   # Should overlap with overnight shift
            "shift_end": time(5, 0)
        }
    ]
    
    print("Debugging overnight overlap case...")
    print("Shift 1: 22:00-02:00 on 2025-01-15")
    print("Shift 2: 01:00-05:00 on 2025-01-15")
    
    # Convert each shift to datetime ranges
    for i, shift in enumerate(shifts_overlap_overnight, 1):
        shift_date = datetime.strptime(shift["shift_date"], "%Y-%m-%d").date()
        start_dt, end_dt = shift_to_datetime_range(
            shift_date, shift["shift_start"], shift["shift_end"]
        )
        print(f"Shift {i}: {start_dt} to {end_dt}")
    
    has_overlap = has_overlaps_for_staff(shifts_overlap_overnight)
    print(f"Overlap detected: {has_overlap}")
    
    # The issue might be that shift 2 (01:00-05:00) is not considered overnight
    # because 05:00 > 01:00, so it stays on the same date
    # But shift 1 (22:00-02:00) spans midnight to the next day
    # So we're comparing:
    # Shift 1: 2025-01-15 22:00 to 2025-01-16 02:00  
    # Shift 2: 2025-01-15 01:00 to 2025-01-15 05:00
    # These don't overlap because they're on different effective dates!
    
    print("\nThe issue is likely that overnight shift detection is based on shift_date,")
    print("but an overnight shift starting at 01:00 on the same date doesn't cross midnight.")

if __name__ == "__main__":
    debug_overnight_overlap()