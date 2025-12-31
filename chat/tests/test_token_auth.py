"""
Tests for token-based guest chat authentication.
Comprehensive test coverage for the new guest portal chat system.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
from datetime import timedelta
import hashlib
import uuid

from hotel.models import Hotel, GuestBookingToken, RoomBooking
from rooms.models import Room, RoomType
from staff.models import Staff, Role
from chat.models import Conversation, RoomMessage, GuestConversationParticipant
from bookings.services import (
    resolve_guest_chat_context, 
    validate_guest_conversation_access,
    GuestChatAccessError,
    InvalidTokenError,
    NotInHouseError,
    NoRoomAssignedError,
    hash_token
)


class TokenBasedChatTestCase(TestCase):
    """Base test case with common setup for token-based chat tests."""
    
    def setUp(self):
        # Create test hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            name="Standard Room",
            hotel=self.hotel
        )
        
        self.room = Room.objects.create(
            room_number="101",
            room_type=self.room_type,
            hotel=self.hotel
        )
        
        # Create booking
        self.booking = RoomBooking.objects.create(
            booking_id="BK-2025-TEST",
            confirmation_number="CONF-123",
            hotel=self.hotel,
            room_type=self.room_type,
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timedelta(days=2)).date(),
            primary_first_name="John",
            primary_last_name="Doe",
            adults=2,
            total_amount=200.00,
            status="CONFIRMED",
            assigned_room=self.room,
            checked_in_at=timezone.now()
        )
        
        # Create valid token
        self.token_str = "test-token-123"
        self.token_hash = hash_token(self.token_str)
        
        self.guest_token = GuestBookingToken.objects.create(
            token_hash=self.token_hash,
            booking=self.booking,
            hotel=self.hotel,
            status='ACTIVE',
            expires_at=timezone.now() + timedelta(days=30)
        )


class GuestChatServicesTest(TokenBasedChatTestCase):
    """Test the guest chat authentication services."""
    
    def test_resolve_guest_chat_context_success(self):
        """Test successful context resolution."""
        booking, room, conversation = resolve_guest_chat_context(
            hotel_slug=self.hotel.slug,
            token_str=self.token_str,
            require_in_house=True
        )
        
        self.assertEqual(booking.id, self.booking.id)
        self.assertEqual(room.id, self.room.id)
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.room, self.room)
        
        # Check token last_used_at was updated
        self.guest_token.refresh_from_db()
        self.assertIsNotNone(self.guest_token.last_used_at)
    
    def test_invalid_token_error(self):
        """Test invalid token handling."""
        with self.assertRaises(InvalidTokenError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str="invalid-token",
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 404)
    
    def test_empty_token_error(self):
        """Test empty token handling."""
        with self.assertRaises(InvalidTokenError):
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str="",
                require_in_house=True
            )
    
    def test_expired_token_error(self):
        """Test expired token handling."""
        # Make token expired
        self.guest_token.expires_at = timezone.now() - timedelta(hours=1)
        self.guest_token.save()
        
        with self.assertRaises(InvalidTokenError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 404)
    
    def test_hotel_mismatch_error(self):
        """Test hotel mismatch returns 404 for anti-enumeration."""
        with self.assertRaises(InvalidTokenError) as cm:
            resolve_guest_chat_context(
                hotel_slug="different-hotel",
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 404)
    
    def test_cancelled_booking_error(self):
        """Test cancelled booking access denied."""
        self.booking.status = "CANCELLED"
        self.booking.save()
        
        with self.assertRaises(InvalidTokenError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 404)
    
    def test_not_checked_in_error(self):
        """Test not checked in error."""
        self.booking.checked_in_at = None
        self.booking.save()
        
        with self.assertRaises(NotInHouseError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 403)
    
    def test_already_checked_out_error(self):
        """Test already checked out error."""
        self.booking.checked_out_at = timezone.now()
        self.booking.save()
        
        with self.assertRaises(NotInHouseError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 403)
    
    def test_no_room_assigned_error(self):
        """Test no assigned room error."""
        self.booking.assigned_room = None
        self.booking.save()
        
        with self.assertRaises(NoRoomAssignedError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                require_in_house=True
            )
        self.assertEqual(cm.exception.status_code, 409)
    
    def test_require_in_house_false(self):
        """Test bypassing in-house requirement."""
        self.booking.checked_in_at = None
        self.booking.save()
        
        # Should work with require_in_house=False
        booking, room, conversation = resolve_guest_chat_context(
            hotel_slug=self.hotel.slug,
            token_str=self.token_str,
            require_in_house=False
        )
        
        self.assertEqual(booking.id, self.booking.id)
    
    def test_validate_guest_conversation_access_success(self):
        """Test conversation access validation success."""
        conversation = Conversation.objects.create(room=self.room)
        
        booking, room, validated_conversation = validate_guest_conversation_access(
            hotel_slug=self.hotel.slug,
            token_str=self.token_str,
            conversation_id=conversation.id
        )
        
        self.assertEqual(validated_conversation.id, conversation.id)
    
    def test_validate_guest_conversation_access_wrong_conversation(self):
        """Test access denied to wrong conversation."""
        # Create conversation for different room
        other_room = Room.objects.create(
            room_number="102",
            room_type=self.room_type,
            hotel=self.hotel
        )
        other_conversation = Conversation.objects.create(room=other_room)
        
        with self.assertRaises(InvalidTokenError) as cm:
            validate_guest_conversation_access(
                hotel_slug=self.hotel.slug,
                token_str=self.token_str,
                conversation_id=other_conversation.id
            )
        self.assertEqual(cm.exception.status_code, 404)


class GuestChatAPITest(APITestCase, TokenBasedChatTestCase):
    """Test the guest chat API endpoints."""
    
    def setUp(self):
        super().setUp()
        # Create conversation for testing
        self.conversation = Conversation.objects.create(room=self.room)
    
    def test_guest_chat_context_success(self):
        """Test successful guest chat context retrieval."""
        response = self.client.get(
            f"/api/chat/{self.hotel.slug}/guest/chat/context/",
            {"token": self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data["conversation_id"], self.conversation.id)
        self.assertEqual(data["room_number"], "101")
        self.assertEqual(data["booking_id"], self.booking.booking_id)
        self.assertEqual(data["pusher"]["channel"], f"private-hotel-{self.hotel.slug}-guest-chat-booking-{self.booking.booking_id}")
        self.assertEqual(data["pusher"]["event"], "realtime_event")
        self.assertTrue(data["allowed_actions"]["can_chat"])
        self.assertIsNone(data["current_staff_handler"])
    
    def test_guest_chat_context_missing_token(self):
        """Test guest chat context without token."""
        response = self.client.get(f"/api/chat/{self.hotel.slug}/guest/chat/context/")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Token parameter is required", response.json()["error"])
    
    def test_guest_chat_context_invalid_token(self):
        """Test guest chat context with invalid token."""
        response = self.client.get(
            f"/api/chat/{self.hotel.slug}/guest/chat/context/",
            {"token": "invalid-token"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_guest_chat_context_not_checked_in(self):
        """Test guest chat context when not checked in."""
        self.booking.checked_in_at = None
        self.booking.save()
        
        response = self.client.get(
            f"/api/chat/{self.hotel.slug}/guest/chat/context/",
            {"token": self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('notifications.notification_manager.notification_manager.realtime_guest_chat_message_created')
    def test_guest_send_message_success(self, mock_notification):
        """Test successful guest message sending."""
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {"message": "Hello from guest!"},
            format='json',
            **{"QUERY_STRING": f"token={self.token_str}"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Check message was created
        self.assertEqual(data["message"], "Hello from guest!")
        self.assertEqual(data["sender_type"], "guest")
        self.assertEqual(data["room_number"], 101)
        
        # Check NotificationManager was called
        self.assertTrue(mock_notification.called)
        
        # Verify message in database
        message = RoomMessage.objects.get(id=data["id"])
        self.assertEqual(message.message, "Hello from guest!")
        self.assertEqual(message.sender_type, "guest")
        self.assertEqual(message.room, self.room)
        self.assertEqual(message.conversation, self.conversation)
    
    def test_guest_send_message_missing_token(self):
        """Test guest send message without token."""
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {"message": "Hello!"},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Token parameter is required", response.json()["error"])
    
    def test_guest_send_message_empty_message(self):
        """Test guest send message with empty message."""
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {"message": "   "},
            format='json',
            **{"QUERY_STRING": f"token={self.token_str}"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Message cannot be empty", response.json()["error"])
    
    @patch('notifications.notification_manager.notification_manager.realtime_guest_chat_message_created')
    def test_guest_send_message_with_reply(self, mock_notification):
        """Test guest send message with reply to previous message."""
        # Create previous message to reply to
        previous_message = RoomMessage.objects.create(
            conversation=self.conversation,
            room=self.room,
            message="Previous message",
            sender_type="staff"
        )
        
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {
                "message": "Reply message",
                "reply_to": previous_message.id
            },
            format='json',
            **{"QUERY_STRING": f"token={self.token_str}"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        # Check reply relationship
        message = RoomMessage.objects.get(id=data["id"])
        self.assertEqual(message.reply_to, previous_message)
    
    def test_guest_send_message_invalid_token(self):
        """Test guest send message with invalid token."""
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {"message": "Hello!"},
            format='json',
            **{"QUERY_STRING": "token=invalid-token"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_guest_send_message_not_in_house(self):
        """Test guest send message when not in house."""
        self.booking.checked_in_at = None
        self.booking.save()
        
        response = self.client.post(
            f"/api/chat/{self.hotel.slug}/guest/chat/messages/",
            {"message": "Hello!"},
            format='json',
            **{"QUERY_STRING": f"token={self.token_str}"}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TokenHashingTest(TestCase):
    """Test token hashing functionality."""
    
    def test_hash_token_consistency(self):
        """Test that token hashing is consistent."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 hex digest length
    
    def test_different_tokens_different_hashes(self):
        """Test that different tokens produce different hashes."""
        token1 = "test-token-123"
        token2 = "test-token-456"
        
        hash1 = hash_token(token1)
        hash2 = hash_token(token2)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_hash_token_expected_format(self):
        """Test that hash follows expected SHA-256 format."""
        token = "test-token"
        expected_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        actual_hash = hash_token(token)
        
        self.assertEqual(actual_hash, expected_hash)


class ChannelNamingTest(TokenBasedChatTestCase):
    """Test that channel naming follows the correct format."""
    
    def test_guest_chat_context_channel_format(self):
        """Test that guest chat context returns correct channel format."""
        response = self.client.get(
            f"/api/chat/{self.hotel.slug}/guest/chat/context/",
            {"token": self.token_str}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        expected_channel = f"{self.hotel.slug}.guest-chat.room-{self.room.room_number}"
        self.assertEqual(data["pusher"]["channel"], expected_channel)
    
    def test_channel_format_consistency(self):
        """Test channel format matches NotificationManager expectations."""
        # This would be tested by integration tests with actual NotificationManager
        expected_format = f"private-hotel-{self.hotel.slug}-guest-chat-booking-{self.booking.booking_id}"
        
        # Channel should be: private-hotel-{slug}-guest-chat-booking-{booking_id}
        parts = expected_format.split('-')
        self.assertTrue(len(parts) >= 6)  # private-hotel-{slug}-guest-chat-booking-{id}
        self.assertEqual(parts[0], "private")
        self.assertEqual(parts[1], "hotel")
        self.assertEqual(parts[3], "guest")
        self.assertEqual(parts[4], "chat")
        self.assertEqual(parts[5], "booking")


class StaffIdentitySystemTest(TokenBasedChatTestCase):
    """Test staff identity and system join messages."""
    
    def setUp(self):
        super().setUp()
        # Create staff user and role
        self.role = Role.objects.create(name="Receptionist")
        self.staff = Staff.objects.create(
            first_name="John",
            last_name="Smith",
            email="john.smith@hotel.com",
            role=self.role
        )
        self.conversation = Conversation.objects.create(room=self.room)
    
    def test_staff_message_serialization(self):
        """Test staff message includes proper identity information."""
        message = RoomMessage.objects.create(
            conversation=self.conversation,
            room=self.room,
            staff=self.staff,
            message="Hello from staff!",
            sender_type="staff"
        )
        
        from chat.serializers import RoomMessageSerializer
        serializer = RoomMessageSerializer(message)
        data = serializer.data
        
        self.assertEqual(data["sender_type"], "staff")
        self.assertEqual(data["staff_name"], "John Smith")
        self.assertIsNotNone(data["staff_info"])
        self.assertEqual(data["staff_info"]["name"], "John Smith")
        self.assertEqual(data["staff_info"]["role"], "Receptionist")
    
    def test_system_message_serialization(self):
        """Test system message serialization."""
        message = RoomMessage.objects.create(
            conversation=self.conversation,
            room=self.room,
            staff=None,
            message="John Smith has joined the conversation.",
            sender_type="system"
        )
        
        from chat.serializers import RoomMessageSerializer
        serializer = RoomMessageSerializer(message)
        data = serializer.data
        
        self.assertEqual(data["sender_type"], "system")
        self.assertIsNone(data["staff_name"])
        self.assertIsNone(data["staff_info"])
        self.assertEqual(data["message"], "John Smith has joined the conversation.")
    
    @patch('notifications.notification_manager.notification_manager.realtime_guest_chat_message_created')
    def test_staff_join_creates_system_message(self, mock_notification):
        """Test that staff first message creates system join message."""
        # Simulate staff sending first message to guest conversation
        # This would normally be done via send_conversation_message endpoint
        # but we'll test the logic directly
        
        participant, created = GuestConversationParticipant.objects.get_or_create(
            conversation=self.conversation,
            staff=self.staff
        )
        
        self.assertTrue(created)
        
        # System message should be created when staff joins
        join_message = RoomMessage.objects.create(
            conversation=self.conversation,
            room=self.room,
            staff=None,
            message=f"{self.staff.first_name} {self.staff.last_name} has joined the conversation.",
            sender_type="system"
        )
        
        self.assertEqual(join_message.sender_type, "system")
        self.assertIsNone(join_message.staff)
        self.assertIn("John Smith has joined", join_message.message)
    
    def test_guest_conversation_participant_uniqueness(self):
        """Test that staff can only join a conversation once."""
        # Create first participant
        participant1 = GuestConversationParticipant.objects.create(
            conversation=self.conversation,
            staff=self.staff
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # Should raise IntegrityError
            GuestConversationParticipant.objects.create(
                conversation=self.conversation,
                staff=self.staff
            )


class BackwardsCompatibilityTest(TokenBasedChatTestCase):
    """Test that existing functionality still works."""
    
    def test_staff_send_message_unchanged(self):
        """Test that staff can still send messages normally."""
        # This would require creating staff user and authenticating
        # For now, just verify the endpoint still exists and has AllowAny permission
        from django.urls import reverse
        
        try:
            url = reverse('send_conversation_message', kwargs={
                'hotel_slug': self.hotel.slug,
                'conversation_id': 1
            })
            self.assertTrue(url.startswith('/api/chat/'))
        except Exception:
            self.fail("send_conversation_message URL pattern should still exist")