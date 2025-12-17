#!/usr/bin/env python
"""
Simple test to verify party_members vs party fix
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking, BookingGuest
from rooms.models import RoomType
from django.utils import timezone
from datetime import timedelta

def test_party_relationship():
    """Test that party relationship works correctly"""
    print("🔧 Testing party relationship...")
    
    # Get or create test hotel
    hotel, created = Hotel.objects.get_or_create(
        slug="test-party",
        defaults={
            'name': "Test Hotel",
            'city': "Test City", 
            'country': "IE"
        }
    )
    
    # Get or create room type
    room_type, created = RoomType.objects.get_or_create(
        hotel=hotel,
        name="Test Room",
        defaults={
            'short_description': "Test room type",
            'starting_price_from': 100.00
        }
    )
    
    # Create booking
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=timezone.now().date() + timedelta(days=1),
        check_out=timezone.now().date() + timedelta(days=3),
        adults=2,
        children=0,
        total_amount=200.00,
        currency='EUR',
        status='CONFIRMED',
        booker_type='SELF',
        primary_first_name='Test',
        primary_last_name='User',
        primary_email='test@test.com'
    )
    
    print(f"✅ Created booking: {booking.booking_id}")
    
    # Test party relationship
    try:
        party_count = booking.party.count()
        print(f"✅ booking.party.count() works: {party_count}")
        
        party_all = booking.party.all()
        print(f"✅ booking.party.all() works: {list(party_all)}")
        
        # Test party_complete property
        print(f"✅ party_complete: {booking.party_complete}")
        print(f"✅ party_missing_count: {booking.party_missing_count}")
        
    except Exception as e:
        print(f"❌ Error with party relationship: {e}")
        return False
    
    # Test serializer import and basic usage
    try:
        from hotel.booking_serializers import RoomBookingDetailSerializer
        serializer = RoomBookingDetailSerializer(booking)
        
        # Try to access party data
        party_data = serializer.get_party(booking)
        print(f"✅ Serializer get_party works: {party_data}")
        
    except Exception as e:
        print(f"❌ Error with serializer: {e}")
        return False
    
    # Clean up
    booking.delete()
    print("🧹 Cleaned up test data")
    
    return True

if __name__ == '__main__':
    success = test_party_relationship()
    
    if success:
        print("\n✅ ALL PARTY RELATIONSHIP TESTS PASSED!")
        print("The party_members -> party fix is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ PARTY RELATIONSHIP TESTS FAILED!")
        sys.exit(1)