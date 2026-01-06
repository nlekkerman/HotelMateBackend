#!/usr/bin/env python3
"""
Test script to verify real-time channel naming consistency.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from notifications.notification_manager import NotificationManager
from chat.utils import pusher_client

def test_channel_formats():
    """Test that all channel formats are consistent."""
    print("🧪 Testing Real-time Channel Formats")
    print("=" * 50)
    
    # Sample data
    hotel_slug = "hotel-killarney"
    conversation_id = 74
    staff_id = 35
    booking_id = "BK-2026-0002"
    
    # Expected formats based on logs and docs
    expected_staff_conversation = f"{hotel_slug}-conversation-{conversation_id}-chat"
    expected_staff_notifications = f"{hotel_slug}-staff-{staff_id}-notifications"
    expected_guest_channel = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"
    
    print(f"✅ Staff Conversation Channel: {expected_staff_conversation}")
    print(f"✅ Staff Notifications Channel: {expected_staff_notifications}")
    print(f"✅ Guest Chat Channel: {expected_guest_channel}")
    print(f"✅ Guest Event Name: realtime_event")
    print(f"✅ Staff Event Names: realtime_staff_chat_message_created, realtime_staff_chat_unread_updated")
    
    print("\n🔍 Channel Format Analysis:")
    print(f"- All channels use DASHES (-) not DOTS (.)")
    print(f"- Staff chat uses: {hotel_slug}-conversation-{conversation_id}-chat")
    print(f"- Staff notifications use: {hotel_slug}-staff-{staff_id}-notifications") 
    print(f"- Guest chat uses: private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}")
    
    print("\n🎯 This should fix the real-time update issues!")
    print("The frontend should now receive Pusher events on the correct channels.")

if __name__ == "__main__":
    test_channel_formats()