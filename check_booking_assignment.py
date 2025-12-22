#!/usr/bin/env python
"""
Quick script to check if room assignment is working.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from hotel.models import RoomBooking

def check_booking(booking_id):
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"✅ Found Booking: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Guest: {booking.primary_first_name} {booking.primary_last_name}")
        print(f"   Check-in: {booking.check_in}")
        print(f"   Check-out: {booking.check_out}")
        print(f"   Assigned Room: {booking.assigned_room}")
        
        if booking.assigned_room:
            print(f"   Room Number: {booking.assigned_room.room_number}")
            print(f"   Room Type: {booking.assigned_room.room_type}")
            print(f"   Room Status: {booking.assigned_room.room_status}")
            print(f"   Assigned At: {booking.room_assigned_at}")
            if booking.room_assigned_by:
                print(f"   Assigned By: {booking.room_assigned_by}")
            else:
                print("   Assigned By: Not specified")
            print("   ✅ ROOM IS ASSIGNED!")
        else:
            print("   ❌ NO ROOM ASSIGNED")
            
        # Check party completeness
        print(f"   Party Complete: {booking.party_complete}")
        
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found")
    except Exception as e:
        print(f"❌ Error checking booking: {e}")

if __name__ == "__main__":
    # Check the specific booking from the logs
    check_booking('BK-2025-0004')