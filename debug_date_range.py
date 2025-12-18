#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from rooms.models import RoomType, RoomTypeInventory
from hotel.services.availability import (
    _inventory_for_date, 
    _booked_for_date,
    is_room_type_available,
    get_room_type_availability
)

def test_date_range_availability():
    """Test availability across a full date range like the frontend would"""
    print("=== DATE RANGE AVAILABILITY TEST ===")
    
    # Get hotel
    hotel = Hotel.objects.filter(is_active=True).first()
    if not hotel:
        print("❌ No active hotel found")
        return
        
    print(f"🏨 Hotel: {hotel.name}")
    
    # Test with typical frontend dates (check-in today, check-out tomorrow)
    check_in = date.today()
    check_out = check_in + timedelta(days=1)
    
    print(f"📅 Testing: {check_in} to {check_out}")
    
    # Get room types
    room_types = hotel.room_types.filter(is_active=True)[:2]  # Test first 2
    
    for rt in room_types:
        print(f"\n--- {rt.name} ({rt.code or 'No code'}) ---")
        
        # Check each individual date in the range
        current_date = check_in
        all_dates_ok = True
        
        while current_date < check_out:
            inventory = _inventory_for_date(rt, current_date)
            booked = _booked_for_date(rt, current_date)
            available = inventory - booked
            
            print(f"  {current_date}: inventory={inventory}, booked={booked}, available={available}")
            
            if available < 1:
                all_dates_ok = False
                print(f"  ❌ {current_date}: Not enough availability")
            else:
                print(f"  ✅ {current_date}: OK")
            
            current_date += timedelta(days=1)
        
        # Test overall availability function
        is_available = is_room_type_available(rt, check_in, check_out, required_units=1)
        print(f"  Final result: is_room_type_available = {is_available}")
        
        if all_dates_ok != is_available:
            print(f"  ⚠️  Mismatch! Manual check = {all_dates_ok}, function = {is_available}")

    # Test the full availability API that the frontend uses
    print(f"\n=== FRONTEND API SIMULATION ===")
    adults = 2
    children = 0
    
    available_rooms = get_room_type_availability(
        hotel, check_in, check_out, adults, children
    )
    
    for room_data in available_rooms[:2]:  # Show first 2
        print(f"Room: {room_data['room_type_name']}")
        print(f"  is_available: {room_data['is_available']}")
        print(f"  can_accommodate: {room_data['can_accommodate']}")
        print(f"  note: {room_data['note']}")

if __name__ == "__main__":
    test_date_range_availability()