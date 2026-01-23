#!/usr/bin/env python
"""
Test the actual API endpoint response for conflict.
"""
import os
import sys
import django
from datetime import date, time, datetime, timedelta
import pytz
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from hotel.models import Hotel, RoomBooking
from rooms.models import Room, RoomType


def test_api_conflict_response():
    """Test the actual API response."""
    print("🌐 Testing API conflict response...")
    
    try:
        client = Client()
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username="test_staff",
            defaults={"is_staff": True, "email": "test@example.com"}
        )
        
        # Get test hotel
        hotel = Hotel.objects.get(slug="test-hotel-dublin")
        
        # Get room and room type
        room_type = RoomType.objects.filter(hotel=hotel).first()
        room = Room.objects.filter(hotel=hotel, room_type=room_type).first()
        
        if not room:
            print("❌ No room found - skipping test")
            return False
        
        today = date.today()
        
        # Clean up
        RoomBooking.objects.filter(booking_id__startswith="API-TEST").delete()
        
        # Create overstaying booking
        overstaying_booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            assigned_room=room,
            booking_id="API-TEST-OVERSTAY",
            confirmation_number="API-CONF-OVERSTAY",
            check_in=today - timedelta(days=2),
            check_out=today,
            primary_first_name="John",
            primary_last_name="Overstay",
            total_amount=300.00,
            checked_in_at=datetime.combine(today - timedelta(days=2), time(15, 0), tzinfo=pytz.UTC),
            checked_out_at=None,
            status="CHECKED_IN"
        )
        
        # Create conflicting booking
        conflicting_booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            assigned_room=room,  # Same room = conflict
            booking_id="API-TEST-CONFLICT",
            confirmation_number="API-CONF-CONFLICT",
            check_in=today + timedelta(days=1),
            check_out=today + timedelta(days=3),
            primary_first_name="Jane",
            primary_last_name="NewGuest",
            total_amount=200.00,
            status="CONFIRMED"
        )
        
        print(f"✓ Created test bookings")
        print(f"  Overstay: {overstaying_booking.booking_id} in room {room.room_number}")
        print(f"  Conflict: {conflicting_booking.booking_id} in same room")
        
        # Force authenticate
        client.force_login(user)
        
        # Make API request to extend (should conflict)
        url = f'/api/staff/hotel/{hotel.slug}/room-bookings/{overstaying_booking.id}/overstay/extend/'
        
        response = client.post(url, {
            'add_nights': 2  # This should conflict with the incoming booking
        }, content_type='application/json')
        
        print(f"📡 API Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Length: {len(response.content)} bytes")
        print(f"   Content-Type: {response.get('Content-Type', 'Unknown')}")
        
        if response.content:
            try:
                response_data = response.json()
                print(f"📋 Response JSON:")
                print(json.dumps(response_data, indent=2))
                
                if response.status_code == 409:
                    if 'conflicts' in response_data and 'suggested_rooms' in response_data:
                        print("✅ Proper 409 conflict response with conflicts and suggested_rooms!")
                        return True
                    else:
                        print("❌ 409 response but missing conflicts or suggested_rooms")
                        return False
                else:
                    print(f"❌ Expected 409 but got {response.status_code}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw content: {response.content}")
                return False
        else:
            print("❌ No response content")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_api_conflict_response()
    sys.exit(0 if success else 1)