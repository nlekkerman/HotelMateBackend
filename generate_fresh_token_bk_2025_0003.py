#!/usr/bin/env python
"""
Debug script to generate a fresh token for BK-2025-0003 for testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
import hashlib

def debug_token_for_pusher():
    booking_id = 'BK-2025-0003'
    
    print(f"🔧 Generating fresh token for Pusher testing: {booking_id}")
    print("=" * 60)
    
    # Get booking
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"✅ Booking: {booking.booking_id} - {booking.hotel.slug}")
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
        return
    
    # Generate a new token (this will revoke the old one)
    print(f"\n🔄 Generating new token (old ones will be auto-revoked)...")
    token_obj, raw_token = GuestBookingToken.generate_token(
        booking=booking,
        purpose='STATUS'
    )
    
    print(f"✅ New token generated!")
    print(f"   Token ID: {token_obj.id}")
    print(f"   Raw Token: {raw_token}")
    print(f"   Hash: {hashlib.sha256(raw_token.encode()).hexdigest()[:16]}...")
    print(f"   Expires: {token_obj.expires_at}")
    
    # Test validation with booking ID
    print(f"\n🧪 Testing token validation...")
    validated = GuestBookingToken.validate_token(raw_token, booking_id)
    if validated:
        print(f"✅ Token validation PASSED")
        print(f"   Validated booking: {validated.booking.booking_id}")
        print(f"   Hotel: {validated.hotel.slug}")
    else:
        print(f"❌ Token validation FAILED")
    
    # Test Pusher channel format
    expected_channel = f"private-guest-booking.{booking_id}"
    print(f"\n📡 Expected Pusher channel: {expected_channel}")
    
    print(f"\n🔧 Frontend should use this token for Pusher auth:")
    print(f"   Token: {raw_token}")
    print(f"   Channel: {expected_channel}")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    debug_token_for_pusher()