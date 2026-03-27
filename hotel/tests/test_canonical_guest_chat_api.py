"""
Tests for Canonical Guest Chat API

Covers session/grant validation, scope enforcement, pre-checkin UX flows,
booking-scoped pusher channels, and verification that legacy routes
are completely removed.

Auth model: bootstrap with raw token → get session → all chat endpoints
accept only X-Guest-Chat-Session header.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from hotel.models import Hotel, RoomBooking
from rooms.models import Room, RoomType
from chat.models import Conversation, RoomMessage
from common.guest_chat_grant import issue_guest_chat_grant


class CanonicalGuestChatAPITest(TestCase):
    """
    All chat endpoints authenticate via X-Guest-Chat-Session header
    containing a signed grant issued at bootstrap. No raw token is
    accepted by chat views.
    """

    def setUp(self):
        self.client = APIClient()

        # Hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel", slug="test-hotel",
        )

        # Room
        self.room_type = RoomType.objects.create(
            name="Standard Room", hotel=self.hotel, capacity=2,
        )
        self.room = Room.objects.create(
            hotel=self.hotel, room_number="101",
            room_type=self.room_type,
        )

        # Booking (CONFIRMED — not yet checked-in by default)
        self.booking = RoomBooking.objects.create(
            hotel=self.hotel,
            booking_id="BK-2026-0001",
            primary_guest_name="John Doe",
            primary_email="john@example.com",
            check_in=timezone.now().date(),
            check_out=(timezone.now() + timezone.timedelta(days=2)).date(),
            status="CONFIRMED",
            assigned_room=self.room,
        )

        # Issue a valid session grant
        self.session = issue_guest_chat_grant(self.booking, self.room)

        # URLs
        self.context_url = f"/api/guest/hotel/{self.hotel.slug}/chat/context"
        self.messages_url = f"/api/guest/hotel/{self.hotel.slug}/chat/messages"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get(self, url, session=None, **extra):
        return self.client.get(
            url, HTTP_X_GUEST_CHAT_SESSION=(session or self.session),
            **extra,
        )

    def _post(self, url, data=None, session=None, **extra):
        return self.client.post(
            url, data=data,
            HTTP_X_GUEST_CHAT_SESSION=(session or self.session),
            **extra,
        )

    # ------------------------------------------------------------------
    # Context endpoint
    # ------------------------------------------------------------------

    def test_context_endpoint_success_checked_in(self):
        """Checked-in guest gets full chat context"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        response = self._get(self.context_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertIn('conversation_id', data)
        self.assertEqual(data['booking_id'], "BK-2026-0001")
        self.assertEqual(data['room_number'], "101")
        self.assertEqual(data['assigned_room_id'], self.room.id)
        self.assertEqual(data['allowed_actions'], ["chat"])

        expected_channel = (
            f"private-hotel-{self.hotel.slug}"
            f"-guest-chat-booking-{self.booking.booking_id}"
        )
        self.assertEqual(data['pusher']['channel'], expected_channel)
        self.assertEqual(data['pusher']['event'], "realtime_event")
        self.assertNotIn('disabled_reason', data)

    def test_context_endpoint_pre_checkin_ux_friendly(self):
        """Pre-checkin guest gets context with disabled chat"""
        self.booking.checked_in_at = None
        self.booking.status = "CONFIRMED"
        self.booking.save()

        response = self._get(self.context_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Check-in required to access chat")
        self.assertIn('conversation_id', data)
        self.assertIn('pusher', data)

    def test_context_endpoint_post_checkout_ux_friendly(self):
        """Checked-out guest sees disabled reason"""
        self.booking.checked_in_at = timezone.now() - timezone.timedelta(days=1)
        self.booking.checked_out_at = timezone.now()
        self.booking.status = "CHECKED_OUT"
        self.booking.save()

        response = self._get(self.context_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Chat unavailable after checkout")

    def test_context_endpoint_no_room_assigned(self):
        """No room assigned → disabled reason, null room fields"""
        self.booking.assigned_room = None
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        # Grant was issued with room, but booking now has no room;
        # grant resolution reads current booking state
        session = issue_guest_chat_grant(self.booking, None)
        response = self._get(self.context_url, session=session)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['allowed_actions'], [])
        self.assertEqual(data['disabled_reason'], "Room assignment required")
        self.assertIsNone(data['room_number'])
        self.assertIsNone(data['assigned_room_id'])

    def test_context_endpoint_missing_session(self):
        """No X-Guest-Chat-Session header → 401"""
        response = self.client.get(self.context_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('session is required', response.json()['error'].lower())

    def test_context_endpoint_invalid_session(self):
        """Tampered/garbage session → 401"""
        response = self._get(self.context_url, session="garbage-value")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_context_endpoint_hotel_mismatch(self):
        """Session for hotel A used against hotel B URL → 403"""
        response = self.client.get(
            "/api/guest/hotel/wrong-hotel/chat/context",
            HTTP_X_GUEST_CHAT_SESSION=self.session,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------
    # Send message endpoint
    # ------------------------------------------------------------------

    def test_send_message_success(self):
        """Checked-in guest sends message → 201"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        response = self._post(
            self.messages_url, {'message': 'Hello reception'},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('message_id', data)
        self.assertIn('sent_at', data)
        self.assertIn('conversation_id', data)

        message = RoomMessage.objects.get(id=data['message_id'])
        self.assertEqual(message.sender_type, 'guest')
        self.assertEqual(message.message, 'Hello reception')
        self.assertEqual(message.booking, self.booking)
        self.assertEqual(message.room, self.room)

    def test_send_message_with_reply_to(self):
        """Reply-to links to parent message"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        conversation = Conversation.objects.create(
            room=self.room, booking=self.booking,
        )
        original = RoomMessage.objects.create(
            conversation=conversation,
            sender_type='staff',
            message='How can I help you?',
            booking=self.booking,
            room=self.room,
        )

        response = self._post(
            self.messages_url,
            {'message': 'I need extra towels', 'reply_to': original.id},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        msg = RoomMessage.objects.get(id=response.json()['message_id'])
        self.assertEqual(msg.reply_to, original)

    def test_send_message_pre_checkin_strict_403(self):
        """Not checked in → 403"""
        self.booking.checked_in_at = None
        self.booking.status = "CONFIRMED"
        self.booking.save()

        response = self._post(
            self.messages_url, {'message': 'Hello reception'},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Guest has not checked in yet', response.json()['error'])

    def test_send_message_post_checkout_strict_403(self):
        """Already checked out → 403"""
        self.booking.checked_in_at = timezone.now() - timezone.timedelta(days=1)
        self.booking.checked_out_at = timezone.now()
        self.booking.status = "CHECKED_OUT"
        self.booking.save()

        response = self._post(
            self.messages_url, {'message': 'Hello reception'},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Guest has already checked out', response.json()['error'])

    def test_send_message_no_room_assigned_409(self):
        """Checked-in but no room → 409"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.assigned_room = None
        self.booking.save()

        session = issue_guest_chat_grant(self.booking, None)
        response = self._post(
            self.messages_url, {'message': 'Hello reception'},
            session=session,
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('No room assigned', response.json()['error'])

    def test_send_message_missing_session_401(self):
        """No session header → 401"""
        response = self.client.post(
            self.messages_url, {'message': 'Hello reception'},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_send_message_empty_message(self):
        """Whitespace-only message → 400"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        response = self._post(
            self.messages_url, {'message': '   '},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Message text is required', response.json()['error'])

    def test_send_message_invalid_reply_to(self):
        """Non-existent reply_to → 400"""
        self.booking.checked_in_at = timezone.now()
        self.booking.status = "CHECKED_IN"
        self.booking.save()

        response = self._post(
            self.messages_url,
            {'message': 'Hello reception', 'reply_to': 99999},
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
    """Test centralized scope validation via bootstrap + grant issuance"""

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

    def test_grant_resolves_booking_correctly(self):
        """Test that a grant issued for a booking resolves correctly"""
        from bookings.services import resolve_chat_context_from_grant
        from common.guest_chat_grant import (
            issue_guest_chat_grant,
            validate_guest_chat_grant,
        )

        grant_str = issue_guest_chat_grant(
            self.booking, self.room,
        )
        grant_ctx = validate_guest_chat_grant(
            grant_str, self.hotel.slug,
        )
        booking, room, conversation = resolve_chat_context_from_grant(
            grant_ctx,
        )
        self.assertEqual(booking.booking_id, "BK-2026-0001")
        self.assertIsNotNone(conversation)

    def test_grant_hotel_mismatch_rejected(self):
        """Test that a grant for one hotel is rejected on another"""
        from common.guest_chat_grant import (
            issue_guest_chat_grant,
            validate_guest_chat_grant,
            GrantHotelMismatchError,
        )

        grant_str = issue_guest_chat_grant(
            self.booking, self.room,
        )
        with self.assertRaises(GrantHotelMismatchError):
            validate_guest_chat_grant(grant_str, "wrong-hotel")