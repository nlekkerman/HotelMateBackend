#!/usr/bin/env python3
"""
Quick Pusher debug script
Run this in your Django shell: python manage.py shell < debug_pusher_quick.py
"""

# Test Pusher manually
booking_id = "BK-2026-0001"
hotel_slug = "hotel-killarney"

print("🔍 Quick Pusher Debug")
print(f"Booking ID: {booking_id}")
print(f"Hotel: {hotel_slug}")

# Try to import Pusher settings
try:
    from django.conf import settings
    print("✅ Django settings loaded")
    
    # Check if Pusher settings exist
    pusher_attrs = [attr for attr in dir(settings) if 'PUSHER' in attr]
    print(f"📊 Pusher settings found: {pusher_attrs}")
    
    for attr in pusher_attrs:
        value = getattr(settings, attr, 'NOT_SET')
        # Don't print secret values
        if 'SECRET' in attr:
            value = '***' if value != 'NOT_SET' else 'NOT_SET'
        print(f"  {attr}: {value}")
        
except ImportError as e:
    print(f"❌ Could not import Django settings: {e}")

# Try to send a test message using your notification system
try:
    # Import your notification manager (adjust import path)
    from notifications.notification_manager import NotificationManager
    
    print("✅ NotificationManager imported")
    
    # Create test message data
    test_data = {
        'type': 'debug_test',
        'message': 'Debug test message',
        'booking_id': booking_id,
        'timestamp': '2026-01-07T11:30:00Z'
    }
    
    # Try to trigger notification
    channel = f'private-hotel-{hotel_slug}-guest-chat-booking-{booking_id}'
    print(f"📡 Sending to channel: {channel}")
    
    # This might need adjustment based on your NotificationManager implementation
    # notification_manager = NotificationManager()
    # result = notification_manager.send_pusher_event(channel, 'realtime_event', test_data)
    # print(f"✅ Test notification sent: {result}")
    
except ImportError as e:
    print(f"⚠️  Could not import NotificationManager: {e}")
except Exception as e:
    print(f"❌ Error sending test notification: {e}")

print("🔍 Quick debug complete!")