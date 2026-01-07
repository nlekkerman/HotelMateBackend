#!/usr/bin/env python3
"""
Direct Pusher test script - run with: python debug_pusher_direct.py
"""

import os
import sys
import json
from datetime import datetime

# Add your project to path
sys.path.append('.')

def test_pusher_direct():
    """Test Pusher without Django shell"""
    
    print("🔍 Direct Pusher Debug Test")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path[0]}")
    
    # Try to import pusher directly
    try:
        import pusher
        print("✅ Pusher library is available")
        print(f"Pusher version: {pusher.__version__}")
    except ImportError as e:
        print(f"❌ Pusher library not found: {e}")
        print("Install with: pip install pusher")
        return
    
    # Test with hardcoded credentials (you'll need to add yours)
    # You can find these in your Django settings or Pusher dashboard
    print("\n📊 Testing Pusher Configuration")
    print("Please add your Pusher credentials to this script:")
    
    # REPLACE THESE WITH YOUR ACTUAL VALUES
    PUSHER_APP_ID = "your_app_id"
    PUSHER_KEY = "your_key" 
    PUSHER_SECRET = "your_secret"
    PUSHER_CLUSTER = "your_cluster"  # probably 'us2' or 'eu'
    
    if PUSHER_APP_ID == "your_app_id":
        print("❌ Please update the Pusher credentials in this script first!")
        print("\nYou can find these values in:")
        print("1. Your Django settings.py file")
        print("2. Your Pusher dashboard at https://dashboard.pusher.com/")
        print("3. Your environment variables")
        return
    
    # Initialize Pusher client
    try:
        pusher_client = pusher.Pusher(
            app_id=PUSHER_APP_ID,
            key=PUSHER_KEY,
            secret=PUSHER_SECRET,
            cluster=PUSHER_CLUSTER,
            ssl=True
        )
        print("✅ Pusher client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Pusher client: {e}")
        return
    
    # Test channel (from your logs)
    booking_id = "BK-2026-0001"
    hotel_slug = "hotel-killarney"
    channel_name = f"private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}"
    
    print(f"\n📡 Testing channel: {channel_name}")
    
    # Send test message
    test_data = {
        'type': 'test_message',
        'message': 'This is a test from debug script',
        'booking_id': booking_id,
        'timestamp': datetime.now().isoformat(),
        'sender': 'debug_script',
        'debug': True
    }
    
    try:
        print("📤 Sending test message...")
        result = pusher_client.trigger(channel_name, 'realtime_event', test_data)
        print(f"✅ Message sent successfully!")
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
    
    # Try to get channel info
    try:
        print("\n📊 Getting channel information...")
        channel_info = pusher_client.channel_info(channel_name)
        print(f"Channel info: {json.dumps(channel_info, indent=2)}")
    except Exception as e:
        print(f"⚠️  Could not get channel info: {e}")
    
    print("\n🔍 Direct test complete!")
    print("\nNext steps:")
    print("1. Check your frontend browser console for received messages")
    print("2. Verify your Pusher credentials are correct")
    print("3. Make sure your frontend is subscribed to the correct channel")

if __name__ == "__main__":
    test_pusher_direct()