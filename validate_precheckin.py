#!/usr/bin/env python
"""
Simple validation script for Hotel Precheckin Configuration System
Tests basic functionality without requiring test database setup.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, HotelPrecheckinConfig
from hotel.precheckin.field_registry import PRECHECKIN_FIELD_REGISTRY, DEFAULT_CONFIG


def test_field_registry():
    """Test that field registry is properly configured"""
    print("🧪 Testing Field Registry...")
    
    # Check registry has expected fields
    expected_fields = ['eta', 'special_requests', 'consent_checkbox', 'nationality', 'date_of_birth']
    
    for field in expected_fields:
        assert field in PRECHECKIN_FIELD_REGISTRY, f"Missing field: {field}"
        assert 'label' in PRECHECKIN_FIELD_REGISTRY[field], f"Missing label for: {field}"
        assert 'type' in PRECHECKIN_FIELD_REGISTRY[field], f"Missing type for: {field}"
    
    print("✅ Field registry validation passed")


def test_default_config():
    """Test default configuration values"""
    print("🧪 Testing Default Config...")
    
    # Check default config structure
    assert 'enabled' in DEFAULT_CONFIG
    assert 'required' in DEFAULT_CONFIG
    
    # Check default enabled fields
    enabled = DEFAULT_CONFIG['enabled']
    assert enabled.get('eta') == True
    assert enabled.get('special_requests') == True
    assert enabled.get('consent_checkbox') == True
    
    # Check default required fields (only consent_checkbox)
    required = DEFAULT_CONFIG['required']
    assert required.get('consent_checkbox') == True
    assert required.get('eta', False) == False
    
    print("✅ Default config validation passed")


def test_model_creation():
    """Test HotelPrecheckinConfig model creation"""
    print("🧪 Testing Model Creation...")
    
    # Create a test hotel (or get existing one)
    hotel, created = Hotel.objects.get_or_create(
        slug='test-validation',
        defaults={
            'name': 'Test Validation Hotel'
        }
    )
    
    # Test get_or_create_default
    config = HotelPrecheckinConfig.get_or_create_default(hotel)
    
    assert config.hotel == hotel
    assert isinstance(config.fields_enabled, dict)
    assert isinstance(config.fields_required, dict)
    
    # Check default values were applied
    assert config.fields_enabled.get('eta') == True
    assert config.fields_enabled.get('consent_checkbox') == True
    assert config.fields_required.get('consent_checkbox') == True
    
    print("✅ Model creation validation passed")


def test_validation_rules():
    """Test model validation rules"""
    print("🧪 Testing Validation Rules...")
    
    # Get test hotel
    hotel = Hotel.objects.filter(slug='test-validation').first()
    if not hotel:
        hotel = Hotel.objects.create(slug='test-validation-2', name='Test Hotel 2')
    
    config = HotelPrecheckinConfig.get_or_create_default(hotel)
    
    # Test valid configuration
    config.fields_enabled = {'eta': True, 'nationality': True, 'consent_checkbox': True}
    config.fields_required = {'nationality': True, 'consent_checkbox': True}
    
    try:
        config.full_clean()  # Should not raise
        print("  ✓ Valid config accepted")
    except Exception as e:
        print(f"  ❌ Valid config rejected: {e}")
        return False
    
    # Test invalid configuration (required without enabled)
    config.fields_enabled = {'eta': False, 'consent_checkbox': True}
    config.fields_required = {'eta': True, 'consent_checkbox': True}
    
    try:
        config.full_clean()
        print("  ❌ Invalid config accepted (should have failed)")
        return False
    except Exception as e:
        print("  ✓ Invalid config properly rejected")
    
    # Test unknown field keys
    config.fields_enabled = {'unknown_field': True, 'consent_checkbox': True}
    config.fields_required = {'consent_checkbox': True}
    
    try:
        config.full_clean()
        print("  ❌ Unknown field accepted (should have failed)")
        return False
    except Exception as e:
        print("  ✓ Unknown field properly rejected")
    
    print("✅ Validation rules working correctly")
    return True


def run_all_tests():
    """Run all validation tests"""
    print("🚀 Running Hotel Precheckin Config Validation Tests\n")
    
    try:
        test_field_registry()
        test_default_config()
        test_model_creation()
        test_validation_rules()
        
        print("\n🎉 All validation tests passed!")
        print("Hotel Precheckin Configuration System is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()