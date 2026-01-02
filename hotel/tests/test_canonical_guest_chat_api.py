"""
Tests for Canonical Guest Chat API

Covers token validation, scope enforcement, pre-checkin UX flows, 
booking-scoped pusher channels, and verification that legacy routes 
are completely removed.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import json

from hotel.models import Hotel, RoomBooking, GuestBookingToken
from rooms.models import Room, RoomType
from chat.models import Conversation, RoomMessage
from bookings.services import hash_token


class CanonicalGuestChatAPITest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )
        
        # Create room type and room
        self.room_type = RoomType.objects.create(
            name="Standard Room",
            hotel=self.hotel,
            capacity=2
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number="101",
            room_type=self.room_type
        )
        
        # Create booking
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="BK-2026-0001",
            primary_guest_name="John Doe",
            primary_email="john@example.com",
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            status="CONFIRMED",
            assigned_room=self.room
        )
        
        # Create token with CHAT scope
        self.token_str = "test-token-123"
        self.guest_token = GuestBookingToken.objects.create(
            booking=self.booking,
            hotel=self.hotel,
            token_hash=hash_token(self.token_str),
            status='ACTIVE',
            scopes=['CHAT', 'STATUS_READ']
        )
        
        # Create token without CHAT scope
        self.no_chat_token_str = "no-chat-token-456"
        self.no_chat_token = GuestBookingToken.objects.create(
            booking=self.booking,
            hotel=self.hotel,
            token_hash=hash_token(self.no_chat_token_str),
            status='ACTIVE',
            scopes=['STATUS_READ']  # Missing CHAT scope
        )
        
        # URLs
        self.context_url = f"/api/guest/hotel/{self.hotel.slug}/chat/context"
        self.messages_url = f"/api/guest/hotel/{self.hotel.slug}/chat/messages"
    
    def test_context_endpoint_success_checked_in(self):
        """Test context endpoint returns correct data for checked-in guest"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        response = self.client.get(
            self.context_url,
            {'token': self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response structure
        self.assertIn('conversation_id', data)
        self.assertEqual(data['booking_id'], "BK-2026-0001")
        self.assertEqual(data['room_number'], "101")
        self.assertEqual(data['assigned_room_id'], self.room.id)
        self.assertEqual(data['allowed_actions'], ["chat"])
        
        # Verify booking-scoped pusher channel
        expected_channel = f"private-hotel-{self.hotel.slug}-guest-chat-booking-{self.booking.booking_id}"
        self.assertEqual(data['pusher']['channel'], expected_channel)
        self.assertEqual(data['pusher']['event'], "realtime_event")
        
        # Should not have disabled_reason for checked-in guest
        self.assertNotIn('disabled_reason', data)
    
    def test_context_endpoint_pre_checkin_ux_friendly(self):
        """Test context endpoint returns UX-friendly response for pre-checkin guest"""
        # Guest not checked in yet
        self.booking.checked_in_at = None
        self.booking.status = "CONFIRMED"
        self.booking.save()
        
        response = self.client.get(
            self.context_url,
            {'token': self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return context but with disabled chat
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Check-in required to access chat")
        self.assertIn('conversation_id', data)  # Still provides context
        self.assertIn('pusher', data)  # Still provides pusher channel
    
    def test_context_endpoint_post_checkout_ux_friendly(self):
        """Test context endpoint for checked-out guest"""
        # Guest checked out
        self.booking.checked_in_at = timezone.now() - timezone.timedelta(days=1)
        self.booking.checked_out_at = timezone.now()
        self.booking.status = "CHECKED_OUT"
        self.booking.save()
        
        response = self.client.get(
            self.context_url,
            {'token': self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Chat unavailable after checkout")
    
    def test_context_endpoint_no_room_assigned(self):
        """Test context endpoint when no room assigned"""
        # Remove room assignment
        self.booking.assigned_room = None
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        response = self.client.get(
            self.context_url,
            {'token': self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Room assignment required")
        self.assertIsNone(data['room_number'])
        self.assertIsNone(data['assigned_room_id'])
    
    def test_context_endpoint_missing_token(self):
        """Test context endpoint with missing token"""
        response = self.client.get(self.context_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Token is required', response.json()['error'])
    
    def test_context_endpoint_invalid_token(self):
        """Test context endpoint with invalid token (anti-enumeration)"""
        response = self.client.get(
            self.context_url,
            {'token': 'invalid-token'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Invalid or expired token', response.json()['error'])
    
    def test_context_endpoint_hotel_mismatch(self):
        """Test context endpoint with hotel mismatch (anti-enumeration)"""
        response = self.client.get(
            "/api/guest/hotel/wrong-hotel/chat/context",
            {'token': self.token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Invalid or expired token', response.json()['error'])
    
    def test_context_endpoint_missing_chat_scope(self):
        """Test context endpoint with token lacking CHAT scope"""
        response = self.client.get(
            self.context_url,
            {'token': self.no_chat_token_str}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Token lacks required permissions: CHAT', response.json()['error'])
    
    def test_send_message_success(self):
        """Test sending message successfully"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        # Create conversation
        conversation = Conversation.objects.create(room=self.room)
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        
        self.assertIn('message_id', data)
        self.assertIn('sent_at', data)
        self.assertIn('conversation_id', data)
        
        # Verify message was created
        message = RoomMessage.objects.get(id=data['message_id'])
        self.assertEqual(message.sender_type, 'guest')
        self.assertEqual(message.message, 'Hello reception')
        self.assertEqual(message.booking, self.booking)
        self.assertEqual(message.room, self.room)
    
    def test_send_message_with_reply_to(self):
        """Test sending message with reply_to"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        # Create conversation and existing message
        conversation = Conversation.objects.create(room=self.room)
        original_message = RoomMessage.objects.create(
            conversation=conversation,
            sender_type='staff',
            message='How can I help you?',
            booking=self.booking,
            room=self.room
        )
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'I need extra towels',
                'reply_to': original_message.id,
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify reply relationship
        message = RoomMessage.objects.get(id=response.json()['message_id'])
        self.assertEqual(message.reply_to, original_message)
    
    def test_send_message_pre_checkin_strict_403(self):
        """Test sending message before check-in (strict validation)"""
        # Guest not checked in yet
        self.booking.checked_in_at = None
        self.booking.status = "CONFIRMED"
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Guest has not checked in yet', response.json()['error'])
    
    def test_send_message_post_checkout_strict_403(self):
        """Test sending message after checkout (strict validation)"""
        # Guest checked out
        self.booking.checked_in_at = timezone.now() - timezone.timedelta(days=1)
        self.booking.checked_out_at = timezone.now()
        self.booking.status = "CHECKED_OUT"
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Guest has already checked out', response.json()['error'])
    
    def test_send_message_no_room_assigned_409(self):
        """Test sending message with no room assigned"""
        # Check in but no room
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.assigned_room = None
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('No room assigned to booking', response.json()['error'])
    
    def test_send_message_missing_chat_scope(self):
        """Test sending message with token lacking CHAT scope"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'token': self.no_chat_token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Token lacks required permissions: CHAT', response.json()['error'])
    
    def test_send_message_empty_message(self):
        """Test sending empty message"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': '   ',  # Whitespace only
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Message text is required', response.json()['error'])
    
    def test_send_message_invalid_reply_to(self):
        """Test sending message with invalid reply_to"""
        # Check in the guest
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()
        
        response = self.client.post(
            self.messages_url,
            {
                'message': 'Hello reception',
                'reply_to': 99999,  # Non-existent message
                'token': self.token_str
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Reply message not found', response.json()['error'])


class LegacyEndpointRemovalTest(TestCase):
    """Test that legacy chat endpoints are completely removed"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_legacy_guest_chat_endpoints_removed(self):
        """Test that old guest chat endpoints return 404"""
        legacy_urls = [
            "/api/guest/chat/",
            "/api/public/chat/test-hotel/guest/chat/context/",
            "/api/public/chat/test-hotel/guest/chat/messages/",
        ]
        
        for url in legacy_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 
                status.HTTP_404_NOT_FOUND,
                f"Legacy URL {url} should return 404 but returned {response.status_code}"
            )
    
    def test_old_token_guest_chat_context_removed(self):
        """Test that old token-less guest chat endpoint is removed"""
        response = self.client.get("/api/guest/chat/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_pin_based_endpoints_removed(self):
        """Test that PIN-based chat endpoints are removed"""
        # These should all return 404 since we removed legacy chat routes
        pin_urls = [
            "/api/public/chat/test-hotel/pin-auth/",
            "/api/public/chat/test-hotel/pin/1234/context/",
        ]
        
        for url in pin_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 
                status.HTTP_404_NOT_FOUND,
                f"PIN-based URL {url} should return 404 but returned {response.status_code}"
            )


class ScopeValidationTest(TestCase):
    """Test centralized scope validation in service layer"""
    
    def setUp(self):
        self.hotel = Hotel.objects.create(name="Test Hotel", slug="test-hotel")
        self.room_type = RoomType.objects.create(
            name="Standard Room",
            hotel=self.hotel,
            capacity=2
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_number="101",
            room_type=self.room_type
        )
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="BK-2026-0001",
            primary_guest_name="John Doe",
            primary_email="john@example.com",
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            status="CHECKED_IN",
            checked_in_at=timezone.now(),
            assigned_room=self.room
        )
    
    def test_multiple_scope_validation(self):
        """Test validation with multiple required scopes"""
        from bookings.services import resolve_guest_chat_context, MissingScopeError
        
        # Token with only CHAT scope
        token_str = "test-token-multi"
        guest_token = GuestBookingToken.objects.create(
            booking=self.booking,
            hotel=self.hotel,
            token_hash=hash_token(token_str),
            status='ACTIVE',
            scopes=['CHAT']  # Missing ROOM_SERVICE
        )
        
        # Should pass with CHAT only
        booking, room, conversation, actions, reason = resolve_guest_chat_context(
            hotel_slug=self.hotel.slug,
            token_str=token_str,
            required_scopes=["CHAT"],
            action_required=True
        )
        self.assertEqual(booking.booking_id, "BK-2026-0001")
        
        # Should fail with CHAT + ROOM_SERVICE
        with self.assertRaises(MissingScopeError) as cm:
            resolve_guest_chat_context(
                hotel_slug=self.hotel.slug,
                token_str=token_str,
                required_scopes=["CHAT", "ROOM_SERVICE"],
                action_required=True
            )
        
        self.assertIn("ROOM_SERVICE", str(cm.exception))
        self.assertEqual(cm.exception.required_scopes, ["ROOM_SERVICE"])