#!/usr/bin/env python3
"""
Debug the new booking in room 349 to see what's wrong with its token.
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from bookings.services import resolve_guest_chat_context
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_room_349_booking():
    """Debug the new booking in room 349"""
    
    print("🔍 Debugging New Booking in Room 349")
    print("=" * 50)
    
    # Find booking with room number 349 that's checked in
    booking = RoomBooking.objects.filter(
        assigned_room__room_number="349",
        status="CONFIRMED",
        checked_in_at__isnull=False,
        checked_out_at__isnull=True
    ).select_related('hotel').first()
    
    if not booking:
        print("❌ No booking found for room 349")
        return
    
    print(f"✅ Found booking: {booking.booking_id}")
    print(f"   Hotel: {booking.hotel.slug}")
    print(f"   Room: {booking.assigned_room.room_number if booking.assigned_room else 'None'}")
    print(f"   Status: {booking.status}")
    print(f"   Checked in: {booking.checked_in_at}")
    
    # Check for tokens
    tokens = GuestBookingToken.objects.filter(booking=booking)
    print(f"\n📋 Total tokens for this booking: {tokens.count()}")
    
    active_tokens = tokens.filter(status='ACTIVE')
    print(f"📋 Active tokens: {active_tokens.count()}")
    
    if active_tokens.exists():
        for token in active_tokens:
            print(f"\n🎟️ Active Token:")
            print(f"   Hash: {token.token_hash}")
            print(f"   Created: {token.created_at}")
            print(f"   Expires: {token.expires_at}")
            print(f"   Scopes: {token.scopes}")
            print(f"   Purpose: {token.purpose}")
            
            # The issue is we need the RAW token, not the hash
            # The raw token should have been provided to the frontend during booking creation
            print(f"\n❌ PROBLEM: We have the hash but need the raw token!")
            print(f"   The frontend should have received a raw token during booking creation")
            print(f"   Check the booking creation response - it should contain 'guest_token' field")
    else:
        print(f"\n❌ NO ACTIVE TOKENS FOUND!")
        print(f"   This means the booking creation didn't generate a token properly")
        
        # Generate a token now
        print(f"\n🔧 Generating token for this booking...")
        try:
            new_token_obj, raw_token = GuestBookingToken.generate_token(
                booking=booking,
                purpose='FULL_ACCESS',
                scopes=['STATUS_READ', 'CHAT', 'ROOM_SERVICE']
            )
            
            print(f"✅ Token generated!")
            print(f"   Raw token: {raw_token}")
            print(f"   Use this token in frontend API calls")
            
            # Test it
            try:
                booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                    hotel_slug=booking.hotel.slug,
                    token_str=raw_token,
                    required_scopes=["CHAT"],
                    action_required=False
                )
                print(f"✅ Token works correctly!")
                print(f"   Can chat: {allowed_actions.get('can_chat', False)}")
                
            except Exception as e:
                print(f"❌ Token test failed: {e}")
        
        except Exception as e:
            print(f"❌ Failed to generate token: {e}")

if __name__ == "__main__":
    debug_room_349_booking()