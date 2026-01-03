#!/usr/bin/env python
"""
Test the BookingStatusView fix to ensure it returns guest tokens for checked-in guests
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import RoomBooking, BookingManagementToken
from hotel.public_views import BookingStatusView
from django.test import RequestFactory
import hashlib

def test_booking_status_guest_token():
    """Test that BookingStatusView now returns guest tokens for checked-in guests"""
    
    booking_id = "BK-2026-0001"
    hotel_slug = "hotel-killarney"
    
    try:
        # Get the booking
        booking = RoomBooking.objects.get(booking_id=booking_id)
        print(f"📋 Booking: {booking.booking_id}")
        print(f"   Status: {booking.status}")
        print(f"   Check-in: {booking.checked_in_at}")
        print(f"   Check-out: {booking.checked_out_at}")
        print(f"   Room: {booking.assigned_room}")
        
        # Find BookingManagementTokens for this booking (what the frontend currently uses)
        mgmt_tokens = BookingManagementToken.objects.filter(
            booking=booking
        )
        
        print(f"\n🔑 Management tokens: {mgmt_tokens.count()}")
        valid_tokens = [token for token in mgmt_tokens if hasattr(token, 'is_valid') and token.is_valid]
        print(f"🔑 Valid management tokens: {len(valid_tokens)}")
        
        if len(valid_tokens) > 0 or mgmt_tokens.count() > 0:
            # We can't get the raw token, but we can create one for testing
            print("⚠️  Cannot test with real management token (only hash stored)")
            print("   Creating test scenario...")
            
            # Create a test request factory
            factory = RequestFactory()
            
            # Simulate the booking status view call
            view = BookingStatusView()
            request = factory.get(f'/api/public/hotels/{hotel_slug}/booking/status/{booking_id}/?token=test_token')
            
            # Test the helper method directly
            guest_token = view._get_or_create_guest_token(booking)
            
            if guest_token:
                print(f"✅ Guest token generated/found: {type(guest_token)}")
                if guest_token == "TOKEN_EXISTS":
                    print(f"   Token already exists (good!)")
                else:
                    print(f"   New token: {guest_token[:20]}...")
                    
                    # Test that this token works with chat context
                    print(f"\n🧪 Testing guest token with chat context...")
                    from bookings.services import resolve_guest_chat_context
                    
                    try:
                        booking_result, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                            hotel_slug=hotel_slug,
                            token_str=guest_token,
                            required_scopes=["CHAT"],
                            action_required=False
                        )
                        
                        print(f"✅ Chat context test PASSED with new guest token:")
                        print(f"   Booking: {booking_result.booking_id}")
                        print(f"   Room: {room.room_number if room else 'None'}")
                        print(f"   Can Chat: {allowed_actions['can_chat']}")
                        print(f"   Disabled Reason: {disabled_reason}")
                        
                    except Exception as e:
                        print(f"❌ Chat context test FAILED: {e}")
                        
            else:
                print(f"❌ No guest token generated")
            
        else:
            print("❌ No management tokens found")
            
    except RoomBooking.DoesNotExist:
        print(f"❌ Booking {booking_id} not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_booking_status_guest_token()