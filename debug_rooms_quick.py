#!/usr/bin/env python
"""
Quick debug for room availability issue
"""
import os
import sys
import django
from datetime import date

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel, RoomBooking
from rooms.models import Room, RoomType
from hotel.services.availability import _inventory_for_date, _booked_for_date

def debug_quick():
    hotel = Hotel.objects.get(slug='hotel-killarney')
    today = date.today()
    
    print(f"=== QUICK DEBUG FOR {today} ===")
    
    room_types = hotel.room_types.all()[:2]  # Just check first 2
    
    for rt in room_types:
        print(f"\n--- {rt.name} ({rt.code}) ---")
        
        # Count total physical rooms
        total_rooms = Room.objects.filter(room_type=rt).count()
        print(f"Total physical rooms: {total_rooms}")
        
        if total_rooms == 0:
            print("❌ NO PHYSICAL ROOMS ASSIGNED TO THIS ROOM TYPE!")
            continue
        
        # Count by status
        rooms_by_status = Room.objects.filter(room_type=rt).values_list('room_status', flat=True)
        from collections import Counter
        status_counts = Counter(rooms_by_status)
        print(f"Room statuses: {dict(status_counts)}")
        
        # Count bookable
        bookable = Room.objects.filter(
            room_type=rt,
            room_status='READY_FOR_GUEST',
            is_active=True,
            maintenance_required=False,
            is_out_of_order=False
        ).count()
        print(f"Bookable rooms: {bookable}")
        
        # Check for RoomTypeInventory override
        from rooms.models import RoomTypeInventory
        try:
            inventory_record = RoomTypeInventory.objects.get(room_type=rt, date=today)
            print(f"⚠️  RoomTypeInventory override found!")
            print(f"   stop_sell={inventory_record.stop_sell}")
            print(f"   total_rooms={inventory_record.total_rooms}")
        except RoomTypeInventory.DoesNotExist:
            print("✅ No RoomTypeInventory override")
        
        # Check inventory function
        inventory = _inventory_for_date(rt, today)
        print(f"_inventory_for_date result: {inventory}")
        
        # Check bookings
        booked = _booked_for_date(rt, today)
        print(f"_booked_for_date result: {booked}")
        
        available = inventory - booked
        print(f"Final available: {available}")
        
        if available <= 0:
            print("❌ NO AVAILABILITY!")
            
            # Check actual bookings
            bookings = RoomBooking.objects.filter(
                room_type=rt,
                status__in=['PENDING_PAYMENT', 'CONFIRMED'],
                check_in__lte=today,
                check_out__gt=today
            )
            print(f"Overlapping bookings: {bookings.count()}")
            for booking in bookings:
                print(f"  - {booking.booking_id}: {booking.check_in} to {booking.check_out}, status={booking.status}")

if __name__ == '__main__':
    debug_quick()