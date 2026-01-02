#!/usr/bin/env python3
"""
Debug token hashing issue. The hotel slug is correct but token validation is failing.
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

def debug_token_hashing():
    """
    Debug the token hashing process to see why validation is failing.
    """
    
    print("🔍 Debugging Token Hashing Issue")
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
    
    # Get the active token from database
    db_token = GuestBookingToken.objects.filter(
        booking=booking,
        status='ACTIVE'
    ).first()
    
    if not db_token:
        print("❌ No active token found")
        return
    
    print(f"   Database token hash: {db_token.token_hash}")
    print(f"   Token created: {db_token.created_at}")
    print(f"   Token expires: {db_token.expires_at}")
    print(f"   Token status: {db_token.status}")
    
    # Try different token formats to see which one matches
    test_formats = [
        db_token.token_hash,  # Raw hash from DB
        f"gbt_{db_token.token_hash}",  # With prefix
        db_token.token_hash[:64],  # First 64 chars
        db_token.token_hash[-64:],  # Last 64 chars
    ]
    
    print(f"\n🧪 Testing different token formats:")
    for i, raw_token in enumerate(test_formats, 1):
        computed_hash = hash_token(raw_token)
        
        print(f"   Format {i}: {raw_token[:20]}...")
        print(f"      Raw token length: {len(raw_token)}")
        print(f"      Computed hash: {computed_hash}")
        print(f"      DB stored hash:  {db_token.token_hash}")
        print(f"      Hashes match: {computed_hash == db_token.token_hash}")
        
        # Try to find token in database with this hash
        try:
            found_token = GuestBookingToken.objects.get(
                token_hash=computed_hash,
                status='ACTIVE'
            )
            print(f"      ✅ Found matching token in DB!")
            print(f"      Token belongs to booking: {found_token.booking.booking_id}")
            break
        except GuestBookingToken.DoesNotExist:
            print(f"      ❌ No token found with this hash")
        
        print()
    
    # Let's also check the hash_token function implementation
    print(f"🔬 Testing hash_token function:")
    test_token = "gbt_test123"
    test_hash = hash_token(test_token)
    print(f"   Test token: {test_token}")
    print(f"   Test hash: {test_hash}")
    print(f"   Hash length: {len(test_hash)}")
    
    # Test what happens when we use the exact token format from our debug
    original_raw_token = f"gbt_{db_token.token_hash}"
    print(f"\n🎯 Testing the exact token from first debug:")
    print(f"   Original raw token: {original_raw_token}")
    print(f"   Length: {len(original_raw_token)}")
    
    computed_hash_2 = hash_token(original_raw_token)
    print(f"   Computed hash: {computed_hash_2}")
    print(f"   DB stored hash:  {db_token.token_hash}")
    print(f"   Hashes match: {computed_hash_2 == db_token.token_hash}")

if __name__ == "__main__":
    debug_token_hashing()