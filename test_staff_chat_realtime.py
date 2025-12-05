#!/usr/bin/env python
"""
Test script to verify staff chat realtime events are properly firing through NotificationManager.

This script tests:
1. New message creation realtime events
2. Message read receipt realtime events  
3. Message delivered status realtime events
4. Message editing realtime events

Usage:
    python test_staff_chat_realtime.py
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User
from staff.models import Staff, Hotel, Department, Role
from staff_chat.models import StaffConversation, StaffChatMessage
from notifications.notification_manager import notification_manager
from unittest.mock import patch, MagicMock
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_test_data():
    """Set up test hotel, staff, and conversation for testing."""
    print("🔧 Setting up test data...")
    
    # Get or create test hotel
    hotel, created = Hotel.objects.get_or_create(
        slug='test-hotel',
        defaults={'name': 'Test Hotel', 'location': 'Test City'}
    )
    
    # Get or create test department and role
    department, _ = Department.objects.get_or_create(
        slug='front-office',
        defaults={'name': 'Front Office'}
    )
    
    role, _ = Role.objects.get_or_create(
        slug='staff',
        defaults={'name': 'Staff', 'department': department}
    )
    
    # Get or create test users and staff
    user1, created = User.objects.get_or_create(
        username='test_staff_1',
        defaults={'first_name': 'Test', 'last_name': 'Staff One', 'is_staff': True}
    )
    
    user2, created = User.objects.get_or_create(
        username='test_staff_2', 
        defaults={'first_name': 'Test', 'last_name': 'Staff Two', 'is_staff': True}
    )
    
    staff1, _ = Staff.objects.get_or_create(
        user=user1,
        hotel=hotel,
        defaults={
            'first_name': 'Test',
            'last_name': 'Staff One',
            'department': department,
            'role': role,
            'access_level': 'regular_staff'
        }
    )
    
    staff2, _ = Staff.objects.get_or_create(
        user=user2,
        hotel=hotel,
        defaults={
            'first_name': 'Test', 
            'last_name': 'Staff Two',
            'department': department,
            'role': role,
            'access_level': 'regular_staff'
        }
    )
    
    # Create or get test conversation
    conversation, created = StaffConversation.objects.get_or_create(
        hotel=hotel,
        title='Test Conversation',
        defaults={'conversation_type': 'group'}
    )
    
    # Add participants
    conversation.participants.add(staff1, staff2)
    
    print(f"✅ Test data ready: Hotel={hotel.name}, Staff1={staff1}, Staff2={staff2}, Conversation={conversation.id}")
    return hotel, staff1, staff2, conversation

def test_new_message_realtime():
    """Test that new staff chat messages trigger realtime events."""
    print("\n🧪 Testing new message realtime events...")
    
    hotel, staff1, staff2, conversation = setup_test_data()
    
    # Mock the Pusher trigger to capture what events are sent
    with patch.object(notification_manager, '_safe_pusher_trigger') as mock_trigger:
        mock_trigger.return_value = True
        
        # Create a new message
        message = StaffChatMessage.objects.create(
            conversation=conversation,
            sender=staff1,
            message="Test message for realtime events"
        )
        
        # Trigger the realtime event
        result = notification_manager.realtime_staff_chat_message_created(message)
        
        # Verify the event was triggered
        assert mock_trigger.called, "❌ Pusher trigger was not called for new message"
        
        # Check the call details
        call_args = mock_trigger.call_args
        channel, event, data = call_args[0]
        
        print(f"📡 Channel: {channel}")
        print(f"📡 Event: {event}")
        print(f"📡 Data keys: {list(data.keys())}")
        
        # Verify channel format
        expected_channel = f"hotel-{hotel.slug}.staff-chat.{conversation.id}"
        assert channel == expected_channel, f"❌ Wrong channel: expected {expected_channel}, got {channel}"
        
        # Verify event type
        assert event == "message_created", f"❌ Wrong event: expected 'message_created', got {event}"
        
        # Verify payload structure
        assert 'payload' in data, "❌ Missing payload in event data"
        payload = data['payload']
        
        required_fields = ['conversation_id', 'message_id', 'sender_id', 'sender_name', 'text']
        for field in required_fields:
            assert field in payload, f"❌ Missing field '{field}' in payload"
        
        print("✅ New message realtime event test passed!")
        return True

def test_read_receipt_realtime():
    """Test that message read receipts trigger realtime events."""
    print("\n🧪 Testing read receipt realtime events...")
    
    hotel, staff1, staff2, conversation = setup_test_data()
    
    # Create a message from staff1
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=staff1,
        message="Test message for read receipt"
    )
    
    # Mock the Pusher trigger
    with patch.object(notification_manager, '_safe_pusher_trigger') as mock_trigger:
        mock_trigger.return_value = True
        
        # Trigger read receipt for staff2 reading the message
        result = notification_manager.realtime_staff_chat_message_read(
            conversation, staff2, [message.id]
        )
        
        # Verify the event was triggered
        assert mock_trigger.called, "❌ Pusher trigger was not called for read receipt"
        
        call_args = mock_trigger.call_args
        channel, event, data = call_args[0]
        
        print(f"📡 Channel: {channel}")
        print(f"📡 Event: {event}")
        print(f"📡 Data keys: {list(data.keys())}")
        
        # Verify event details
        expected_channel = f"hotel-{hotel.slug}.staff-chat.{conversation.id}"
        assert channel == expected_channel, f"❌ Wrong channel for read receipt"
        assert event == "messages-read", f"❌ Wrong event type for read receipt"
        
        # Verify payload
        payload = data['payload']
        assert 'message_ids' in payload, "❌ Missing message_ids in read receipt payload"
        assert 'read_by_staff_id' in payload, "❌ Missing read_by_staff_id in read receipt payload"
        assert payload['message_ids'] == [message.id], "❌ Wrong message IDs in read receipt"
        assert payload['read_by_staff_id'] == staff2.id, "❌ Wrong staff ID in read receipt"
        
        print("✅ Read receipt realtime event test passed!")
        return True

def test_delivered_status_realtime():
    """Test that message delivered status triggers realtime events."""
    print("\n🧪 Testing delivered status realtime events...")
    
    hotel, staff1, staff2, conversation = setup_test_data()
    
    # Create a message from staff1
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=staff1,
        message="Test message for delivered status"
    )
    
    # Mock the Pusher trigger
    with patch.object(notification_manager, '_safe_pusher_trigger') as mock_trigger:
        mock_trigger.return_value = True
        
        # Trigger delivered status for staff2
        result = notification_manager.realtime_staff_chat_message_delivered(message, staff2)
        
        # Verify the event was triggered
        assert mock_trigger.called, "❌ Pusher trigger was not called for delivered status"
        
        call_args = mock_trigger.call_args
        channel, event, data = call_args[0]
        
        print(f"📡 Channel: {channel}")
        print(f"📡 Event: {event}")
        print(f"📡 Data keys: {list(data.keys())}")
        
        # Verify event details
        expected_channel = f"hotel-{hotel.slug}.staff-chat.{conversation.id}"
        assert channel == expected_channel, f"❌ Wrong channel for delivered status"
        assert event == "message-delivered", f"❌ Wrong event type for delivered status"
        
        # Verify payload
        payload = data['payload']
        assert 'message_id' in payload, "❌ Missing message_id in delivered payload"
        assert 'delivered_to_staff_id' in payload, "❌ Missing delivered_to_staff_id in payload"
        assert payload['message_id'] == message.id, "❌ Wrong message ID in delivered status"
        assert payload['delivered_to_staff_id'] == staff2.id, "❌ Wrong staff ID in delivered status"
        
        print("✅ Delivered status realtime event test passed!")
        return True

def test_message_edited_realtime():
    """Test that message edits trigger realtime events."""
    print("\n🧪 Testing message edit realtime events...")
    
    hotel, staff1, staff2, conversation = setup_test_data()
    
    # Create and edit a message
    message = StaffChatMessage.objects.create(
        conversation=conversation,
        sender=staff1,
        message="Original message"
    )
    
    # Update the message
    message.message = "Edited message"
    message.save()
    
    # Mock the Pusher trigger
    with patch.object(notification_manager, '_safe_pusher_trigger') as mock_trigger:
        mock_trigger.return_value = True
        
        # Trigger edit event
        result = notification_manager.realtime_staff_chat_message_edited(message)
        
        # Verify the event was triggered
        assert mock_trigger.called, "❌ Pusher trigger was not called for message edit"
        
        call_args = mock_trigger.call_args
        channel, event, data = call_args[0]
        
        print(f"📡 Channel: {channel}")
        print(f"📡 Event: {event}")
        print(f"📡 Data keys: {list(data.keys())}")
        
        # Verify event details
        expected_channel = f"hotel-{hotel.slug}.staff-chat.{conversation.id}"
        assert channel == expected_channel, f"❌ Wrong channel for message edit"
        assert event == "message_edited", f"❌ Wrong event type for message edit"
        
        # Verify payload
        payload = data['payload']
        assert 'message_id' in payload, "❌ Missing message_id in edit payload"
        assert 'text' in payload, "❌ Missing text in edit payload"
        assert payload['message_id'] == message.id, "❌ Wrong message ID in edit event"
        assert payload['text'] == "Edited message", "❌ Wrong text in edit event"
        
        print("✅ Message edit realtime event test passed!")
        return True

def run_all_tests():
    """Run all staff chat realtime tests."""
    print("🚀 Starting Staff Chat Realtime Event Tests")
    print("=" * 60)
    
    tests = [
        test_new_message_realtime,
        test_read_receipt_realtime,
        test_delivered_status_realtime,
        test_message_edited_realtime
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All staff chat realtime tests passed!")
        print("\n✅ CONFIRMED: Staff-to-staff chat realtime events are working:")
        print("   • New messages fire realtime events ✓")
        print("   • Read receipts (seen status) fire realtime events ✓") 
        print("   • Delivery status fires realtime events ✓")
        print("   • Message edits fire realtime events ✓")
        print("   • All events use unified NotificationManager ✓")
    else:
        print(f"⚠️ {failed} test(s) failed - check the issues above")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)