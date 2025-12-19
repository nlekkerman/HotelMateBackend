#!/usr/bin/env python
"""
Test the staff booking detail contract by creating a minimal test scenario.
This tests the actual endpoint without database setup issues.
"""

import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking
from hotel.canonical_serializers import StaffRoomBookingDetailSerializer

def test_booking_serializer():
    """Test serializer with mock booking data"""
    
    # Create a mock booking object for testing serialization
    class MockBooking:
        def __init__(self):
            self.booking_id = "BK-2025-0001"
            self.confirmation_number = "CONF12345"
            self.status = "CONFIRMED"
            self.adults = 4
            self.children = 0
            self.party_complete = False
            self.party_missing_count = 3
            self.precheckin_submitted_at = None
            self.precheckin_payload = {}
            self.nights = 2
            self.total_amount = 200.00
            self.currency = "USD"
            self.check_in = "2025-12-20"
            self.check_out = "2025-12-22"
            self.special_requests = ""
            self.promo_code = ""
            self.payment_reference = ""
            self.payment_provider = ""
            self.paid_at = None
            self.checked_in_at = None
            self.checked_out_at = None
            self.created_at = "2025-12-19T10:00:00Z"
            self.updated_at = "2025-12-19T10:00:00Z"
            self.internal_notes = ""
            self.assigned_room = None
            
        @property
        def party(self):
            # Mock party queryset
            class MockPartyManager:
                def all(self):
                    return []
                def filter(self, **kwargs):
                    return self
                def first(self):
                    return None
                def count(self):
                    return 1
            return MockPartyManager()
            
        @property
        def guests(self):
            # Mock guests queryset  
            class MockGuestsManager:
                def all(self):
                    return []
            return MockGuestsManager()
    
    # Test the serializer
    mock_booking = MockBooking()
    serializer = StaffRoomBookingDetailSerializer(mock_booking)
    
    print("🔍 Testing StaffRoomBookingDetailSerializer output:")
    print("=" * 50)
    
    try:
        data = serializer.data
        
        print("✅ Serialization successful")
        print(f"\n📊 Key contract fields:")
        print(f"  adults: {data.get('adults', 'MISSING')}")
        print(f"  children: {data.get('children', 'MISSING')}")
        print(f"  party_complete: {data.get('party_complete', 'MISSING')}")
        print(f"  party_missing_count: {data.get('party_missing_count', 'MISSING')}")
        print(f"  precheckin_submitted_at: {data.get('precheckin_submitted_at', 'MISSING')}")
        print(f"  precheckin_payload: {data.get('precheckin_payload', 'MISSING')}")
        
        # Check for forbidden fields
        forbidden = ['precheckin_complete', 'guest_info_complete', 'expected_guests']
        for field in forbidden:
            if field in data:
                print(f"  ❌ FORBIDDEN field '{field}' found: {data[field]}")
            else:
                print(f"  ✅ '{field}' correctly absent")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_booking_serializer()
    sys.exit(0 if success else 1)