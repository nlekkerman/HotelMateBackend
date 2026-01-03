#!/usr/bin/env python
"""
Debug the 401 Unauthorized issue for the specific token
from the logs: e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import GuestBookingToken, RoomBooking
from bookings.services import hash_token, resolve_guest_chat_context, InvalidTokenError, MissingScopeError
import logging

# Set up logging to see detailed errors
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_token():
    """Debug the failing token from the logs"""
    
    # Token from the logs
    raw_token = "e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0"
    hotel_slug = "hotel-killarney"
    
    print(f"🔍 Debugging token: {raw_token}")
    print(f"🔍 Hotel slug: {hotel_slug}")
    print(f"🔍 Token length: {len(raw_token)}")
    
    # Hash the token
    token_hash = hash_token(raw_token)
    print(f"🔍 Token hash: {token_hash}")
    
    # Look for the token in the database
    try:
        guest_tokens = GuestBookingToken.objects.filter(token_hash=token_hash)
        print(f"🔍 Found {guest_tokens.count()} tokens with this hash")
        
        if guest_tokens.count() == 0:
            print("❌ No tokens found with this hash - token doesn't exist!")
            
            # Check if there are any active tokens for hotel-killarney
            killarney_tokens = GuestBookingToken.objects.filter(
                booking__hotel__slug=hotel_slug,
                status='ACTIVE'
            ).select_related('booking', 'booking__hotel')[:10]
            
            print(f"🔍 Found {killarney_tokens.count()} active tokens for {hotel_slug}:")
            for token in killarney_tokens:
                print(f"   Token: {token.token_hash[:20]}... | Booking: {token.booking.booking_id} | Status: {token.status}")
            
            return
        
        for guest_token in guest_tokens:
            print(f"\n📋 Token Details:")
            print(f"   Hash: {guest_token.token_hash}")
            print(f"   Status: {guest_token.status}")
            print(f"   Expires: {guest_token.expires_at}")
            print(f"   Scopes: {guest_token.scopes}")
            print(f"   Created: {guest_token.created_at}")
            
            booking = guest_token.booking
            print(f"\n📋 Booking Details:")
            print(f"   ID: {booking.booking_id}")
            print(f"   Hotel: {booking.hotel.slug} (requested: {hotel_slug})")
            print(f"   Status: {booking.status}")
            print(f"   Check-in: {booking.checked_in_at}")
            print(f"   Check-out: {booking.checked_out_at}")
            print(f"   Assigned Room: {booking.assigned_room}")
            
            # Test resolve_guest_chat_context
            print(f"\n🧪 Testing resolve_guest_chat_context...")
            try:
                booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                    hotel_slug=hotel_slug,
                    token_str=raw_token,
                    required_scopes=["CHAT"],
                    action_required=False  # Use UX-friendly mode
                )
                
                print(f"✅ resolve_guest_chat_context succeeded:")
                print(f"   Booking: {booking_result.booking_id}")
                print(f"   Room: {room.room_number if room else 'None'}")
                print(f"   Conversation: {conversation.id if conversation else 'None'}")
                print(f"   Allowed Actions: {allowed_actions}")
                print(f"   Disabled Reason: {disabled_reason}")
                
            except InvalidTokenError as e:
                print(f"❌ InvalidTokenError: {e}")
            except MissingScopeError as e:
                print(f"❌ MissingScopeError: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error looking up token: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_token()