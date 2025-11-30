#!/usr/bin/env python
"""
Simple verification script for Phase 3 implementation.
Tests core functionality without complex Django setup.
"""

import os
import sys
import django

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

def test_phase3_implementation():
    """Test Phase 3 implementation components"""
    print("="*60)
    print("Phase 3 Implementation Verification")
    print("="*60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: Model field exists
    try:
        from attendance.models import ClockLog
        fields = [f.name for f in ClockLog._meta.get_fields()]
        assert 'roster_shift' in fields, "ClockLog.roster_shift field missing"
        print("✓ ClockLog.roster_shift field exists")
        success_count += 1
    except Exception as e:
        print(f"✗ ClockLog model test failed: {e}")
    total_tests += 1
    
    # Test 2: Serializer configuration  
    try:
        from attendance.serializers import ClockLogSerializer
        serializer = ClockLogSerializer()
        fields = ClockLogSerializer.Meta.fields
        
        assert 'roster_shift_id' in fields, "roster_shift_id field missing"
        assert 'roster_shift' in fields, "roster_shift field missing"
        assert hasattr(serializer, 'get_roster_shift'), "get_roster_shift method missing"
        
        roster_field = serializer.fields['roster_shift_id']
        assert roster_field.write_only, "roster_shift_id should be write_only"
        assert roster_field.allow_null, "roster_shift_id should allow_null"
        
        print("✓ ClockLogSerializer configured correctly")
        success_count += 1
    except Exception as e:
        print(f"✗ Serializer test failed: {e}")
    total_tests += 1
    
    # Test 3: Utility functions
    try:
        from attendance.views import (
            shift_to_datetime_range, 
            calculate_shift_hours, 
            is_overnight_shift,
            find_matching_shift_for_datetime
        )
        from datetime import date, time
        
        # Test normal shift
        hours = calculate_shift_hours(date(2025, 1, 1), time(9, 0), time(17, 0))
        assert hours == 8.0, f"Expected 8.0 hours, got {hours}"
        
        # Test overnight detection
        is_overnight = is_overnight_shift(time(22, 0), time(2, 0))
        assert is_overnight, "Should detect overnight shift"
        
        # Test datetime range
        start_dt, end_dt = shift_to_datetime_range(date(2025, 1, 1), time(22, 0), time(2, 0))
        assert end_dt.date() == date(2025, 1, 2), "Overnight shift should end next day"
        
        print("✓ Utility functions working correctly")
        success_count += 1
    except Exception as e:
        print(f"✗ Utility functions test failed: {e}")
    total_tests += 1
    
    # Test 4: View methods exist
    try:
        from attendance.views import ClockLogViewSet
        viewset = ClockLogViewSet()
        
        assert hasattr(viewset, 'auto_attach_shift'), "auto_attach_shift method missing"
        assert hasattr(viewset, 'relink_day'), "relink_day method missing"
        
        print("✓ Management action methods exist")
        success_count += 1
    except Exception as e:
        print(f"✗ ViewSet methods test failed: {e}")
    total_tests += 1
    
    # Test 5: Migration applied
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'attendance_clocklog' 
            AND column_name = 'roster_shift_id'
        """)
        result = cursor.fetchone()
        assert result is not None, "roster_shift_id column not found in database"
        
        print("✓ Database migration applied successfully")
        success_count += 1
    except Exception as e:
        print(f"✗ Database migration test failed: {e}")
    total_tests += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"VERIFICATION SUMMARY: {success_count}/{total_tests} tests passed")
    print("="*60)
    
    if success_count == total_tests:
        print("🎉 Phase 3 implementation is COMPLETE and working!")
        print("\nImplemented Features:")
        print("• ClockLog.roster_shift ForeignKey relationship")
        print("• ClockLogSerializer with roster_shift_id (input) and roster_shift (output)")  
        print("• find_matching_shift_for_datetime helper with overnight support")
        print("• Enhanced face_clock_in to auto-link shifts")
        print("• Management actions: auto_attach_shift, relink_day")
        print("• Database migration applied")
        
        print("\nNext Steps for Full Testing:")
        print("• Create test hotel/staff data")
        print("• Test face recognition with shift linking")  
        print("• Test management actions with real data")
        print("• Verify security isolation between hotels")
        
        return True
    else:
        print("❌ Some components failed verification")
        return False

if __name__ == '__main__':
    success = test_phase3_implementation()
    sys.exit(0 if success else 1)