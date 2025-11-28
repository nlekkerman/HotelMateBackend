#!/usr/bin/env python3
"""
Check room pricing data in the public API response.
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType
from hotel.models import Hotel


def check_api_response():
    """Check what the API returns for room pricing"""
    print("🔍 Checking API response for room prices...\n")
    
    try:
        response = requests.get('http://localhost:8000/api/hotel/public/page/hotel-killarney/')
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return
        
        data = response.json()
        
        # Find rooms section
        rooms_section = None
        for section in data.get('sections', []):
            if section.get('section_type') == 'rooms':
                rooms_section = section
                break
        
        if not rooms_section:
            print("❌ No rooms section found in API response")
            return
        
        print("✅ Found rooms section in API response")
        print(f"📊 Number of room types: {len(rooms_section.get('room_types', []))}\n")
        
        # Check each room type for pricing info
        for i, room in enumerate(rooms_section.get('room_types', []), 1):
            print(f"🏨 Room {i}: {room.get('name', 'Unknown')}")
            print(f"   💰 Price: {room.get('starting_price_from', 'NO PRICE')}")
            print(f"   💱 Currency: {room.get('currency', 'NO CURRENCY')}")
            print(f"   👥 Max occupancy: {room.get('max_occupancy', 'Unknown')}")
            print(f"   📝 Description: {room.get('short_description', 'None')}")
            print(f"   🔗 Booking URL: {room.get('booking_cta_url', 'None')}")
            print()
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")


def check_database_data():
    """Check what's in the database for room pricing"""
    print("🗄️  Checking database for room pricing data...\n")
    
    try:
        hotel = Hotel.objects.get(slug='hotel-killarney')
        room_types = RoomType.objects.filter(hotel=hotel, is_active=True)
        
        print(f"✅ Found hotel: {hotel.name}")
        print(f"📊 Number of active room types: {room_types.count()}\n")
        
        for room in room_types:
            print(f"🏨 Room: {room.name}")
            print(f"   💰 Base price: {getattr(room, 'base_price', 'NO BASE_PRICE FIELD')}")
            print(f"   💰 Starting price: {getattr(room, 'starting_price_from', 'NO STARTING_PRICE_FROM FIELD')}")
            print(f"   💱 Currency: {getattr(room, 'currency', 'NO CURRENCY FIELD')}")
            print(f"   👥 Max occupancy: {room.max_occupancy}")
            print(f"   📝 Description: {room.short_description or 'None'}")
            print()
            
    except Hotel.DoesNotExist:
        print("❌ Hotel 'hotel-killarney' not found in database")
    except Exception as e:
        print(f"❌ Database error: {e}")


def check_room_type_model():
    """Check RoomType model fields"""
    print("📋 Checking RoomType model fields...\n")
    
    fields = [f.name for f in RoomType._meta.get_fields()]
    price_fields = [f for f in fields if 'price' in f.lower() or 'currency' in f.lower()]
    
    print(f"✅ All RoomType fields: {', '.join(fields)}")
    print(f"💰 Price-related fields: {', '.join(price_fields) if price_fields else 'NONE FOUND'}")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("ROOM PRICING DATA CHECK")
    print("=" * 60)
    print()
    
    check_room_type_model()
    check_database_data()
    check_api_response()
    
    print("=" * 60)
    print("DONE")
    print("=" * 60)