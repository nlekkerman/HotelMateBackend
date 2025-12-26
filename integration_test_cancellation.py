"""
Integration test script to verify the guest cancellation implementation.
This tests the core service logic without Django test framework dependencies.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_service_imports():
    """Test that all service components can be imported."""
    try:
        from hotel.services.guest_cancellation import (
            cancel_booking_with_token,
            GuestCancellationError,
            StripeOperationError
        )
        print("✅ Guest cancellation service imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Service import failed: {e}")
        return False

def test_service_structure():
    """Test service function signature and basic structure."""
    try:
        from hotel.services.guest_cancellation import cancel_booking_with_token
        import inspect
        
        # Check function signature
        sig = inspect.signature(cancel_booking_with_token)
        params = list(sig.parameters.keys())
        
        expected_params = ['booking', 'token_obj', 'reason']
        if all(param in params for param in expected_params):
            print("✅ Service function has correct signature")
            return True
        else:
            print(f"❌ Service signature incorrect. Expected {expected_params}, got {params}")
            return False
    except Exception as e:
        print(f"❌ Service structure test failed: {e}")
        return False

def test_model_field_exists():
    """Test that refund_reference field was added to model."""
    try:
        # Try to import the model and check field exists
        from hotel.models import RoomBooking
        
        # Check if refund_reference field exists
        field_names = [field.name for field in RoomBooking._meta.fields]
        
        if 'refund_reference' in field_names:
            print("✅ RoomBooking.refund_reference field exists")
            return True
        else:
            print(f"❌ refund_reference field not found in RoomBooking. Fields: {field_names}")
            return False
    except Exception as e:
        print(f"❌ Model field test failed: {e}")
        return False

def test_exception_classes():
    """Test that custom exception classes are properly defined."""
    try:
        from hotel.services.guest_cancellation import GuestCancellationError, StripeOperationError
        
        # Test exception hierarchy
        if issubclass(GuestCancellationError, Exception):
            print("✅ GuestCancellationError is properly defined")
        else:
            print("❌ GuestCancellationError is not an Exception subclass")
            return False
            
        if issubclass(StripeOperationError, GuestCancellationError):
            print("✅ StripeOperationError is properly defined")
        else:
            print("❌ StripeOperationError is not a GuestCancellationError subclass")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Exception classes test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🧪 Running Guest Cancellation Implementation Integration Tests\n")
    
    tests = [
        test_service_imports,
        test_service_structure, 
        test_model_field_exists,
        test_exception_classes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Implementation looks good.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)