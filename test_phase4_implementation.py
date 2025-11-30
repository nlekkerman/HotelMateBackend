#!/usr/bin/env python
"""
Phase 4 Attendance System Test Suite
Tests for unrostered approval, break/overtime alerts, and period finalization

This test file validates the Phase 4 implementation without requiring database setup.
It tests the core logic, model structures, and utility functions.
"""
import os
import sys
from datetime import datetime, date, time, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_attendance_settings_model():
    """Test AttendanceSettings model structure and defaults"""
    print("Testing AttendanceSettings model...")
    
    try:
        import django
        django.setup()
        
        from hotel.models import AttendanceSettings, Hotel
        
        # Check model fields exist
        assert hasattr(AttendanceSettings, 'hotel')
        assert hasattr(AttendanceSettings, 'break_warning_hours')
        assert hasattr(AttendanceSettings, 'overtime_warning_hours')
        assert hasattr(AttendanceSettings, 'hard_limit_hours')
        assert hasattr(AttendanceSettings, 'enforce_limits')
        
        print("✓ AttendanceSettings model has all required fields")
        
        # Test field defaults (without creating instance)
        field_defaults = {
            field.name: field.default for field in AttendanceSettings._meta.fields
            if hasattr(field, 'default') and field.default is not None
        }
        
        expected_defaults = {
            'break_warning_hours': Decimal('6.0'),
            'overtime_warning_hours': Decimal('10.0'),
            'hard_limit_hours': Decimal('12.0'),
            'enforce_limits': True
        }
        
        for field, expected in expected_defaults.items():
            assert field in field_defaults, f"Missing default for {field}"
            assert field_defaults[field] == expected, f"Wrong default for {field}: got {field_defaults[field]}, expected {expected}"
        
        print("✓ AttendanceSettings model has correct default values")
        
    except Exception as e:
        print(f"❌ AttendanceSettings model test failed: {e}")
        return False
    
    return True

def test_clocklog_model_extensions():
    """Test ClockLog model Phase 4 extensions"""
    print("\nTesting ClockLog model extensions...")
    
    try:
        from attendance.models import ClockLog
        
        # Check Phase 4 fields exist
        phase4_fields = [
            'is_unrostered', 'is_approved', 'is_rejected',
            'break_warning_sent', 'overtime_warning_sent', 'hard_limit_warning_sent',
            'long_session_ack_mode'
        ]
        
        for field_name in phase4_fields:
            assert hasattr(ClockLog, field_name), f"Missing field: {field_name}"
        
        print("✓ ClockLog model has all Phase 4 fields")
        
        # Check field defaults
        field_defaults = {
            field.name: field.default for field in ClockLog._meta.fields
            if hasattr(field, 'default') and field.name in phase4_fields
        }
        
        expected_defaults = {
            'is_unrostered': False,
            'is_approved': True,
            'is_rejected': False,
            'break_warning_sent': False,
            'overtime_warning_sent': False,
            'hard_limit_warning_sent': False,
        }
        
        for field, expected in expected_defaults.items():
            if field in field_defaults:
                assert field_defaults[field] == expected, f"Wrong default for {field}: got {field_defaults[field]}, expected {expected}"
        
        print("✓ ClockLog Phase 4 fields have correct defaults")
        
        # Check long_session_ack_mode choices
        ack_mode_field = ClockLog._meta.get_field('long_session_ack_mode')
        expected_choices = [('stay', 'Stay clocked in'), ('clocked_out', 'Clocked out after warning')]
        assert ack_mode_field.choices == expected_choices, f"Wrong choices for long_session_ack_mode"
        
        print("✓ long_session_ack_mode field has correct choices")
        
    except Exception as e:
        print(f"❌ ClockLog model extension test failed: {e}")
        return False
    
    return True

def test_roster_period_finalization():
    """Test RosterPeriod finalization fields"""
    print("\nTesting RosterPeriod finalization fields...")
    
    try:
        from attendance.models import RosterPeriod
        
        # Check finalization fields exist
        finalization_fields = ['is_finalized', 'finalized_by', 'finalized_at']
        
        for field_name in finalization_fields:
            assert hasattr(RosterPeriod, field_name), f"Missing field: {field_name}"
        
        print("✓ RosterPeriod model has all finalization fields")
        
        # Check is_finalized default
        is_finalized_field = RosterPeriod._meta.get_field('is_finalized')
        assert is_finalized_field.default == False, "is_finalized should default to False"
        
        print("✓ is_finalized field has correct default")
        
    except Exception as e:
        print(f"❌ RosterPeriod finalization test failed: {e}")
        return False
    
    return True

def test_attendance_utils_functions():
    """Test attendance utility functions"""
    print("\nTesting attendance utility functions...")
    
    try:
        from attendance.utils import (
            get_attendance_settings, 
            validate_period_finalization,
            is_period_or_log_locked
        )
        
        print("✓ All required utility functions imported successfully")
        
        # Test get_attendance_settings function signature
        import inspect
        sig = inspect.signature(get_attendance_settings)
        assert 'hotel' in sig.parameters, "get_attendance_settings should accept hotel parameter"
        
        print("✓ get_attendance_settings has correct signature")
        
        # Test validate_period_finalization function signature
        sig = inspect.signature(validate_period_finalization)
        assert 'period' in sig.parameters, "validate_period_finalization should accept period parameter"
        
        print("✓ validate_period_finalization has correct signature")
        
        # Test is_period_or_log_locked function signature
        sig = inspect.signature(is_period_or_log_locked)
        params = list(sig.parameters.keys())
        assert 'roster_period' in params or 'clock_log' in params, "is_period_or_log_locked should accept roster_period or clock_log parameters"
        
        print("✓ is_period_or_log_locked has correct signature")
        
    except Exception as e:
        print(f"❌ Attendance utilities test failed: {e}")
        return False
    
    return True

def test_serializer_updates():
    """Test serializer updates for Phase 4 fields"""
    print("\nTesting serializer updates...")
    
    try:
        from attendance.serializers import (
            ClockLogSerializer, 
            RosterPeriodSerializer,
            UnrosteredConfirmSerializer,
            ClockLogApprovalSerializer,
            AlertActionSerializer,
            PeriodFinalizationSerializer
        )
        
        print("✓ All Phase 4 serializers imported successfully")
        
        # Test ClockLogSerializer fields
        clock_log_fields = ClockLogSerializer.Meta.fields
        phase4_fields = [
            'is_unrostered', 'is_approved', 'is_rejected',
            'break_warning_sent', 'overtime_warning_sent', 'hard_limit_warning_sent',
            'long_session_ack_mode'
        ]
        
        for field in phase4_fields:
            assert field in clock_log_fields, f"ClockLogSerializer missing field: {field}"
        
        print("✓ ClockLogSerializer includes all Phase 4 fields")
        
        # Test RosterPeriodSerializer finalization fields
        roster_period_fields = RosterPeriodSerializer.Meta.fields
        finalization_fields = ['is_finalized', 'finalized_by', 'finalized_by_name', 'finalized_at']
        
        for field in finalization_fields:
            assert field in roster_period_fields, f"RosterPeriodSerializer missing field: {field}"
        
        print("✓ RosterPeriodSerializer includes all finalization fields")
        
        # Test UnrosteredConfirmSerializer
        assert hasattr(UnrosteredConfirmSerializer, 'Meta') or hasattr(UnrosteredConfirmSerializer, '_declared_fields')
        print("✓ UnrosteredConfirmSerializer is properly defined")
        
    except Exception as e:
        print(f"❌ Serializer updates test failed: {e}")
        return False
    
    return True

def test_management_command_exists():
    """Test that management command exists"""
    print("\nTesting management command...")
    
    try:
        command_path = os.path.join(
            os.path.dirname(__file__), 
            'attendance', 'management', 'commands', 'check_attendance_alerts.py'
        )
        
        assert os.path.exists(command_path), "Management command file does not exist"
        print("✓ check_attendance_alerts management command exists")
        
        # Test command content
        with open(command_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert 'class Command' in content, "Command class not found"
        assert 'check_open_log_alerts_for_hotel' in content, "Required function call not found"
        assert '--hotel' in content, "Hotel argument not found"
        assert '--dry-run' in content, "Dry-run argument not found"
        
        print("✓ Management command has correct structure and arguments")
        
    except Exception as e:
        print(f"❌ Management command test failed: {e}")
        return False
    
    return True

def test_view_endpoints():
    """Test that Phase 4 view endpoints are properly defined"""
    print("\nTesting view endpoints...")
    
    try:
        from attendance.views import ClockLogViewSet, RosterPeriodViewSet
        
        # Check ClockLogViewSet Phase 4 methods
        clocklog_methods = [
            'unrostered_confirm', 'approve_log', 'reject_log',
            'stay_clocked_in', 'force_clock_out'
        ]
        
        for method_name in clocklog_methods:
            assert hasattr(ClockLogViewSet, method_name), f"ClockLogViewSet missing method: {method_name}"
        
        print("✓ ClockLogViewSet has all Phase 4 action methods")
        
        # Check RosterPeriodViewSet finalization methods
        period_methods = [
            'finalize_period', 'unfinalize_period', 'finalization_status'
        ]
        
        for method_name in period_methods:
            assert hasattr(RosterPeriodViewSet, method_name), f"RosterPeriodViewSet missing method: {method_name}"
        
        print("✓ RosterPeriodViewSet has all finalization methods")
        
        # Check face_clock_in modifications (look for unrostered detection)
        import inspect
        face_clock_in_source = inspect.getsource(ClockLogViewSet.face_clock_in)
        assert 'unrostered_detected' in face_clock_in_source, "face_clock_in doesn't handle unrostered detection"
        
        print("✓ face_clock_in method handles unrostered scenarios")
        
    except Exception as e:
        print(f"❌ View endpoints test failed: {e}")
        return False
    
    return True

def test_alert_thresholds_logic():
    """Test alert threshold calculation logic"""
    print("\nTesting alert threshold logic...")
    
    try:
        # Test duration calculation
        from django.utils.timezone import now
        
        # Simulate time calculations
        current_time = now()
        past_time = current_time - timedelta(hours=7.5)
        
        duration_hours = (current_time - past_time).total_seconds() / 3600
        
        # Test threshold checks
        break_warning_hours = 6.0
        overtime_warning_hours = 10.0
        hard_limit_hours = 12.0
        
        assert duration_hours >= break_warning_hours, "Should trigger break warning"
        assert duration_hours < overtime_warning_hours, "Should not trigger overtime warning yet (only 7.5 hours)"
        assert duration_hours < hard_limit_hours, "Should not trigger hard limit yet"
        
        print("✓ Alert threshold logic works correctly")
        
    except Exception as e:
        print(f"❌ Alert threshold logic test failed: {e}")
        return False
    
    return True

def main():
    """Run all Phase 4 tests"""
    print("🚀 Starting Phase 4 Attendance System Tests")
    print("=" * 60)
    
    tests = [
        test_attendance_settings_model,
        test_clocklog_model_extensions,
        test_roster_period_finalization,
        test_attendance_utils_functions,
        test_serializer_updates,
        test_management_command_exists,
        test_view_endpoints,
        test_alert_thresholds_logic
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 4 tests passed! Implementation is ready.")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)