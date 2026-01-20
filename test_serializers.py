#!/usr/bin/env python
"""
Test the staff serializers with time control fields to ensure no configuration issues.
"""
import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from hotel.canonical_serializers import StaffRoomBookingListSerializer, StaffRoomBookingDetailSerializer

def test_serializers():
    """Test that the staff serializers work without configuration errors."""
    print("🔍 Testing Staff Booking Serializers")
    print("=" * 50)
    
    # Get a booking to test with
    bookings = RoomBooking.objects.all()[:1]
    if not bookings:
        print("❌ No bookings found in database for testing")
        return False
    
    booking = bookings[0]
    print(f"📋 Testing with booking: {booking.booking_id}")
    
    # Test list serializer
    print("\n📄 Testing StaffRoomBookingListSerializer:")
    try:
        list_serializer = StaffRoomBookingListSerializer(booking)
        data = list_serializer.data
        
        print("✅ List serializer works!")
        print(f"   Fields in output: {len(data)} total")
        
        # Check for our new time control fields
        time_control_fields = [
            'approval_deadline_at', 'is_approval_due_soon', 'is_approval_overdue',
            'approval_overdue_minutes', 'approval_risk_level', 'checkout_deadline_at',
            'is_overstay', 'overstay_minutes', 'overstay_risk_level'
        ]
        
        for field in time_control_fields:
            if field in data:
                print(f"   ✅ {field}: {data[field]}")
            else:
                print(f"   ❌ {field}: MISSING")
                
    except Exception as e:
        print(f"❌ List serializer error: {e}")
        return False
    
    # Test detail serializer
    print("\n📋 Testing StaffRoomBookingDetailSerializer:")
    try:
        detail_serializer = StaffRoomBookingDetailSerializer(booking)
        data = detail_serializer.data
        
        print("✅ Detail serializer works!")
        print(f"   Fields in output: {len(data)} total")
        
        # Check for our new time control fields
        for field in time_control_fields:
            if field in data:
                print(f"   ✅ {field}: {data[field]}")
            else:
                print(f"   ❌ {field}: MISSING")
                
    except Exception as e:
        print(f"❌ Detail serializer error: {e}")
        return False
    
    print("\n🎉 All serializer tests passed!")
    return True

if __name__ == "__main__":
    success = test_serializers()
    sys.exit(0 if success else 1)