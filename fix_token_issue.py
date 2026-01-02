#!/usr/bin/env python3
"""
Find the correct raw token that should be generated for the booking and test the full flow.
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from bookings.services import hash_token, resolve_guest_chat_context
import logging
import secrets
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_token_issue():
    """
    Generate a new proper token for the booking and test the complete flow.
    """
    
    print("🔧 Fixing Token Issue for Chat Permissions")
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
    print(f"   Hotel: {booking.hotel.slug}")
    
    # Check existing tokens
    existing_tokens = GuestBookingToken.objects.filter(
        booking=booking,
        status='ACTIVE'
    )
    
    print(f"\n📋 Existing active tokens: {existing_tokens.count()}")
    for token in existing_tokens:
        print(f"   - Token hash: {token.token_hash}")
        print(f"   - Created: {token.created_at}")
        print(f"   - Scopes: {token.scopes}")
    
    # Generate a new proper token with correct flow
    print(f"\n🔧 Generating new proper token...")
    
    # Method 1: Use the model's generate_token method
    try:
        new_token_obj, raw_token = GuestBookingToken.generate_token(
            booking=booking,
            purpose='FULL_ACCESS',
            scopes=['STATUS_READ', 'CHAT', 'ROOM_SERVICE']
        )
        
        print(f"✅ New token generated successfully!")
        print(f"   Raw token: {raw_token}")
        print(f"   Raw token length: {len(raw_token)}")
        print(f"   Stored hash: {new_token_obj.token_hash}")
        print(f"   Scopes: {new_token_obj.scopes}")
        
        # Verify the hash matches what we expect
        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        print(f"   Expected hash: {expected_hash}")
        print(f"   Hashes match: {expected_hash == new_token_obj.token_hash}")
        
        # Test the resolve_guest_chat_context function with the raw token
        print(f"\n🧪 Testing resolve_guest_chat_context with new raw token...")
        
        try:
            booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                hotel_slug=booking.hotel.slug,
                token_str=raw_token,
                required_scopes=["CHAT"],
                action_required=False
            )
            
            print(f"✅ Token validation successful with new token!")
            print(f"   Booking: {booking_result.booking_id}")
            print(f"   Room: {room.room_number if room else None}")
            print(f"   Can chat: {allowed_actions.get('can_chat', False)}")
            print(f"   Disabled reason: {disabled_reason}")
            
            # Show what the correct frontend URL should be
            print(f"\n🌐 CORRECT Frontend API Call:")
            print(f"   URL: /api/guest/hotel/{booking.hotel.slug}/chat/context")
            print(f"   Token parameter: ?token={raw_token}")
            print(f"   OR Authorization header: Bearer {raw_token}")
            
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
    
    except Exception as e:
        print(f"❌ Failed to generate token: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_token_issue()