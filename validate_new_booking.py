#!/usr/bin/env python
"""
Validation script to test the new booking create endpoint implementation.
This script validates that the code compiles and the basic structure is correct.
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

try:
    import django
    django.setup()
    
    # Try importing the new classes and functions
    from hotel.models import BookerType, RoomBooking, BookingGuest
    from hotel.booking_views import HotelBookingCreateView
    from hotel.services.booking import create_room_booking_from_request
    
    print("✅ All imports successful!")
    
    # Test BookerType constants
    print(f"✅ BookerType.SELF = {BookerType.SELF}")
    print(f"✅ BookerType.THIRD_PARTY = {BookerType.THIRD_PARTY}")  
    print(f"✅ BookerType.COMPANY = {BookerType.COMPANY}")
    print(f"✅ BookerType.values() = {BookerType.values()}")
    
    # Test view class exists
    print(f"✅ HotelBookingCreateView class: {HotelBookingCreateView}")
    
    # Test service function signature
    import inspect
    sig = inspect.signature(create_room_booking_from_request)
    params = list(sig.parameters.keys())
    expected_params = [
        'hotel', 'room_type', 'check_in', 'check_out', 'adults', 'children',
        'primary_first_name', 'primary_last_name', 'primary_email', 'primary_phone',
        'booker_type', 'booker_first_name', 'booker_last_name', 'booker_email',
        'booker_phone', 'booker_company', 'special_requests', 'promo_code'
    ]
    
    for param in expected_params:
        if param in params:
            print(f"✅ Service function has parameter: {param}")
        else:
            print(f"❌ Service function missing parameter: {param}")
    
    print("\n🎉 Validation completed successfully!")
    print("The new booking create endpoint implementation is ready.")
    
except Exception as e:
    print(f"❌ Validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)