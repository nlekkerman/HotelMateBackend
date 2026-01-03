#!/usr/bin/env python
"""
Get the correct token for booking BK-2026-0001
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import GuestBookingToken, RoomBooking

def get_correct_token():
    """Get the correct token for BK-2026-0001"""
    
    try:
        # Find the booking
        booking = RoomBooking.objects.get(booking_id="BK-2026-0001")
        print(f"📋 Booking: {booking.booking_id}")
        print(f"   Hotel: {booking.hotel.slug}")
        print(f"   Status: {booking.status}")
        print(f"   Check-in: {booking.checked_in_at}")
        print(f"   Check-out: {booking.checked_out_at}")
        print(f"   Assigned Room: {booking.assigned_room}")
        
        # Find active tokens for this booking
        tokens = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE'
        ).order_by('-created_at')
        
        print(f"\n🔑 Found {tokens.count()} active token(s):")
        
        for token in tokens:
            print(f"\n   Token Details:")
            print(f"   Hash: {token.token_hash}")
            print(f"   Status: {token.status}")
            print(f"   Expires: {token.expires_at}")
            print(f"   Scopes: {token.scopes}")
            print(f"   Created: {token.created_at}")
            
            # Try to find the raw token (this is tricky since we only store hashes)
            # But we can check if there's a recent token generation log or script
            print(f"   ⚠️  Raw token unknown - only hash is stored")
            
        if tokens.count() == 0:
            print("❌ No active tokens found for this booking!")
            print("   You need to generate a new token.")
            
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking BK-2026-0001 not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_correct_token()