#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from rooms.models import RoomType, RoomTypeInventory, Room

def fix_inventory_limits():
    """Fix RoomTypeInventory records that are limiting room availability"""
    print("=== FIXING ROOM TYPE INVENTORY LIMITS ===")
    
    # Get hotel
    hotel = Hotel.objects.filter(is_active=True).first()
    if not hotel:
        print("❌ No active hotel found")
        return
        
    print(f"🏨 Hotel: {hotel.name}")
    
    # Find problematic RoomTypeInventory records
    today = date.today()
    
    room_types = hotel.room_types.filter(is_active=True)
    
    for rt in room_types:
        # Count physical rooms
        physical_count = Room.objects.filter(
            room_type=rt,
            room_status__in=['AVAILABLE', 'READY_FOR_GUEST']
        ).count()
        
        print(f"\n--- {rt.name} ({rt.code or 'No code'}) ---")
        print(f"Physical rooms: {physical_count}")
        
        # Check for inventory overrides
        try:
            inventory_record = RoomTypeInventory.objects.get(room_type=rt, date=today)
            print(f"Current inventory override: {inventory_record.total_rooms}")
            
            if inventory_record.total_rooms < physical_count:
                print(f"⚠️  Override is too low! Updating {inventory_record.total_rooms} → {physical_count}")
                
                # Option 1: Update to match physical rooms
                inventory_record.total_rooms = physical_count
                inventory_record.save()
                print(f"✅ Updated inventory to {physical_count}")
                
                # Option 2: Alternative - delete the override entirely to use physical count
                # inventory_record.delete()
                # print(f"✅ Deleted inventory override - will use physical count ({physical_count})")
            else:
                print(f"✅ Override looks good: {inventory_record.total_rooms}")
                
        except RoomTypeInventory.DoesNotExist:
            print(f"✅ No inventory override - uses physical count ({physical_count})")

if __name__ == "__main__":
    fix_inventory_limits()
    print("\n🎯 Test availability now - should see more rooms available!")