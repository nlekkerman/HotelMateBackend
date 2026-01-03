#!/usr/bin/env python
"""
Check if the frontend token e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0
matches the database token hash 2832bba5a6df6f4595eb1013bb36b19db46827f5da370d6a8f33d4a572efa846
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from bookings.services import hash_token

def check_token_match():
    # Frontend token from logs
    frontend_token = "e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0"
    
    # Database hash from our previous query
    database_hash = "2832bba5a6df6f4595eb1013bb36b19db46827f5da370d6a8f33d4a572efa846"
    
    # Hash the frontend token
    frontend_hash = hash_token(frontend_token)
    
    print(f"🔍 Frontend token: {frontend_token}")
    print(f"🔍 Frontend hash:  {frontend_hash}")
    print(f"🔍 Database hash:  {database_hash}")
    print(f"🔍 Match: {frontend_hash == database_hash}")
    
    if frontend_hash == database_hash:
        print("✅ SAME TOKEN! The frontend token IS the correct token!")
        print("❓ So why is it returning 401?")
        
        # Test the token resolution directly
        print(f"\n🧪 Testing resolve_guest_chat_context directly...")
        try:
            from bookings.services import resolve_guest_chat_context
            
            booking, room, conversation, allowed_actions, disabled_reason = resolve_guest_chat_context(
                hotel_slug="hotel-killarney",
                token_str=frontend_token,
                required_scopes=["CHAT"],
                action_required=False
            )
            
            print(f"✅ Direct resolve_guest_chat_context worked!")
            print(f"   Booking: {booking.booking_id}")
            print(f"   Room: {room.room_number if room else 'None'}")
            print(f"   Can Chat: {allowed_actions['can_chat']}")
            print(f"   Disabled Reason: {disabled_reason}")
            
        except Exception as e:
            print(f"❌ Direct resolve_guest_chat_context failed: {e}")
            import traceback
            traceback.print_exc()
            
    else:
        print("❌ DIFFERENT TOKENS! Frontend token doesn't match database.")

if __name__ == "__main__":
    check_token_match()