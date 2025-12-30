#!/usr/bin/env python
"""
Debug script to check GuestBookingToken for BK-2025-0003
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from django.utils import timezone

def debug_guest_token():
    booking_id = 'BK-2025-0003'
    
    print(f"🔍 Debugging GuestBookingToken for {booking_id}")
    print("=" * 50)
    
    # 1. Check if booking exists
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"✅ Booking found: {booking.booking_id}")
        print(f"   Hotel: {booking.hotel.name} ({booking.hotel.slug})")
        print(f"   Status: {booking.status}")
        print(f"   Created: {booking.created_at}")
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
        return
    
    # 2. Check for GuestBookingTokens
    tokens = GuestBookingToken.objects.filter(booking=booking)
    print(f"\n📋 Found {tokens.count()} tokens for this booking:")
    
    for token in tokens:
        print(f"\n  Token ID: {token.id}")
        print(f"  Created: {token.created_at}")
        print(f"  Expires: {token.expires_at}")
        print(f"  Revoked: {token.revoked_at}")
        print(f"  Purpose: {token.purpose}")
        print(f"  Is Valid: {token.is_valid()}")
        print(f"  Last Used: {token.last_used_at}")
        
        # Check if expired
        if token.expires_at and timezone.now() > token.expires_at:
            print("  ⚠️ EXPIRED!")
        if token.revoked_at:
            print("  ⚠️ REVOKED!")
    
    # 3. Generate a new token if none exist or all are invalid
    valid_tokens = [t for t in tokens if t.is_valid()]
    if not valid_tokens:
        print(f"\n🔧 No valid tokens found. Generating new token...")
        try:
            token_obj, raw_token = GuestBookingToken.generate_token(
                booking=booking,
                purpose='STATUS'
            )
            print(f"✅ New token generated!")
            print(f"   Token ID: {token_obj.id}")
            print(f"   Raw Token: {raw_token}")
            print(f"   Expires: {token_obj.expires_at}")
            
            # Test validation
            validated = GuestBookingToken.validate_token(raw_token, booking_id)
            print(f"   Validation Test: {'✅ PASS' if validated else '❌ FAIL'}")
            
        except Exception as e:
            print(f"❌ Failed to generate token: {e}")
    else:
        print(f"\n✅ Found {len(valid_tokens)} valid token(s)")
    
    print(f"\n" + "=" * 50)

if __name__ == '__main__':
    debug_guest_token()