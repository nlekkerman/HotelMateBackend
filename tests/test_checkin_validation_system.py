"""
Test Suite for Staff Check-in Validation System

Tests the comprehensive check-in validation implementation following the
STAFF_CHECKIN_VALIDATION_IMPLEMENTATION_PLAN.md specification.

Covers:
- Policy schema + defaults resolver
- Single validation function 
- Time restrictions and date validation
- Room readiness checks
- Error code contracts
- Edge cases and timezone handling
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
import pytz

from hotelmate.utils.checkin_policy import get_checkin_policy, get_hotel_now, _validate_policy_format
from hotelmate.utils.checkin_validation import validate_checkin, _validate_arrival_window


class TestCheckinPolicyResolver(TestCase):
    """Test policy schema + defaults resolver"""
    
    def setUp(self):
        """Create test hotel mock"""
        self.hotel_mock = MagicMock()
        self.hotel_mock.slug = 'test-hotel'
    
    def test_default_policy_values(self):
        """Test that defaults are correctly applied"""
        policy = get_checkin_policy(self.hotel_mock)
        
        expected = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        self.assertEqual(policy, expected)
    
    def test_hotel_specific_policy_override(self):
        """Test that hotel-specific settings override defaults"""
        # Mock hotel with custom settings
        self.hotel_mock.precheckin_config = MagicMock()
        self.hotel_mock.precheckin_config.checkin_policy = {
            'timezone': 'US/Eastern',
            'check_in_time': '16:00',
            'early_checkin_from': '13:00'
            # late_arrival_cutoff should use default
        }
        
        policy = get_checkin_policy(self.hotel_mock)
        
        expected = {
            'timezone': 'US/Eastern',
            'check_in_time': '16:00', 
            'early_checkin_from': '13:00',
            'late_arrival_cutoff': '02:00'  # Default fallback
        }
        
        self.assertEqual(policy, expected)
    
    def test_invalid_timezone_fallback(self):
        """Test that invalid timezone falls back to default"""
        invalid_policy = {
            'timezone': 'Invalid/Timezone',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        validated = _validate_policy_format(invalid_policy)
        self.assertEqual(validated['timezone'], 'Europe/Dublin')
    
    def test_invalid_time_format_fallback(self):
        """Test that invalid time format falls back to default"""
        invalid_policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '25:00',  # Invalid hour
            'early_checkin_from': 'not-a-time',  # Invalid format
            'late_arrival_cutoff': '02:00'
        }
        
        validated = _validate_policy_format(invalid_policy)
        self.assertEqual(validated['check_in_time'], '15:00')  # Default fallback
        self.assertEqual(validated['early_checkin_from'], '12:00')  # Default fallback
        self.assertEqual(validated['late_arrival_cutoff'], '02:00')  # Valid, unchanged
    
    @patch('hotelmate.utils.checkin_policy.timezone.now')
    def test_get_hotel_now_timezone_conversion(self, mock_now):
        """Test hotel local time conversion"""
        # Mock UTC time
        utc_time = datetime(2025, 12, 29, 20, 30, 0, tzinfo=pytz.UTC)  # 8:30 PM UTC
        mock_now.return_value = utc_time
        
        # Test Dublin timezone (UTC+1 in winter)
        hotel_now = get_hotel_now(self.hotel_mock)
        
        # Should be 9:30 PM in Dublin
        dublin_tz = pytz.timezone('Europe/Dublin')
        expected_local = utc_time.astimezone(dublin_tz)
        
        self.assertEqual(hotel_now.hour, expected_local.hour)
        self.assertEqual(hotel_now.minute, expected_local.minute)


class TestCheckinValidation(TestCase):
    """Test single validation function"""
    
    def setUp(self):
        """Set up test data"""
        self.booking_mock = MagicMock()
        self.booking_mock.checked_in_at = None
        self.booking_mock.status = 'CONFIRMED'
        self.booking_mock.check_in = date(2025, 12, 29)
        
        self.room_mock = MagicMock()
        self.room_mock.room_number = '101'
        self.room_mock.room_status = 'READY_FOR_GUEST'
        
        self.policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        # 3:30 PM on check-in date (valid check-in time)
        self.valid_time = datetime(2025, 12, 29, 15, 30)
    
    def test_idempotent_success_already_checked_in(self):
        """Test idempotent response for already checked in booking"""
        self.booking_mock.checked_in_at = timezone.now()
        
        ok, code, detail = validate_checkin(
            self.booking_mock, self.room_mock, self.policy, self.valid_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Already checked in')
    
    def test_booking_not_confirmed_status(self):
        """Test rejection of non-confirmed booking"""
        self.booking_mock.status = 'PENDING_PAYMENT'
        
        ok, code, detail = validate_checkin(
            self.booking_mock, self.room_mock, self.policy, self.valid_time
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'BOOKING_NOT_ELIGIBLE')
        self.assertIn('PENDING_PAYMENT not eligible', detail)
    
    def test_no_room_assigned(self):
        """Test rejection when no room assigned"""
        ok, code, detail = validate_checkin(
            self.booking_mock, None, self.policy, self.valid_time
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'BOOKING_NOT_ELIGIBLE')
        self.assertIn('No room assigned', detail)
    
    def test_room_not_ready_out_of_order(self):
        """Test rejection of out-of-order room"""
        self.room_mock.room_status = 'OUT_OF_ORDER'
        
        ok, code, detail = validate_checkin(
            self.booking_mock, self.room_mock, self.policy, self.valid_time
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'ROOM_NOT_READY')
        self.assertIn('out of order', detail.lower())
    
    def test_room_maintenance_required(self):
        """Test rejection of maintenance required room"""
        self.room_mock.room_status = 'MAINTENANCE_REQUIRED'
        
        ok, code, detail = validate_checkin(
            self.booking_mock, self.room_mock, self.policy, self.valid_time
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'ROOM_NOT_READY')
        self.assertIn('maintenance required', detail.lower())
    
    def test_valid_normal_checkin_time(self):
        """Test successful check-in at normal time (after 3 PM)"""
        ok, code, detail = validate_checkin(
            self.booking_mock, self.room_mock, self.policy, self.valid_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Check-in validation passed')


class TestArrivalWindowValidation(TestCase):
    """Test arrival window validation with exact rules"""
    
    def setUp(self):
        """Set up test data"""
        self.booking_mock = MagicMock()
        self.booking_mock.check_in = date(2025, 12, 29)
        
        self.policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
    
    def test_too_early_before_early_checkin_window(self):
        """Test rejection before early check-in window (before 12:00)"""
        # 11:30 AM on check-in date
        too_early = datetime(2025, 12, 29, 11, 30)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, too_early
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'CHECKIN_TOO_EARLY')
        self.assertIn('12:00', detail)
    
    def test_early_checkin_allowed(self):
        """Test early check-in allowed between 12:00-15:00"""
        # 1:00 PM on check-in date (early check-in window)
        early_time = datetime(2025, 12, 29, 13, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, early_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Early check-in allowed')
    
    def test_normal_checkin_time(self):
        """Test normal check-in time (after 15:00)"""
        # 4:00 PM on check-in date
        normal_time = datetime(2025, 12, 29, 16, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, normal_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Normal check-in time')
    
    def test_late_arrival_allowed(self):
        """Test late arrival on next day within cutoff"""
        # 1:00 AM next day (within 02:00 cutoff)
        late_time = datetime(2025, 12, 30, 1, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, late_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Late arrival allowed')
    
    def test_late_arrival_cutoff_exceeded(self):
        """Test rejection after late arrival cutoff (after 02:00 next day)"""
        # 3:00 AM next day (after 02:00 cutoff)
        too_late = datetime(2025, 12, 30, 3, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, too_late
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'CHECKIN_TOO_LATE')
        self.assertIn('02:00', detail)
    
    def test_wrong_date_too_early(self):
        """Test rejection for date before check-in date"""
        # Day before check-in date
        wrong_date = datetime(2025, 12, 28, 15, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, wrong_date
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'CHECKIN_WRONG_DATE')
        self.assertIn('before arrival date', detail)
    
    def test_wrong_date_too_late(self):
        """Test rejection for date too far after check-in date"""
        # Two days after check-in date
        wrong_date = datetime(2025, 12, 31, 15, 0)
        
        ok, code, detail = _validate_arrival_window(
            self.booking_mock, self.policy, wrong_date
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'CHECKIN_TOO_LATE')
        self.assertIn('window closed', detail)


class TestEdgeCasesAndTimezones(TestCase):
    """Test edge cases and timezone boundary conditions"""
    
    def test_midnight_crossover_boundary(self):
        """Test validation across midnight boundary"""
        booking_mock = MagicMock()
        booking_mock.check_in = date(2025, 12, 29)
        
        policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        # Exactly at midnight (start of next day)
        midnight = datetime(2025, 12, 30, 0, 0)
        
        ok, code, detail = _validate_arrival_window(
            booking_mock, policy, midnight
        )
        
        self.assertTrue(ok)  # Should be allowed as late arrival
        self.assertEqual(detail, 'Late arrival allowed')
    
    def test_exact_cutoff_time_boundary(self):
        """Test validation at exact cutoff time"""
        booking_mock = MagicMock()
        booking_mock.check_in = date(2025, 12, 29)
        
        policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        # Exactly at 02:00 cutoff
        exact_cutoff = datetime(2025, 12, 30, 2, 0)
        
        ok, code, detail = _validate_arrival_window(
            booking_mock, policy, exact_cutoff
        )
        
        self.assertTrue(ok)  # Should be allowed (<=)
        self.assertEqual(detail, 'Late arrival allowed')
        
        # One minute after cutoff
        after_cutoff = datetime(2025, 12, 30, 2, 1)
        
        ok, code, detail = _validate_arrival_window(
            booking_mock, policy, after_cutoff
        )
        
        self.assertFalse(ok)
        self.assertEqual(code, 'CHECKIN_TOO_LATE')


class TestAPIContractCompliance(TestCase):
    """Test error codes as API contract compliance"""
    
    def test_all_error_codes_defined(self):
        """Test that all required error codes are defined"""
        from hotelmate.utils.checkin_validation import CHECKIN_ERROR_CODES
        
        required_codes = [
            'CHECKIN_TOO_EARLY',
            'CHECKIN_WRONG_DATE', 
            'CHECKIN_TOO_LATE',
            'ROOM_NOT_READY',
            'BOOKING_NOT_ELIGIBLE'
        ]
        
        for code in required_codes:
            self.assertIn(code, CHECKIN_ERROR_CODES)
            self.assertTrue(isinstance(CHECKIN_ERROR_CODES[code], str))
            self.assertGreater(len(CHECKIN_ERROR_CODES[code]), 0)
    
    def test_error_message_formatting(self):
        """Test that error messages support formatting placeholders"""
        from hotelmate.utils.checkin_validation import CHECKIN_ERROR_CODES
        
        # Test specific format placeholders
        self.assertIn('{time}', CHECKIN_ERROR_CODES['CHECKIN_TOO_EARLY'])
        self.assertIn('{date}', CHECKIN_ERROR_CODES['CHECKIN_WRONG_DATE'])
        self.assertIn('{cutoff}', CHECKIN_ERROR_CODES['CHECKIN_TOO_LATE'])
        self.assertIn('{room}', CHECKIN_ERROR_CODES['ROOM_NOT_READY'])
        self.assertIn('{reason}', CHECKIN_ERROR_CODES['BOOKING_NOT_ELIGIBLE'])


# Integration test for full validation chain
class TestFullValidationIntegration(TestCase):
    """Test complete validation workflow"""
    
    def test_complete_happy_path(self):
        """Test complete successful check-in validation"""
        # Mock objects
        booking_mock = MagicMock()
        booking_mock.checked_in_at = None
        booking_mock.status = 'CONFIRMED'
        booking_mock.check_in = date(2025, 12, 29)
        
        room_mock = MagicMock()
        room_mock.room_number = '101'
        room_mock.room_status = 'READY_FOR_GUEST'
        
        policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        # Valid check-in time
        valid_time = datetime(2025, 12, 29, 15, 30)
        
        ok, code, detail = validate_checkin(
            booking_mock, room_mock, policy, valid_time
        )
        
        self.assertTrue(ok)
        self.assertEqual(code, '')
        self.assertEqual(detail, 'Check-in validation passed')
    
    def test_complete_failure_chain(self):
        """Test that validation stops at first failure"""
        # Create booking with multiple issues
        booking_mock = MagicMock()
        booking_mock.checked_in_at = None
        booking_mock.status = 'PENDING_PAYMENT'  # First issue: wrong status
        booking_mock.check_in = date(2025, 12, 29)
        
        room_mock = MagicMock()
        room_mock.room_number = '101'
        room_mock.room_status = 'OUT_OF_ORDER'  # Second issue: room not ready
        
        policy = {
            'timezone': 'Europe/Dublin',
            'check_in_time': '15:00',
            'early_checkin_from': '12:00',
            'late_arrival_cutoff': '02:00'
        }
        
        # Third issue: too early time
        too_early_time = datetime(2025, 12, 29, 11, 0)
        
        ok, code, detail = validate_checkin(
            booking_mock, room_mock, policy, too_early_time
        )
        
        # Should fail at first validation step (booking status)
        self.assertFalse(ok)
        self.assertEqual(code, 'BOOKING_NOT_ELIGIBLE')
        self.assertIn('PENDING_PAYMENT', detail)