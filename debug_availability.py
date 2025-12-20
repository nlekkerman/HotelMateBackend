#!/usr/bin/env python
"""
Debug availability issue - check if rooms are properly counted by room type
"""
import os
import sys
import django
from datetime import date, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from rooms.models import Room, RoomType
from hotel.services.availability import get_room_type_availability, _inventory_for_date

def debug_availability():
    print("=== AVAILABILITY DEBUG ===")
    
    # Get hotel
    hotel = Hotel.objects.get(slug='hotel-killarney')
    print(f"Hotel: {hotel.name}")
    
    # Get room types
    room_types = hotel.room_types.all()
    print(f"Room Types: {room_types.count()}")
    
    for rt in room_types:
        print(f"\n--- {rt.name} ---")
        
        # Count physical rooms of this type
        physical_rooms = Room.objects.filter(room_type=rt)
        total_rooms = physical_rooms.count()
        print(f"Total physical rooms: {total_rooms}")
        
        # Count bookable rooms of this type
        bookable_rooms = physical_rooms.filter(
            room_status='READY_FOR_GUEST',
            is_active=True,
            maintenance_required=False,
            is_out_of_order=False
        )
        bookable_count = bookable_rooms.count()
        print(f"Bookable rooms: {bookable_count}")
        
        # Test inventory calculation
        today = date.today()
        inventory = _inventory_for_date(rt, today)
        print(f"Inventory for {today}: {inventory}")
        
        # Show room statuses
        statuses = physical_rooms.values_list('room_status', flat=True)
        from collections import Counter
        status_counts = Counter(statuses)
        print(f"Room statuses: {dict(status_counts)}")
    
    # Test availability endpoint
    print(f"\n=== TESTING AVAILABILITY ENDPOINT ===")
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)
    
    availability = get_room_type_availability(
        hotel=hotel,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        children=0
    )
    
    print(f"Availability for {check_in} to {check_out}:")
    for room in availability:
        print(f"  {room['room_type_name']}: available={room['is_available']}, can_accommodate={room['can_accommodate']}")

if __name__ == '__main__':
    debug_availability()