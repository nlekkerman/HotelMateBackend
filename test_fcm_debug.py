#!/usr/bin/env python3
"""
Quick FCM debugging script
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff
from notifications.fcm_service import send_fcm_notification

def test_fcm():
    print("🔍 FCM Debug Test")
    print("=" * 50)
    
    # Find staff with ID 35 (from your logs)
    try:
        staff = Staff.objects.get(id=35)
        print(f"📋 Staff found: {staff.first_name} {staff.last_name}")
        print(f"📧 Email: {staff.email}")
        
        if staff.fcm_token:
            print(f"📱 FCM Token: {staff.fcm_token[:50]}...")
            print(f"📱 Token Length: {len(staff.fcm_token)} chars")
            
            # Send test notification
            print("\n🚀 Sending test FCM notification...")
            result = send_fcm_notification(
                token=staff.fcm_token,
                title="🔥 FCM Test",
                body="This is a test notification to debug FCM",
                data={
                    'type': 'test',
                    'test_id': '123',
                    'hotel_slug': 'hotel-killarney'
                }
            )
            
            if result:
                print("✅ FCM test notification sent successfully!")
            else:
                print("❌ FCM test notification FAILED!")
                
        else:
            print("❌ No FCM token found for this staff member!")
            print("💡 This means the app hasn't registered for push notifications")
            
    except Staff.DoesNotExist:
        print("❌ Staff with ID 35 not found")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_fcm()