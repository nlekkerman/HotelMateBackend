"""
Test Push Notifications - Check FCM tokens and send test notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff
from notifications.fcm_service import send_fcm_notification


def test_push_notifications():
    print("\n" + "="*60)
    print("PUSH NOTIFICATION TEST")
    print("="*60)
    
    # Check which porters have FCM tokens
    porters = Staff.objects.filter(
        role__slug='porter',
        is_active=True
    )
    
    print(f"\n📱 All Porters ({porters.count()}):")
    porters_with_tokens = []
    
    for porter in porters:
        on_duty = "✓ ON DUTY" if porter.is_on_duty else "✗ Off duty"
        if porter.fcm_token:
            token_preview = porter.fcm_token[:20] + "..." if len(porter.fcm_token) > 20 else porter.fcm_token
            print(f"  - {porter.first_name} {porter.last_name} (ID: {porter.id}) - {on_duty}")
            print(f"    ✓ Has FCM token: {token_preview}")
            porters_with_tokens.append(porter)
        else:
            print(f"  - {porter.first_name} {porter.last_name} (ID: {porter.id}) - {on_duty}")
            print(f"    ✗ No FCM token")
    
    if not porters_with_tokens:
        print("\n" + "="*60)
        print("❌ NO FCM TOKENS FOUND")
        print("="*60)
        print("\nNo porters have FCM tokens saved.")
        print("\nTo test push notifications:")
        print("1. Implement Firebase in your React web app")
        print("2. Login as a porter")
        print("3. Grant notification permissions")
        print("4. The app will save the FCM token to backend")
        print("5. Then run this test again")
        print("\nSee: FIREBASE_FCM_REACT_WEB_GUIDE.md")
        return
    
    # Send test notifications
    print("\n" + "="*60)
    print(f"SENDING TEST NOTIFICATIONS ({len(porters_with_tokens)} porters)")
    print("="*60)
    
    for porter in porters_with_tokens:
        print(f"\nSending to {porter.first_name} {porter.last_name}...")
        
        title = "🔔 Test Push Notification"
        body = f"Hello {porter.first_name}! This is a test from the backend."
        data = {
            "type": "test",
            "porter_id": str(porter.id),
            "message": "Backend push notification test"
        }
        
        success = send_fcm_notification(porter.fcm_token, title, body, data)
        
        if success:
            print(f"  ✅ Notification sent successfully!")
        else:
            print(f"  ❌ Failed to send notification")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nCheck your browser for notifications!")
    print("If using Chrome: Look for notification popup or system tray")
    print("If using Firefox: Check notification center")
    print()


if __name__ == '__main__':
    test_push_notifications()
