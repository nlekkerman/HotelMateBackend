#!/usr/bin/env python
"""
Debug script to test overstay extension conflict response.
"""
import os
import sys
import django
from datetime import date, time, datetime, timedelta
from decimal import Decimal
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking
from rooms.models import Room, RoomType
from staff.models import Staff
from room_bookings.services.overstay import extend_overstay, ConflictError
from django.contrib.auth.models import User


def test_conflict_response():
    """Test the 409 conflict response structure."""
    print("🧪 Testing overstay extension conflict response...")
    
    try:
        # Get test hotel
        hotel = Hotel.objects.get(slug="test-hotel-dublin")
        print(f"✓ Found hotel: {hotel.name}")
        
        # Get room and room type
        room_type = RoomType.objects.filter(hotel=hotel).first()
        room = Room.objects.filter(hotel=hotel, room_type=room_type).first()
        
        if not room or not room_type:
            print("❌ No room or room_type found - creating...")
            room_type, _ = RoomType.objects.get_or_create(
                hotel=hotel,
                name="Test Room Type",
                defaults={'max_occupancy': 2, 'starting_price_from': 100.00}
            )
            room, _ = Room.objects.get_or_create(
                hotel=hotel,
                room_number="201",
                defaults={'room_type': room_type, 'room_status': 'READY_FOR_GUEST'}
            )
        
        print(f"✓ Using room: {room.room_number}")
        
        # Create an overstaying booking (ending today)
        today = date.today()
        
        # Clean up existing test data
        RoomBooking.objects.filter(booking_id__startswith="CONFLICT-TEST").delete()
        
        # Create current overstaying booking
        overstaying_booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            assigned_room=room,
            booking_id="CONFLICT-TEST-1",
            confirmation_number="CONF-TEST-1",
            check_in=today - timedelta(days=2),
            check_out=today,  # Should have checked out today
            primary_first_name="John",
            primary_last_name="Overstay",
            primary_email="john.overstay@test.com",
            total_amount=300.00,
            checked_in_at=datetime.combine(today - timedelta(days=2), time(15, 0), tzinfo=pytz.UTC),
            checked_out_at=None,  # Still not checked out
            status="CHECKED_IN"
        )
        
        # Create a CONFLICTING booking that starts tomorrow (so extension conflicts)
        conflicting_booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            assigned_room=room,  # SAME ROOM - this creates conflict
            booking_id="CONFLICT-TEST-2",
            confirmation_number="CONF-TEST-2",
            check_in=today + timedelta(days=1),  # Tomorrow
            check_out=today + timedelta(days=3),  # 2 nights
            primary_first_name="Jane",
            primary_last_name="NewGuest",
            primary_email="jane.newguest@test.com",
            total_amount=200.00,
            status="CONFIRMED"  # This booking is confirmed for tomorrow
        )
        
        print(f"✓ Created overstaying booking: {overstaying_booking.booking_id}")
        print(f"✓ Created conflicting booking: {conflicting_booking.booking_id}")
        print(f"  - Overstay ends: {overstaying_booking.check_out}")
        print(f"  - Conflict starts: {conflicting_booking.check_in}")
        print(f"  - Same room: {room.room_number}")
        
        # Get a staff user
        staff_user = User.objects.filter(is_staff=True).first()
        if not staff_user:
            staff_user = User.objects.create_user(username="test_staff", is_staff=True)
        
        # Try to extend the overstaying booking by 2 days (should conflict!)
        extension_end = today + timedelta(days=2)  # This overlaps with the incoming booking
        
        print(f"🔥 Attempting to extend overstay to: {extension_end}")
        print(f"   This should conflict with booking starting: {conflicting_booking.check_in}")
        
        # This should raise ConflictError
        try:
            result = extend_overstay(
                hotel=hotel,
                booking=overstaying_booking,
                staff_user=staff_user,
                new_checkout_date=extension_end
            )
            print("❌ ERROR: extend_overstay should have raised ConflictError but returned:", result)
            return False
            
        except ConflictError as e:
            print(f"✅ ConflictError raised as expected!")
            print(f"   Message: {e.message}")
            print(f"   Conflicts count: {len(e.conflicts)}")
            print(f"   Suggestions count: {len(e.suggestions)}")
            
            # Build the response payload that the view should return
            payload = {
                'detail': e.message,
                'conflicts': e.conflicts,
                'suggested_rooms': e.suggestions
            }
            
            print(f"📦 Response payload size: {len(str(payload))} characters")
            print("📋 Response structure:")
            import json
            print(json.dumps(payload, indent=2, default=str))
            
            return True
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the conflict test."""
    print("🚀 Testing overstay extension conflict response...\n")
    
    success = test_conflict_response()
    
    if success:
        print("\n🎉 ConflictError structure is correct!")
        print("🔍 If the frontend is still getting a 56-byte response,")
        print("   the issue is in the view layer or middleware.")
    else:
        print("\n💥 ConflictError test failed!")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())