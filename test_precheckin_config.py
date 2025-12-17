"""
Comprehensive tests for Hotel Precheckin Configuration System
Tests all validation rules, model behavior, API endpoints, and edge cases per specification.
"""
import json
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from hotel.models import Hotel, HotelPrecheckinConfig, RoomBooking, BookingPrecheckinToken, BookingGuest
from hotel.precheckin.field_registry import DEFAULT_CONFIG, PRECHECKIN_FIELD_REGISTRY
from rooms.models import RoomType
from staff.models import Staff


class HotelPrecheckinConfigModelTests(TestCase):
    """Test HotelPrecheckinConfig model validation and behavior"""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
    
    def test_get_or_create_default_creates_minimal_config(self):
        """Test that get_or_create_default creates config with minimal defaults"""
        config = HotelPrecheckinConfig.get_or_create_default(self.hotel)
        
        self.assertIsNotNone(config)
        self.assertEqual(config.hotel, self.hotel)
        
        # Verify default enabled fields
        expected_enabled = DEFAULT_CONFIG['enabled']
        self.assertEqual(config.fields_enabled, expected_enabled)
        self.assertTrue(config.fields_enabled.get('eta'))
        self.assertTrue(config.fields_enabled.get('special_requests'))
        self.assertTrue(config.fields_enabled.get('consent_checkbox'))
        
        # Verify default required fields
        expected_required = DEFAULT_CONFIG['required']
        self.assertEqual(config.fields_required, expected_required)
        self.assertTrue(config.fields_required.get('consent_checkbox'))
    
    def test_get_or_create_default_returns_existing_config(self):
        """Test that get_or_create_default returns existing config without changes"""
        # Create initial config
        config1 = HotelPrecheckinConfig.get_or_create_default(self.hotel)
        original_enabled = config1.fields_enabled.copy()
        
        # Get again - should return same instance
        config2 = HotelPrecheckinConfig.get_or_create_default(self.hotel)
        
        self.assertEqual(config1.id, config2.id)
        self.assertEqual(config2.fields_enabled, original_enabled)
    
    def test_subset_validation_rejects_required_without_enabled(self):
        """Test validation rule: required must be subset of enabled"""
        config = HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={'eta': False, 'nationality': True},
            fields_required={'eta': True, 'nationality': False}  # eta required but not enabled
        )
        
        with self.assertRaises(ValidationError) as context:
            config.full_clean()
        
        self.assertIn("cannot be required without being enabled", str(context.exception))
    
    def test_unknown_field_keys_rejected_in_enabled(self):
        """Test that unknown field keys are rejected in fields_enabled"""
        config = HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={'unknown_field': True},
            fields_required={}
        )
        
        with self.assertRaises(ValidationError) as context:
            config.full_clean()
        
        self.assertIn("Unknown field key 'unknown_field'", str(context.exception))
    
    def test_unknown_field_keys_rejected_in_required(self):
        """Test that unknown field keys are rejected in fields_required"""
        config = HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={},
            fields_required={'unknown_field': True}
        )
        
        with self.assertRaises(ValidationError) as context:
            config.full_clean()
        
        self.assertIn("Unknown field key 'unknown_field'", str(context.exception))
    
    def test_valid_subset_configuration_accepted(self):
        """Test that valid configurations pass validation"""
        config = HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={'eta': True, 'nationality': True, 'consent_checkbox': True},
            fields_required={'nationality': True, 'consent_checkbox': True}
        )
        
        # Should not raise ValidationError
        config.full_clean()
        self.assertTrue(True)  # Test passed


class StaffPrecheckinConfigEndpointTests(TestCase):
    """Test staff API endpoints for precheckin configuration management"""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel", 
            slug="test-hotel"
        )
        
        # Create super staff admin user
        self.staff_user = User.objects.create_user(
            username='superstaff',
            password='testpass123'
        )
        self.staff_member = Staff.objects.create(
            user=self.staff_user,
            hotel=self.hotel,
            role='SUPER_ADMIN'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff_user)
        
        self.config_url = f'/api/staff/hotel/{self.hotel.slug}/precheckin-config/'
    
    def test_get_returns_current_config_and_registry(self):
        """Test GET endpoint returns current config plus field registry"""
        # Create custom config
        config = HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={'eta': True, 'nationality': True},
            fields_required={'nationality': True}
        )
        
        response = self.client.get(self.config_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['enabled'], config.fields_enabled)
        self.assertEqual(data['required'], config.fields_required)
        self.assertEqual(data['field_registry'], PRECHECKIN_FIELD_REGISTRY)
    
    def test_get_auto_creates_default_config_if_missing(self):
        """Test GET auto-creates default config if none exists"""
        response = self.client.get(self.config_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return default config
        self.assertEqual(data['enabled'], DEFAULT_CONFIG['enabled'])
        self.assertEqual(data['required'], DEFAULT_CONFIG['required'])
        
        # Verify config was created in database
        config = HotelPrecheckinConfig.objects.get(hotel=self.hotel)
        self.assertEqual(config.fields_enabled, DEFAULT_CONFIG['enabled'])
    
    def test_post_updates_configuration_successfully(self):
        """Test POST endpoint updates configuration with valid data"""
        update_data = {
            'enabled': {
                'eta': True,
                'nationality': True, 
                'consent_checkbox': True,
                'date_of_birth': True
            },
            'required': {
                'nationality': True,
                'consent_checkbox': True
            }
        }
        
        response = self.client.post(self.config_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['enabled'], update_data['enabled'])
        self.assertEqual(data['required'], update_data['required'])
        
        # Verify database was updated
        config = HotelPrecheckinConfig.objects.get(hotel=self.hotel)
        self.assertEqual(config.fields_enabled, update_data['enabled'])
        self.assertEqual(config.fields_required, update_data['required'])
    
    def test_post_rejects_required_true_when_enabled_false(self):
        """Test POST rejects configuration where required=true but enabled=false"""
        invalid_data = {
            'enabled': {'eta': False, 'nationality': True},
            'required': {'eta': True, 'nationality': False}  # eta required but not enabled
        }
        
        response = self.client.post(self.config_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be required without being enabled', response.json()['error'])
    
    def test_post_rejects_unknown_field_keys_in_enabled(self):
        """Test POST rejects unknown field keys in enabled configuration"""
        invalid_data = {
            'enabled': {'unknown_field': True},
            'required': {}
        }
        
        response = self.client.post(self.config_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unknown field key: unknown_field', response.json()['error'])
    
    def test_post_rejects_unknown_field_keys_in_required(self):
        """Test POST rejects unknown field keys in required configuration"""
        invalid_data = {
            'enabled': {},
            'required': {'unknown_field': True}
        }
        
        response = self.client.post(self.config_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unknown field key: unknown_field', response.json()['error'])
    
    def test_requires_super_admin_permission(self):
        """Test endpoint requires IsSuperStaffAdminForHotel permission"""
        # Create regular staff user
        regular_user = User.objects.create_user(
            username='regularstaff',
            password='testpass123'
        )
        Staff.objects.create(
            user=regular_user,
            hotel=self.hotel,
            role='STAFF'  # Not super admin
        )
        
        self.client.force_authenticate(user=regular_user)
        
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PrecheckinSubmissionIntegrationTests(TestCase):
    """Test integration of precheckin config with public submission endpoints"""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type and booking
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            code="DLX",
            name="Deluxe Room"
        )
        
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            booking_id="BK123",
            confirmation_number="CONF123",
            check_in="2025-12-20",
            check_out="2025-12-22",
            adults=2,
            children=0,
            booker_type="SELF",
            primary_first_name="John",
            primary_last_name="Doe",
            primary_email="john@example.com"
        )
        
        # Create precheckin token with config snapshot
        import hashlib
        from django.utils import timezone
        from datetime import timedelta
        
        self.raw_token = "test-token-123"
        token_hash = hashlib.sha256(self.raw_token.encode()).hexdigest()
        
        self.token = BookingPrecheckinToken.objects.create(
            booking=self.booking,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(hours=72),
            config_snapshot_enabled={'nationality': True, 'consent_checkbox': True},
            config_snapshot_required={'consent_checkbox': True}
        )
        
        self.client = APIClient()
    
    def test_public_get_includes_config_and_registry(self):
        """Test public GET endpoint includes precheckin_config and field_registry"""
        url = f'/api/public/hotel/{self.hotel.slug}/precheckin/?token={self.raw_token}'
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify new fields are present
        self.assertIn('precheckin_config', data)
        self.assertIn('precheckin_field_registry', data)
        
        # Verify config uses snapshot from token
        expected_config = {
            'enabled': {'nationality': True, 'consent_checkbox': True},
            'required': {'consent_checkbox': True}
        }
        self.assertEqual(data['precheckin_config'], expected_config)
        
        # Verify registry contains only enabled fields
        self.assertIn('nationality', data['precheckin_field_registry'])
        self.assertIn('consent_checkbox', data['precheckin_field_registry'])
        self.assertNotIn('eta', data['precheckin_field_registry'])  # Not enabled in snapshot
    
    def test_public_submit_validates_required_config_fields(self):
        """Test public SUBMIT validates required fields from config"""
        url = f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/'
        
        # Submit without required consent_checkbox
        submit_data = {
            'token': self.raw_token,
            'party': [
                {
                    'role': 'PRIMARY',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'is_staying': True
                },
                {
                    'role': 'COMPANION', 
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                    'is_staying': True
                }
            ],
            'nationality': 'US'  # Optional field provided
            # consent_checkbox missing but required
        }
        
        response = self.client.post(url, submit_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('consent_checkbox is required', response.json()['message'])
    
    def test_public_submit_rejects_unknown_field_keys(self):
        """Test public SUBMIT rejects unknown field keys"""
        url = f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/'
        
        submit_data = {
            'token': self.raw_token,
            'party': [
                {
                    'role': 'PRIMARY',
                    'first_name': 'John',
                    'last_name': 'Doe', 
                    'is_staying': True
                },
                {
                    'role': 'COMPANION',
                    'first_name': 'Jane',
                    'last_name': 'Doe',
                    'is_staying': True
                }
            ],
            'consent_checkbox': True,
            'unknown_field': 'some_value'  # Unknown field
        }
        
        response = self.client.post(url, submit_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Unknown field: unknown_field', response.json()['message'])
    
    def test_public_submit_stores_enabled_fields_in_payload(self):
        """Test public SUBMIT stores enabled fields in precheckin_payload"""
        url = f'/api/public/hotel/{self.hotel.slug}/precheckin/submit/'
        
        submit_data = {
            'token': self.raw_token,
            'party': [
                {
                    'role': 'PRIMARY',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'is_staying': True
                },
                {
                    'role': 'COMPANION',
                    'first_name': 'Jane', 
                    'last_name': 'Doe',
                    'is_staying': True
                }
            ],
            'nationality': 'US',
            'consent_checkbox': True
        }
        
        response = self.client.post(url, submit_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify precheckin_payload was stored
        self.booking.refresh_from_db()
        expected_payload = {
            'nationality': 'US',
            'consent_checkbox': True
        }
        self.assertEqual(self.booking.precheckin_payload, expected_payload)
        self.assertIsNotNone(self.booking.precheckin_submitted_at)
    
    def test_old_tokens_without_snapshots_use_current_hotel_config(self):
        """Test old tokens without snapshots fallback to current HotelPrecheckinConfig"""
        # Create token without config snapshot (old token)
        import hashlib
        from django.utils import timezone
        from datetime import timedelta
        
        old_raw_token = "old-token-456"
        old_token_hash = hashlib.sha256(old_raw_token.encode()).hexdigest()
        
        old_token = BookingPrecheckinToken.objects.create(
            booking=self.booking,
            token_hash=old_token_hash,
            expires_at=timezone.now() + timedelta(hours=72)
            # No config_snapshot fields set (old token)
        )
        
        # Create current hotel config
        HotelPrecheckinConfig.objects.create(
            hotel=self.hotel,
            fields_enabled={'eta': True, 'special_requests': True},
            fields_required={'eta': True}
        )
        
        # Test GET uses current hotel config
        url = f'/api/public/hotel/{self.hotel.slug}/precheckin/?token={old_raw_token}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        expected_config = {
            'enabled': {'eta': True, 'special_requests': True},
            'required': {'eta': True}
        }
        self.assertEqual(data['precheckin_config'], expected_config)


if __name__ == '__main__':
    import django
    django.setup()
    
    # Run specific test categories
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTest(loader.loadTestsFromTestCase(HotelPrecheckinConfigModelTests))
    suite.addTest(loader.loadTestsFromTestCase(StaffPrecheckinConfigEndpointTests))
    suite.addTest(loader.loadTestsFromTestCase(PrecheckinSubmissionIntegrationTests))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)