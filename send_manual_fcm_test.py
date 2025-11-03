"""
Manual FCM Push Notification Test
Sends a test FCM notification to a specific token
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from notifications.fcm_service import send_fcm_notification


def send_manual_fcm_test():
    print("\n" + "="*60)
    print("MANUAL FCM PUSH NOTIFICATION TEST")
    print("="*60)
    
    # Get FCM token from user
    print("\nTo send a test FCM notification, you need an FCM token.")
    print("You can get this from:")
    print("1. Browser console after implementing Firebase in React")
    print("2. Staff profile in Django admin")
    print("3. Database query: Staff.objects.get(id=X).fcm_token")
    
    token = input("\nEnter FCM token (or press Enter to skip): ").strip()
    
    if not token:
        print("\n⚠️  No token provided.")
        print("\nTo get an FCM token:")
        print("1. Implement Firebase in your React web app")
        print("2. Login as a porter")
        print("3. Grant notification permissions")
        print("4. Copy the token from browser console or database")
        return
    
    # Test notification
    print("\n" + "-"*60)
    print("SENDING FCM NOTIFICATION...")
    print("-"*60)
    
    title = "🔔 Test Notification"
    body = "This is a manual FCM test from backend!"
    data = {
        "type": "test",
        "message": "Manual FCM notification test",
        "timestamp": str(django.utils.timezone.now())
    }
    
    success = send_fcm_notification(token, title, body, data)
    
    print("\n" + "="*60)
    if success:
        print("✅ FCM NOTIFICATION SENT SUCCESSFULLY!")
        print("="*60)
        print("\nCheck your browser/device for the notification!")
    else:
        print("❌ FCM NOTIFICATION FAILED")
        print("="*60)
        print("\nPossible reasons:")
        print("- Invalid FCM token")
        print("- Token expired/unregistered")
        print("- Firebase credentials not configured")
        print("- Network issues")
        print("\nCheck the logs above for error details.")
    print()


if __name__ == '__main__':
    send_manual_fcm_test()
