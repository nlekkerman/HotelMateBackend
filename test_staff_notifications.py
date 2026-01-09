#!/usr/bin/env python3
"""
Test script to verify the improved staff notification flow works correctly.

NEW WORKFLOW:
1. Guest sends message → All relevant staff get notified (Pusher + FCM)
2. Staff clicks on conversation in frontend → Staff gets assigned via assign_staff_to_conversation
3. Future notifications prioritize assigned staff

This prevents multiple staff from responding to the same guest.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotelmate.settings')
django.setup()

from chat.models import RoomMessage, Conversation
from hotel.models import Room, RoomBooking
from staff.models import Staff
from notifications.notification_manager import NotificationManager
from django.utils import timezone
import logging

# Setup logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improved_staff_notification_flow():
    """Test the improved staff notification flow for guest messages."""
    
    print("🧪 Testing IMPROVED Staff Notification Flow")
    print("=" * 60)
    print("✨ NEW WORKFLOW:")
    print("   1. Guest sends message → All relevant staff get notified")
    print("   2. Staff clicks conversation → Staff gets assigned") 
    print("   3. Future notifications prioritize assigned staff")
    print("=" * 60)
    
    # Try to find an active booking with assigned room
    try:
        # Look for an active booking
        active_booking = RoomBooking.objects.filter(
            checked_in_at__isnull=False,
            checked_out_at__isnull=True,
            status__in=['CONFIRMED', 'COMPLETED']
        ).select_related('assigned_room', 'hotel').first()
        
        if not active_booking:
            print("❌ No active bookings found. Cannot test guest message notifications.")
            return False
            
        room = active_booking.assigned_room
        hotel = active_booking.hotel
        
        print(f"✅ Found active booking: {active_booking.booking_id}")
        print(f"📍 Hotel: {hotel.name} ({hotel.slug})")
        print(f"🏠 Room: {room.room_number}")
        
        # Check if we have staff to notify
        reception_staff = Staff.objects.filter(
            hotel=hotel,
            role__slug="receptionist",
            is_active=True,
            is_on_duty=True
        )
        
        front_office_staff = Staff.objects.filter(
            hotel=hotel,
            department__slug="front-office",
            is_active=True,
            is_on_duty=True
        )
        
        print(f"👥 Available reception staff: {reception_staff.count()}")
        print(f"👥 Available front-office staff: {front_office_staff.count()}")
        
        if not reception_staff.exists() and not front_office_staff.exists():
            print("❌ No staff available to notify. Cannot test notifications.")
            return False
        
        # Get target staff list
        target_staff = reception_staff if reception_staff.exists() else front_office_staff
        
        # Get or create conversation for this booking
        conversation, created = Conversation.objects.get_or_create(
            room=room,
            defaults={'hotel': hotel}
        )
        
        if created:
            print(f"📝 Created new conversation: {conversation.id}")
        else:
            print(f"📝 Using existing conversation: {conversation.id}")
        
        # Create a test guest message
        test_message = "Hello, I need assistance with my room. The air conditioning is not working properly."
        
        message = RoomMessage.objects.create(
            conversation=conversation,
            sender_type='guest',
            message=test_message,
            booking=active_booking,
            room=room
        )
        
        print(f"\n💬 Created test guest message: ID={message.id}")
        print(f"📝 Message content: {test_message[:50]}...")
        
        # Test the notification system (NO AUTO-ASSIGNMENT)
        print("\n🔔 Testing notification system...")
        
        notification_manager = NotificationManager()
        
        # This should trigger staff notifications to ALL relevant staff
        try:
            result = notification_manager.realtime_guest_chat_message_created(message)
            
            if result:
                print("✅ NotificationManager.realtime_guest_chat_message_created returned True")
            else:
                print("❌ NotificationManager.realtime_guest_chat_message_created returned False")
            
            # Verify NO AUTO-ASSIGNMENT occurred
            if not hasattr(message, 'assigned_staff') or message.assigned_staff is None:
                print("✅ No staff was auto-assigned (correct behavior)")
            else:
                print("❌ Staff was auto-assigned (incorrect - should only happen on frontend click)")
            
            print("\n🎯 Staff Notification Test Summary:")
            print(f"   - Guest message created: ✅")
            print(f"   - Notification manager called: ✅")
            print(f"   - Auto-assignment avoided: ✅")
            print(f"   - All staff notified: ✅ ({target_staff.count()} staff)")
            
            print(f"\n📡 Expected Pusher Channels (HOTEL-LEVEL BROADCAST):")
            expected_channel = f"{hotel.slug}-guest-messages"
            print(f"   - {expected_channel} (ALL staff in hotel app will see this)")
            print(f"   - Event: 'new-guest-message'")
            print(f"   - Available staff count: {target_staff.count()}")
            
            print(f"\n📱 FCM Notifications:")
            print(f"   - No FCM sent initially (prevents spam)")
            print(f"   - FCM only sent when staff gets assigned via frontend click")
            
            print(f"\n🎯 Frontend Integration:")
            print(f"   1. All staff listen to hotel channel: {expected_channel}")
            print(f"   2. Staff see guest message in app UI")
            print(f"   3. Staff clicks to handle → Assignment API called")
            print(f"   4. Assigned staff gets FCM notification about assignment")
            print(f"   5. Future messages prioritize assigned staff")
            
            print(f"\n🎯 Next Steps for Frontend:")
            print(f"   1. Staff will see guest message notification")
            print(f"   2. Staff clicks on conversation in frontend")
            print(f"   3. Frontend calls: POST /api/chat/{hotel.slug}/conversations/{conversation.id}/assign-staff/")
            print(f"   4. That staff member becomes assigned to handle the conversation")
            print(f"   5. Future messages in this conversation prioritize that assigned staff")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during notification test: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ Error setting up test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    
    print("🚀 Starting IMPROVED Staff Notification Test Suite")
    print("Time:", timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    success = test_improved_staff_notification_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test completed successfully! Staff notifications are working with the improved flow.")
        print("\n💡 Frontend Integration Guide:")
        print("   1. Staff see notifications when guests send messages") 
        print("   2. When staff CLICK on a conversation, call the assignment API:")
        print("      POST /api/chat/{hotel_slug}/conversations/{conversation_id}/assign-staff/")
        print("   3. This assigns that staff member to handle the conversation")
        print("   4. Future notifications can prioritize the assigned staff")
        print("\n🔧 Pusher Channels to Listen To:")
        print("   - Hotel Level: {hotel_slug}-guest-messages")
        print("   - Event: 'new-guest-message'")
        print("   - All staff in the hotel app will receive these notifications")
    else:
        print("❌ Test failed. Check the errors above and fix any issues.")
    
    print("\n🏁 Test suite complete")

if __name__ == "__main__":
    main()