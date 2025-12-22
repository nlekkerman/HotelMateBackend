#!/usr/bin/env python
"""
Test the checkout_rooms function directly without Django test framework bullshit.
This creates real data and tests the actual view.
"""

import os
import sys
import django
from django.db import transaction

# Setup Django
sys.path.append('c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from hotel.models import Hotel
from rooms.models import Room, RoomType
from guests.models import Guest
from rooms.views import checkout_rooms
import json

User = get_user_model()

def create_test_data():
    """Create test hotel and rooms"""
    print("🏗️ Creating test data...")
    
    # Create hotel
    hotel, created = Hotel.objects.get_or_create(
        slug="test-checkout-hotel",
        defaults={
            'name': "Test Checkout Hotel",
            'is_active': True
        }
    )
    if created:
        print(f"  ✅ Created hotel: {hotel.name}")
    else:
        print(f"  ♻️  Using existing hotel: {hotel.name}")
    
    # Create room type
    room_type, created = RoomType.objects.get_or_create(
        hotel=hotel,
        name="Standard Room",
        defaults={
            'starting_price_from': 100.00,
            'currency': 'USD'
        }
    )
    
    # Create rooms
    rooms_data = [
        (301, True, 'OCCUPIED'),
        (302, True, 'OCCUPIED'), 
        (303, False, 'READY_FOR_GUEST')
    ]
    
    rooms = []
    for room_num, occupied, status in rooms_data:
        room, created = Room.objects.get_or_create(
            hotel=hotel,
            room_number=room_num,
            defaults={
                'room_type': room_type,
                'is_occupied': occupied,
                'room_status': status
            }
        )
        if not created:
            # Update existing room
            room.is_occupied = occupied
            room.room_status = status
            room.save()
        rooms.append(room)
        print(f"  🏠 Room {room_num}: ID={room.id}, occupied={room.is_occupied}")
    
    # Create guests in occupied rooms
    for room in rooms[:2]:  # First 2 rooms are occupied
        Guest.objects.get_or_create(
            room=room,
            defaults={
                'first_name': f'Guest',
                'last_name': f'Room{room.room_number}',
                'email': f'guest{room.room_number}@test.com'
            }
        )
        print(f"  👤 Created guest for room {room.room_number}")
    
    return hotel, rooms

def test_checkout_with_ids(hotel, rooms):
    """Test checkout using room database IDs (correct way)"""
    print("\n🧪 Testing checkout with room database IDs...")
    
    factory = APIRequestFactory()
    
    # Use room IDs (correct)
    room_ids = [rooms[0].id, rooms[1].id]  # Rooms 301, 302
    data = {'room_ids': room_ids}
    
    request = factory.post(
        f'/api/staff/hotel/{hotel.slug}/rooms/checkout/',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print(f"  📤 Sending: {data}")
    print(f"  🎯 Targeting rooms: {[r.room_number for r in rooms[:2]]}")
    
    response = checkout_rooms(request, hotel.slug)
    
    print(f"  📥 Status: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"  📄 Response: {response.data}")
    else:
        print(f"  📄 Content: {response.content.decode()}")
    
    # Check if rooms were updated
    if response.status_code == 200:
        for room in rooms[:2]:
            room.refresh_from_db()
            print(f"  🏠 Room {room.room_number}: occupied={room.is_occupied}, status={room.room_status}")
            guest_count = Guest.objects.filter(room=room).count()
            print(f"     👥 Guests remaining: {guest_count}")
    
    return response.status_code == 200

def test_checkout_with_room_numbers(hotel, rooms):
    """Test checkout using room numbers (wrong way - should fail)"""
    print("\n🧪 Testing checkout with room numbers (should fail)...")
    
    factory = APIRequestFactory()
    
    # Use room numbers (wrong!)
    room_numbers = [rooms[0].room_number, rooms[1].room_number]  # 301, 302
    data = {'room_ids': room_numbers}
    
    request = factory.post(
        f'/api/staff/hotel/{hotel.slug}/rooms/checkout/',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print(f"  📤 Sending: {data}")
    print(f"  ❌ Using room numbers instead of database IDs")
    
    response = checkout_rooms(request, hotel.slug)
    
    print(f"  📥 Status: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"  📄 Response: {response.data}")
    else:
        print(f"  📄 Content: {response.content.decode()}")

def test_empty_room_ids(hotel):
    """Test with empty room_ids (should reproduce original error)"""
    print("\n🧪 Testing with empty room_ids...")
    
    factory = APIRequestFactory()
    data = {'room_ids': []}
    
    request = factory.post(
        f'/api/staff/hotel/{hotel.slug}/rooms/checkout/',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    print(f"  📤 Sending: {data}")
    
    response = checkout_rooms(request, hotel.slug)
    
    print(f"  📥 Status: {response.status_code}")
    if hasattr(response, 'data'):
        print(f"  📄 Response: {response.data}")
        if response.data.get('detail') == '`room_ids` must be a non-empty list.':
            print("  ✅ Reproduced original error!")
    
def show_id_vs_number_mapping(rooms):
    """Show the mapping between database IDs and room numbers"""
    print("\n🗺️  ID vs Room Number Mapping:")
    print("=" * 40)
    for room in rooms:
        print(f"  Room {room.room_number} → Database ID: {room.id}")
    print("\n💡 Always use database IDs in room_ids array!")

def cleanup_test_data():
    """Clean up test data"""
    try:
        hotel = Hotel.objects.get(slug="test-checkout-hotel")
        Guest.objects.filter(room__hotel=hotel).delete()
        Room.objects.filter(hotel=hotel).delete()
        RoomType.objects.filter(hotel=hotel).delete()
        hotel.delete()
        print("\n🧹 Cleaned up test data")
    except Hotel.DoesNotExist:
        pass

if __name__ == "__main__":
    print("🚀 Testing checkout_rooms functionality...")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            hotel, rooms = create_test_data()
            
            show_id_vs_number_mapping(rooms)
            
            # Test different scenarios
            success = test_checkout_with_ids(hotel, rooms)
            test_checkout_with_room_numbers(hotel, rooms) 
            test_empty_room_ids(hotel)
            
            print("\n" + "=" * 50)
            if success:
                print("✅ Tests completed successfully!")
                print("🎯 Key findings:")
                print("  - Use database IDs, not room numbers")
                print("  - room_ids must be non-empty list") 
                print("  - Endpoint exists at /api/staff/hotel/{slug}/rooms/checkout/")
            else:
                print("❌ Some tests failed")
                
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_test_data()