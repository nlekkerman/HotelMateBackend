#!/usr/bin/env python3
"""
Debug script for chat permissions 404 issue.

Based on the frontend logs:
- guestContext: null
- contextError: { message: "Unable to validate permissions", status: 404 }
- booking status: CONFIRMED, checked_in_at set, room assigned (420)

This suggests the guest token might be invalid/expired or there's a URL mismatch.
"""

import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, GuestBookingToken
from bookings.services import resolve_guest_chat_context, InvalidTokenError, MissingScopeError, NotInHouseError, NoRoomAssignedError
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_chat_permissions():
    """
    Debug chat permissions for a specific booking that's showing issues.
    From the logs: booking has assigned_room_number: 420, status: CONFIRMED, isCheckedIn: true
    """
    
    print("🔍 Debugging Chat Permissions Issue")
    print("=" * 50)
    
    # Find booking with room number 420 that's checked in
    try:
        booking = RoomBooking.objects.filter(
            assigned_room__room_number="420",
            status="CONFIRMED",
            checked_in_at__isnull=False,
            checked_out_at__isnull=True
        ).first()
        
        if not booking:
            print("❌ No booking found with room 420 that's checked in and confirmed")
            # Let's see what bookings we have for room 420
            all_bookings = RoomBooking.objects.filter(
                assigned_room__room_number="420"
            ).order_by('-created_at')[:5]
            
            print(f"📋 Recent bookings for room 420:")
            for b in all_bookings:
                print(f"  - {b.booking_id}: {b.status}, checked_in: {b.checked_in_at}, checked_out: {b.checked_out_at}")
            return
        
        print(f"✅ Found booking: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Room: {booking.assigned_room.room_number if booking.assigned_room else 'None'}")
        print(f"   Checked in: {booking.checked_in_at}")
        print(f"   Checked out: {booking.checked_out_at}")
        print(f"   Hotel: {booking.hotel.slug}")
        
        # Find active guest tokens for this booking
        tokens = GuestBookingToken.objects.filter(
            booking=booking,
            status='ACTIVE'
        ).order_by('-created_at')
        
        print(f"🎟️  Active tokens found: {tokens.count()}")
        
        if not tokens.exists():
            print("❌ No active tokens found for this booking")
            # Check if there are any tokens at all
            all_tokens = GuestBookingToken.objects.filter(booking=booking)
            print(f"📋 Total tokens for booking: {all_tokens.count()}")
            for token in all_tokens[:3]:
                print(f"  - Token: ...{token.token_hash[-8:]} Status: {token.status} Created: {token.created_at}")
            return
        
        # Test each token
        for i, token in enumerate(tokens[:3]):  # Test up to 3 most recent tokens
            print(f"\n🧪 Testing token {i+1}: ...{token.token_hash[-8:]}")
            print(f"   Created: {token.created_at}")
            print(f"   Last used: {token.last_used_at}")
            print(f"   Expires: {token.expires_at}")
            print(f"   Scopes: {token.scopes}")
            
            # Test if token is expired
            now = datetime.now(timezone.utc)
            if token.expires_at and token.expires_at < now:
                print(f"   ⚠️  Token is expired (expired {token.expires_at})")
                continue
                
            # Test the resolve_guest_chat_context function
            try:
                raw_token = f"gbt_{token.token_hash}"
                hotel_slug = booking.hotel.slug
                
                print(f"   🔬 Testing resolve_guest_chat_context...")
                print(f"      hotel_slug: {hotel_slug}")
                print(f"      token: gbt_...{token.token_hash[-8:]}")
                
                booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                    hotel_slug=hotel_slug,
                    token_str=raw_token,
                    required_scopes=["CHAT"],
                    action_required=False
                )
                
                print(f"   ✅ Token validation successful!")
                print(f"      Booking: {booking_result.booking_id}")
                print(f"      Room: {room.room_number if room else None}")
                print(f"      Can chat: {allowed_actions.get('can_chat', False)}")
                print(f"      Disabled reason: {disabled_reason}")
                
                # Test the actual API endpoint URL
                print(f"\n   🌐 Expected API endpoints:")
                print(f"      Context: /api/guest/hotel/{hotel_slug}/chat/context?token={raw_token}")
                print(f"      Messages: /api/guest/hotel/{hotel_slug}/chat/messages?token={raw_token}")
                
                break  # Stop at first working token
                
            except InvalidTokenError as e:
                print(f"   ❌ InvalidTokenError: {e}")
            except MissingScopeError as e:
                print(f"   ❌ MissingScopeError: {e}")
            except NotInHouseError as e:
                print(f"   ❌ NotInHouseError: {e}")
            except NoRoomAssignedError as e:
                print(f"   ❌ NoRoomAssignedError: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

def test_url_patterns():
    """Test if the URL patterns are correctly configured"""
    print("\n🌐 Testing URL Configuration")
    print("=" * 30)
    
    from django.urls import reverse
    from django.test import RequestFactory
    
    try:
        # Test if the canonical guest chat context URL can be resolved
        url = reverse('canonical-guest-chat-context', kwargs={'hotel_slug': 'test-hotel'})
        print(f"✅ canonical-guest-chat-context URL: {url}")
    except Exception as e:
        print(f"❌ canonical-guest-chat-context URL resolution failed: {e}")
    
    # Test the hotel guest chat context URL from hotel.urls
    try:
        from django.urls import resolve
        # The pattern should be /api/guest/hotel/{hotel_slug}/chat/context
        test_path = "/api/guest/hotel/test-hotel/chat/context"
        match = resolve(test_path)
        print(f"✅ URL pattern matches: {test_path} -> {match.func}")
    except Exception as e:
        print(f"❌ URL pattern resolution failed for {test_path}: {e}")

if __name__ == "__main__":
    debug_chat_permissions()
    test_url_patterns()
    
    print(f"\n💡 Next steps:")
    print(f"   1. Check if the token being used by frontend is valid and not expired")
    print(f"   2. Verify the frontend is calling the correct URL: /api/guest/hotel/<hotel_slug>/chat/context")
    print(f"   3. Check if the token has the required 'CHAT' scope")
    print(f"   4. Ensure the booking is in the correct state (checked in, has room assigned)")