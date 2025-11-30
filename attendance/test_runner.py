#!/usr/bin/env python
"""
Phase 3 Test Runner - Clock Log and Roster Shift Linking

Runs all Phase 3 tests in the proper order:
1. Utility function tests (no dependencies)
2. Serializer integration tests (mock-based)
3. Core matching logic tests (mock-based)
4. Manual integration verification

Usage:
    python attendance/test_runner.py
"""

import sys
import unittest
from io import StringIO


def run_test_module(module_name, description):
    """
    Run a specific test module and return results
    """
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"Module: {module_name}")
    print(f"{'='*60}")
    
    try:
        # Import and run the test module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)
        
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream, 
            verbosity=2,
            failfast=False
        )
        
        result = runner.run(suite)
        
        # Print results
        output = stream.getvalue()
        print(output)
        
        # Summary
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
        
        print(f"\n{'-'*40}")
        print(f"Tests run: {total_tests}")
        print(f"Failures: {failures}")
        print(f"Errors: {errors}")
        print(f"Skipped: {skipped}")
        print(f"Success rate: {((total_tests - failures - errors) / total_tests * 100):.1f}%" if total_tests > 0 else "N/A")
        
        return result.wasSuccessful(), total_tests, failures, errors
        
    except Exception as e:
        print(f"ERROR: Failed to run {module_name}: {e}")
        return False, 0, 0, 1


def manual_verification():
    """
    Manual verification of key components
    """
    print(f"\n{'='*60}")
    print("Manual Verification Tests")
    print(f"{'='*60}")
    
    try:
        # Test 1: Import all required functions
        print("\n1. Testing imports...")
        from attendance.views import (
            shift_to_datetime_range, 
            calculate_shift_hours, 
            is_overnight_shift,
            find_matching_shift_for_datetime
        )
        from attendance.serializers import ClockLogSerializer
        from attendance.models import ClockLog
        print("✓ All imports successful")
        
        # Test 2: Basic function calls
        print("\n2. Testing basic function calls...")
        from datetime import date, time, datetime
        
        # Test shift_to_datetime_range
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(9, 0), time(17, 0)
        )
        assert start_dt.time() == time(9, 0)
        assert end_dt.time() == time(17, 0)
        print("✓ shift_to_datetime_range works")
        
        # Test overnight shift
        start_dt, end_dt = shift_to_datetime_range(
            date(2025, 1, 1), time(22, 0), time(2, 0)
        )
        assert start_dt.date() == date(2025, 1, 1)
        assert end_dt.date() == date(2025, 1, 2)
        print("✓ Overnight shift calculation works")
        
        # Test calculate_shift_hours
        hours = calculate_shift_hours(date(2025, 1, 1), time(9, 0), time(17, 0))
        assert hours == 8.0
        print("✓ calculate_shift_hours works")
        
        # Test is_overnight_shift
        assert not is_overnight_shift(time(9, 0), time(17, 0))
        assert is_overnight_shift(time(22, 0), time(2, 0))
        print("✓ is_overnight_shift works")
        
        # Test 3: Serializer field configuration
        print("\n3. Testing serializer configuration...")
        serializer = ClockLogSerializer()
        fields = ClockLogSerializer.Meta.fields
        
        assert 'roster_shift_id' in fields
        assert 'roster_shift' in fields
        assert 'hours_worked' in fields
        print("✓ ClockLogSerializer has required fields")
        
        # Check field properties
        roster_shift_field = serializer.fields['roster_shift_id']
        assert roster_shift_field.write_only
        assert roster_shift_field.allow_null
        print("✓ roster_shift_id field configured correctly")
        
        # Test 4: Model field exists
        print("\n4. Testing model field...")
        clock_log_fields = [f.name for f in ClockLog._meta.get_fields()]
        assert 'roster_shift' in clock_log_fields
        print("✓ ClockLog.roster_shift field exists")
        
        print("\n" + "✓" * 40)
        print("ALL MANUAL VERIFICATION TESTS PASSED!")
        print("✓" * 40)
        
        return True, 4, 0, 0
        
    except Exception as e:
        print(f"\n❌ Manual verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 4, 1, 0


def main():
    """
    Main test execution
    """
    print("Phase 3 Test Suite: Clock Log and Roster Shift Linking")
    print("="*80)
    
    test_modules = [
        (
            'attendance.test_shift_matching_utils',
            'Utility Function Tests (shift calculations, datetime ranges)'
        ),
        (
            'attendance.test_serializer_integration', 
            'Serializer Integration Tests (ClockLogSerializer with roster_shift)'
        ),
        (
            'attendance.test_matching_logic',
            'Core Matching Logic Tests (find_matching_shift_for_datetime)'
        )
    ]
    
    all_successful = True
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    # Run unit tests
    for module_name, description in test_modules:
        success, tests, failures, errors = run_test_module(module_name, description)
        all_successful &= success
        total_tests += tests
        total_failures += failures
        total_errors += errors
    
    # Run manual verification
    success, tests, failures, errors = manual_verification()
    all_successful &= success
    total_tests += tests
    total_failures += failures
    total_errors += errors
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests run: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    print(f"Overall success rate: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%" if total_tests > 0 else "N/A")
    
    if all_successful:
        print("\n🎉 ALL TESTS PASSED! Phase 3 implementation is working correctly.")
        print("\nPhase 3 Features Verified:")
        print("✓ ClockLog.roster_shift FK relationship")
        print("✓ ClockLogSerializer roster_shift fields (input/output)")
        print("✓ find_matching_shift_for_datetime helper function")
        print("✓ Overnight shift support in matching logic")
        print("✓ Utility functions for datetime range calculations")
        print("✓ Serializer integration with mock data")
        
        print("\nNext Steps:")
        print("• Run full Django test suite with database")
        print("• Test face_clock_in integration with real data")
        print("• Test management actions (auto-attach-shift, relink-day)")
        print("• Test security and permission isolation")
        
        return 0
    else:
        print("\n❌ SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())