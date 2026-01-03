#!/usr/bin/env python3
"""
Debug the NEW booking in room 113 to see what's happening.
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from bookings.services import resolve_guest_chat_context

def debug_room_113_booking():
    """Debug the newest booking in room 113"""
    
    print("🔍 Debugging NEW Booking in Room 113")
    print("=" * 50)
    
    # Find booking with room number 113 that's checked in
    booking = RoomBooking.objects.filter(
        assigned_room__room_number="113",
        status="CONFIRMED",
        checked_in_at__isnull=False,
        checked_out_at__isnull=True
    ).select_related('hotel').order_by('-created_at').first()
    
    if not booking:
        print("❌ No booking found for room 113")
        return
    
    print(f"✅ Found booking: {booking.booking_id}")
    print(f"   Hotel: {booking.hotel.slug}")
    print(f"   Created: {booking.created_at}")
    print(f"   Checked in: {booking.checked_in_at}")
    
    # Check tokens
    tokens = GuestBookingToken.objects.filter(booking=booking).order_by('-created_at')
    print(f"\n📋 Tokens for this booking: {tokens.count()}")
    
    for i, token in enumerate(tokens, 1):
        print(f"\n🎟️ Token #{i}:")
        print(f"   Status: {token.status}")
        print(f"   Purpose: {token.purpose}")
        print(f"   Scopes: {token.scopes}")
        print(f"   Created: {token.created_at}")
        print(f"   Hash: {token.token_hash}")
        
        if token.status == 'ACTIVE':
            print(f"   ✅ This is the ACTIVE token")
            # Check if it has CHAT scope
            if 'CHAT' in token.scopes:
                print(f"   ✅ Token has CHAT scope!")
            else:
                print(f"   ❌ Token missing CHAT scope - only has: {token.scopes}")
                # The backend fix should have worked - let's see why it didn't
                print(f"   🔧 This token was created BEFORE the backend fix was applied")

if __name__ == "__main__":
    debug_room_113_booking()