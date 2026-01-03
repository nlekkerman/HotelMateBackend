#!/usr/bin/env python
"""
Generate a fresh token for BK-2026-0001 to fix the 401 Unauthorized issue
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

def generate_token_for_bk_2026_0001():
    booking_id = 'BK-2026-0001'
    
    print(f"🔧 Generating fresh token for: {booking_id}")
    print("=" * 60)
    
    # Get booking
    try:
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"✅ Booking: {booking.booking_id} - {booking.hotel.slug}")
        print(f"   Status: {booking.status}")
        print(f"   Check-in: {booking.checked_in_at}")
        print(f"   Room: {booking.assigned_room}")
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
        return
    
    # Show current tokens
    current_tokens = GuestBookingToken.objects.filter(
        booking=booking,
        status='ACTIVE'
    )
    print(f"\n📋 Current active tokens: {current_tokens.count()}")
    for token in current_tokens:
        print(f"   Hash: {token.token_hash[:20]}...")
        print(f"   Scopes: {token.scopes}")
        print(f"   Created: {token.created_at}")
    
    # Generate a new token (this will revoke the old one)
    print(f"\n🔄 Generating new token (old ones will be auto-revoked)...")
    try:
        token_obj, raw_token = GuestBookingToken.generate_token(
            booking=booking,
            purpose='CHAT',  # This should include CHAT scope
            scopes=['STATUS_READ', 'CHAT', 'ROOM_SERVICE']  # Explicit scopes
        )
        
        print(f"✅ New token generated!")
        print(f"   Token ID: {token_obj.id}")
        print(f"   Raw Token: {raw_token}")
        print(f"   Hash: {hashlib.sha256(raw_token.encode()).hexdigest()}")
        print(f"   Scopes: {token_obj.scopes}")
        print(f"   Expires: {token_obj.expires_at}")
        
        # Test the token with resolve_guest_chat_context
        print(f"\n🧪 Testing token with chat context...")
        from bookings.services import resolve_guest_chat_context
        
        try:
            booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                hotel_slug=booking.hotel.slug,
                token_str=raw_token,
                required_scopes=["CHAT"],
                action_required=False  # UX-friendly mode
            )
            
            print(f"✅ Chat context test PASSED:")
            print(f"   Booking: {booking_result.booking_id}")
            print(f"   Room: {room.room_number if room else 'None'}")
            print(f"   Conversation: {conversation.id if conversation else 'None'}")
            print(f"   Can Chat: {allowed_actions['can_chat']}")
            print(f"   Disabled Reason: {disabled_reason}")
            
        except Exception as e:
            print(f"❌ Chat context test FAILED: {e}")
            import traceback
            traceback.print_exc()
        
        # Print frontend usage
        print(f"\n🌐 Frontend Usage:")
        print(f"   Replace the old token with: {raw_token}")
        print(f"   URL: /api/guest/hotel/{booking.hotel.slug}/chat/context?token={raw_token}")
        
        return raw_token
        
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    generate_token_for_bk_2026_0001()