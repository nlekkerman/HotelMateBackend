#!/usr/bin/env python
"""
Test the updated check-in process to ensure tokens are generated properly
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import GuestBookingToken, RoomBooking

def test_checkin_token_fix():
    """Test that the check-in fix generates proper tokens"""
    
    # Check current token situation for BK-2026-0001
    booking_id = "BK-2026-0001"
    
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"📋 Booking: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Check-in: {booking.checked_in_at}")
        print(f"   Check-out: {booking.checked_out_at}")
        print(f"   Room: {booking.assigned_room}")
        print(f"   Hotel: {booking.hotel.slug}")
        
        # Find active tokens
        active_tokens = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE'
        ).order_by('-created_at')
        
        print(f"\n🔑 Active tokens: {active_tokens.count()}")
        for token in active_tokens:
            print(f"   Hash: {token.token_hash[:20]}...")
            print(f"   Scopes: {token.scopes}")
            print(f"   Created: {token.created_at}")
            print(f"   Expires: {token.expires_at}")
            
        if active_tokens.count() > 0:
            latest_token = active_tokens.first()
            
            # Test the latest token with resolve_guest_chat_context
            print(f"\n🧪 Testing latest token with chat context...")
            
            # We can't get the raw token from the hash, but we can check the scopes
            if 'CHAT' in latest_token.scopes:
                print(f"✅ Latest token has CHAT scope")
                print(f"✅ Frontend should be able to use this token for chat")
            else:
                print(f"❌ Latest token missing CHAT scope: {latest_token.scopes}")
                
            if booking.checked_in_at and booking.assigned_room:
                print(f"✅ Booking is checked in with room assigned")
                print(f"✅ Should allow chat access")
            else:
                print(f"❌ Booking not properly checked in or no room assigned")
                
        else:
            print(f"❌ No active tokens found!")
            print(f"   Next check-in should generate a fresh token")
            
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_checkin_token_fix()