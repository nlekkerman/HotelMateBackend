"""
Test Script for Staff Chat Pusher and FCM Notifications
Run: python test_staff_chat_notifications.py
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff_chat.models import StaffConversation, StaffChatMessage
from staff.models import Staff
from hotel.models import Hotel
from django.contrib.auth.models import User
from staff_chat.pusher_utils import (
    broadcast_new_message,
    broadcast_read_receipt,
    get_conversation_channel,
    get_staff_personal_channel
)
from staff_chat.fcm_utils import (
    send_new_message_notification,
    send_mention_notification,
    notify_conversation_participants
)
from chat.utils import pusher_client
from django.conf import settings
import json


def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_pusher_configuration():
    """Test Pusher configuration"""
    print_section("1. PUSHER CONFIGURATION")
    
    try:
        print(f"✓ Pusher App ID: {settings.PUSHER_APP_ID}")
        print(f"✓ Pusher Key: {settings.PUSHER_KEY[:10]}...")
        print(f"✓ Pusher Cluster: {settings.PUSHER_CLUSTER}")
        print(f"✓ SSL Enabled: True")
        
        # Test pusher client
        print(f"\n✓ Pusher client initialized: {pusher_client}")
        return True
    except Exception as e:
        print(f"✗ Pusher configuration error: {e}")
        return False


def test_fcm_configuration():
    """Test FCM configuration"""
    print_section("2. FCM CONFIGURATION")
    
    try:
        from notifications.fcm_service import send_fcm_notification
        print("✓ FCM service module imported successfully")
        
        # Check if Firebase credentials exist
        if hasattr(settings, 'FIREBASE_CREDENTIALS'):
            print("✓ Firebase credentials configured")
        else:
            print("⚠ Firebase credentials not found in settings")
        
        return True
    except Exception as e:
        print(f"✗ FCM configuration error: {e}")
        return False


def test_database_setup():
    """Test database has necessary data"""
    print_section("3. DATABASE SETUP")
    
    try:
        # Check hotels
        hotels = Hotel.objects.all()
        print(f"✓ Found {hotels.count()} hotel(s)")
        for hotel in hotels[:3]:
            print(f"  - {hotel.name} (slug: {hotel.slug})")
        
        # Check staff
        staff = Staff.objects.all()
        print(f"\n✓ Found {staff.count()} staff member(s)")
        for s in staff[:3]:
            print(f"  - {s.first_name} {s.last_name} (Hotel: {s.hotel.name})")
            print(f"    FCM Token: {'✓ Set' if s.fcm_token else '✗ Not set'}")
        
        # Check conversations
        conversations = StaffConversation.objects.all()
        print(f"\n✓ Found {conversations.count()} conversation(s)")
        
        # Check messages
        messages = StaffChatMessage.objects.all()
        print(f"✓ Found {messages.count()} message(s)")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def test_pusher_channels():
    """Test Pusher channel naming"""
    print_section("4. PUSHER CHANNELS")
    
    try:
        hotel_slug = "test-hotel"
        conversation_id = 1
        staff_id = 1
        
        conv_channel = get_conversation_channel(hotel_slug, conversation_id)
        print(f"✓ Conversation channel: {conv_channel}")
        print(f"  Expected format: {hotel_slug}-staff-conversation-{conversation_id}")
        
        staff_channel = get_staff_personal_channel(hotel_slug, staff_id)
        print(f"\n✓ Staff personal channel: {staff_channel}")
        print(f"  Expected format: {hotel_slug}-staff-{staff_id}-notifications")
        
        return True
    except Exception as e:
        print(f"✗ Channel naming error: {e}")
        return False


def test_pusher_broadcast():
    """Test actual Pusher broadcasting"""
    print_section("5. PUSHER BROADCAST TEST")
    
    try:
        # Get a real hotel
        hotel = Hotel.objects.first()
        if not hotel:
            print("✗ No hotel found in database")
            return False
        
        test_channel = f"{hotel.slug}-staff-test-channel"
        test_event = "test-event"
        test_data = {
            "message": "Test broadcast from staff chat",
            "timestamp": "2025-11-12T10:30:00Z",
            "test": True
        }
        
        print(f"Broadcasting to channel: {test_channel}")
        print(f"Event: {test_event}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        # Attempt broadcast
        response = pusher_client.trigger(test_channel, test_event, test_data)
        
        if response:
            print(f"\n✓ Pusher broadcast successful!")
            print(f"  Response: {response}")
        else:
            print(f"\n✗ Pusher broadcast returned None/False")
            print(f"  This might indicate a configuration issue")
        
        return True
    except Exception as e:
        print(f"✗ Pusher broadcast error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_broadcast():
    """Test broadcasting a real message"""
    print_section("6. MESSAGE BROADCAST TEST")
    
    try:
        # Get a real conversation
        conversation = StaffConversation.objects.first()
        if not conversation:
            print("✗ No conversation found in database")
            return False
        
        message = conversation.messages.first()
        if not message:
            print("✗ No message found in conversation")
            return False
        
        hotel_slug = conversation.hotel.slug
        
        # Create test message data
        message_data = {
            "id": message.id,
            "sender_info": {
                "id": message.sender.id,
                "name": f"{message.sender.first_name} {message.sender.last_name}",
            },
            "message": "Test broadcast message",
            "timestamp": "2025-11-12T10:30:00Z",
        }
        
        print(f"Broadcasting to: {hotel_slug}-staff-conversation-{conversation.id}")
        print(f"Message data: {json.dumps(message_data, indent=2)}")
        
        result = broadcast_new_message(
            hotel_slug,
            conversation.id,
            message_data
        )
        
        if result:
            print("\n✓ Message broadcast successful!")
        else:
            print("\n✗ Message broadcast failed")
        
        return result
    except Exception as e:
        print(f"✗ Message broadcast error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_read_receipt_broadcast():
    """Test broadcasting read receipts"""
    print_section("7. READ RECEIPT BROADCAST TEST")
    
    try:
        conversation = StaffConversation.objects.first()
        if not conversation:
            print("✗ No conversation found")
            return False
        
        staff = conversation.participants.first()
        if not staff:
            print("✗ No staff found in conversation")
            return False
        
        hotel_slug = conversation.hotel.slug
        
        read_data = {
            "staff_id": staff.id,
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "message_ids": [1, 2, 3],
            "timestamp": "2025-11-12T10:30:00Z"
        }
        
        print(f"Broadcasting read receipt to: {hotel_slug}-staff-conversation-{conversation.id}")
        print(f"Read data: {json.dumps(read_data, indent=2)}")
        
        from staff_chat.pusher_utils import broadcast_read_receipt
        result = broadcast_read_receipt(
            hotel_slug,
            conversation.id,
            read_data
        )
        
        if result:
            print("\n✓ Read receipt broadcast successful!")
        else:
            print("\n✗ Read receipt broadcast failed")
        
        return result
    except Exception as e:
        print(f"✗ Read receipt broadcast error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fcm_notification():
    """Test FCM notification sending"""
    print_section("8. FCM NOTIFICATION TEST")
    
    try:
        # Find a staff member with FCM token
        staff_with_token = Staff.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='').first()
        
        if not staff_with_token:
            print("⚠ No staff member has FCM token set")
            print("  To test FCM, set a staff member's fcm_token in the database")
            return False
        
        print(f"✓ Found staff with FCM token: {staff_with_token.first_name} {staff_with_token.last_name}")
        print(f"  Token: {staff_with_token.fcm_token[:20]}...")
        
        # Find or create a conversation
        conversation = StaffConversation.objects.filter(
            participants=staff_with_token
        ).first()
        
        if not conversation:
            print("✗ No conversation found for this staff member")
            return False
        
        # Create a mock sender
        sender = conversation.participants.exclude(id=staff_with_token.id).first()
        if not sender:
            sender = conversation.participants.first()
        
        print(f"\nAttempting to send FCM notification...")
        print(f"  To: {staff_with_token.first_name} {staff_with_token.last_name}")
        print(f"  From: {sender.first_name} {sender.last_name}")
        print(f"  Conversation: {conversation.id}")
        
        # Test message notification
        result = send_new_message_notification(
            recipient_staff=staff_with_token,
            sender_staff=sender,
            conversation=conversation,
            message_text="Test message from staff chat notification test"
        )
        
        if result:
            print("\n✓ FCM notification sent successfully!")
        else:
            print("\n✗ FCM notification failed to send")
            print("  Check FCM service configuration and token validity")
        
        return result
    except Exception as e:
        print(f"✗ FCM notification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mention_notification():
    """Test FCM mention notification"""
    print_section("9. FCM MENTION NOTIFICATION TEST")
    
    try:
        staff_with_token = Staff.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='').first()
        
        if not staff_with_token:
            print("⚠ No staff member has FCM token set")
            return False
        
        conversation = StaffConversation.objects.filter(
            participants=staff_with_token
        ).first()
        
        if not conversation:
            print("✗ No conversation found")
            return False
        
        sender = conversation.participants.exclude(id=staff_with_token.id).first()
        if not sender:
            sender = conversation.participants.first()
        
        print(f"Sending mention notification...")
        print(f"  Mentioned: {staff_with_token.first_name} {staff_with_token.last_name}")
        print(f"  From: {sender.first_name} {sender.last_name}")
        
        result = send_mention_notification(
            mentioned_staff=staff_with_token,
            sender_staff=sender,
            conversation=conversation,
            message_text=f"Hey @{staff_with_token.first_name}, check this out!"
        )
        
        if result:
            print("\n✓ Mention notification sent successfully!")
        else:
            print("\n✗ Mention notification failed")
        
        return result
    except Exception as e:
        print(f"✗ Mention notification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Staff chat notifications are working!")
    else:
        print("\n⚠ Some tests failed. Check the output above for details.")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  STAFF CHAT NOTIFICATION SYSTEM TEST")
    print("="*60)
    print("\nThis script will test:")
    print("  1. Pusher configuration")
    print("  2. FCM configuration")
    print("  3. Database setup")
    print("  4. Pusher channel naming")
    print("  5. Pusher broadcast functionality")
    print("  6. Message broadcasting")
    print("  7. Read receipt broadcasting")
    print("  8. FCM message notifications")
    print("  9. FCM mention notifications")
    
    input("\nPress Enter to continue...")
    
    results = {}
    
    # Run tests
    results["Pusher Configuration"] = test_pusher_configuration()
    results["FCM Configuration"] = test_fcm_configuration()
    results["Database Setup"] = test_database_setup()
    results["Pusher Channels"] = test_pusher_channels()
    results["Pusher Broadcast"] = test_pusher_broadcast()
    results["Message Broadcast"] = test_message_broadcast()
    results["Read Receipt Broadcast"] = test_read_receipt_broadcast()
    results["FCM Message Notification"] = test_fcm_notification()
    results["FCM Mention Notification"] = test_mention_notification()
    
    # Print summary
    print_summary(results)
    
    print("\n" + "="*60)
    print("  TROUBLESHOOTING TIPS")
    print("="*60)
    print("""
If Pusher tests failed:
  1. Check PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET in settings
  2. Verify Pusher cluster is correct
  3. Check Pusher dashboard for errors
  4. Ensure pusher-python library is installed

If FCM tests failed:
  1. Check Firebase credentials in settings
  2. Verify FCM tokens are valid in database
  3. Test FCM tokens haven't expired
  4. Check Firebase console for errors
  5. Ensure staff members have fcm_token set

To set FCM token for testing:
  python manage.py shell
  >>> from staff.models import Staff
  >>> staff = Staff.objects.first()
  >>> staff.fcm_token = 'your-test-token'
  >>> staff.save()

To view Pusher events in real-time:
  - Go to Pusher Dashboard
  - Select your app
  - Go to "Debug Console"
  - Watch for events as they're broadcast
""")


if __name__ == "__main__":
    main()
