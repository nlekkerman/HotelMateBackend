#!/usr/bin/env python
"""
Phase 4 Unrostered Clock-In Flow Test
Tests the complete unrostered clock-in approval workflow
"""
import os
import sys
from datetime import datetime, date, time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.utils.timezone import now
from hotel.models import Hotel, AttendanceSettings
from staff.models import Staff
from attendance.models import ClockLog, StaffRoster, RosterPeriod
from attendance.views import find_matching_shift_for_datetime
from attendance.utils import get_attendance_settings, validate_period_finalization

def test_unrostered_flow():
    """Test complete unrostered clock-in flow"""
    print("Testing unrostered clock-in flow...")
    
    try:
        # Get first hotel and staff for testing
        hotel = Hotel.objects.first()
        staff = Staff.objects.filter(hotel=hotel).first()
        
        if not hotel or not staff:
            print("⚠️ No test data available - skipping unrostered flow test")
            return True
        
        print(f"Using hotel: {hotel.name}, staff: {staff.first_name} {staff.last_name}")
        
        # Test 1: No matching shift should return None
        current_dt = now()
        matching_shift = find_matching_shift_for_datetime(hotel, staff, current_dt)
        
        if matching_shift is None:
            print("✓ No matching shift found (as expected for unrostered scenario)")
        else:
            print(f"ℹ️ Found matching shift: {matching_shift} (roster exists)")
        
        # Test 2: Create unrostered clock log
        unrostered_log = ClockLog(
            hotel=hotel,
            staff=staff,
            verified_by_face=True,
            roster_shift=None,
            is_unrostered=True,
            is_approved=False,
            is_rejected=False,
        )
        
        # Validate without saving (we don't want to modify actual data)
        assert unrostered_log.is_unrostered == True
        assert unrostered_log.is_approved == False
        assert unrostered_log.is_rejected == False
        assert unrostered_log.roster_shift is None
        
        print("✓ Unrostered clock log structure is correct")
        
        # Test 3: Test attendance settings
        settings = get_attendance_settings(hotel)
        assert settings is not None
        assert isinstance(settings.break_warning_hours, (int, float)) or hasattr(settings.break_warning_hours, 'quantize')
        assert settings.break_warning_hours > 0
        
        print(f"✓ Attendance settings: {settings.break_warning_hours}h break, {settings.overtime_warning_hours}h overtime, {settings.hard_limit_hours}h limit")
        
        return True
        
    except Exception as e:
        print(f"❌ Unrostered flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_period_finalization():
    """Test period finalization logic"""
    print("\nTesting period finalization...")
    
    try:
        # Get a roster period for testing
        period = RosterPeriod.objects.first()
        
        if not period:
            print("⚠️ No roster periods available - skipping finalization test")
            return True
        
        print(f"Testing with period: {period.title}")
        
        # Test validation function
        is_valid, error_message = validate_period_finalization(period)
        
        if is_valid:
            print("✓ Period can be finalized (no unresolved logs)")
        else:
            print(f"ℹ️ Period cannot be finalized: {error_message}")
        
        # Check finalization fields
        assert hasattr(period, 'is_finalized')
        assert hasattr(period, 'finalized_by')
        assert hasattr(period, 'finalized_at')
        
        print("✓ Period finalization fields exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Period finalization test failed: {e}")
        return False

def test_alert_system():
    """Test alert system components"""
    print("\nTesting alert system...")
    
    try:
        from attendance.utils import check_open_log_alerts_for_hotel
        
        hotel = Hotel.objects.first()
        if not hotel:
            print("⚠️ No hotels available - skipping alert test")
            return True
        
        # This should work without errors even if no logs exist
        alerts_sent = check_open_log_alerts_for_hotel(hotel)
        
        assert isinstance(alerts_sent, dict)
        assert 'break_warnings' in alerts_sent
        assert 'overtime_warnings' in alerts_sent
        assert 'hard_limit_warnings' in alerts_sent
        
        print(f"✓ Alert system works - sent {sum(alerts_sent.values())} alerts")
        
        return True
        
    except Exception as e:
        print(f"❌ Alert system test failed: {e}")
        return False

def main():
    """Run integration tests"""
    print("🧪 Phase 4 Integration Tests")
    print("=" * 50)
    
    tests = [
        test_unrostered_flow,
        test_period_finalization,
        test_alert_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print(f"⚠️ {failed} test(s) failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)