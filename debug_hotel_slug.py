#!/usr/bin/env python3
"""
Enhanced debug script to check hotel slug mismatch issue.
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from bookings.services import hash_token
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_hotel_slug_mismatch():
    """
    Debug the hotel slug mismatch issue specifically.
    """
    
    print("🔍 Debugging Hotel Slug Mismatch Issue")
    print("=" * 50)
    
    # Find the booking with room 420 that's checked in
    booking = RoomBooking.objects.filter(
        assigned_room__room_number="420",
        status="CONFIRMED",
        checked_in_at__isnull=False,
        checked_out_at__isnull=True
    ).select_related('hotel').first()
    
    if not booking:
        print("❌ No booking found")
        return
    
    print(f"✅ Found booking: {booking.booking_id}")
    print(f"   Hotel ID: {booking.hotel.id}")
    print(f"   Hotel slug: '{booking.hotel.slug}'")
    print(f"   Hotel name: '{booking.hotel.name}'")
    
    # Get the active token
    token = GuestBookingToken.objects.filter(
        booking=booking,
        status='ACTIVE'
    ).first()
    
    if not token:
        print("❌ No active token found")
        return
    
    raw_token = f"gbt_{token.token_hash}"
    print(f"   Raw token: {raw_token}")
    
    # The issue seems to be that frontend is calling hotel-killarney but booking is for different slug
    # Let's test different potential hotel slugs
    test_slugs = [
        'hotel-killarney',
        'killarney',
        booking.hotel.slug,  # The actual slug
        booking.hotel.name.lower().replace(' ', '-'),
        booking.hotel.name.lower().replace(' ', '_')
    ]
    
    print(f"\n🧪 Testing different hotel slugs:")
    for slug in test_slugs:
        print(f"   Testing slug: '{slug}'")
        
        # Test the hotel match logic manually
        if booking.hotel.slug == slug:
            print(f"      ✅ MATCH! This slug would work")
        else:
            print(f"      ❌ Mismatch: booking hotel='{booking.hotel.slug}' vs requested='{slug}'")
    
    # Check all hotels to see available slugs
    from hotel.models import Hotel
    all_hotels = Hotel.objects.all()
    print(f"\n📋 All available hotel slugs in system:")
    for hotel in all_hotels:
        marker = " 👈 CURRENT BOOKING" if hotel.id == booking.hotel.id else ""
        print(f"   - {hotel.slug} ('{hotel.name}'){marker}")

if __name__ == "__main__":
    debug_hotel_slug_mismatch()