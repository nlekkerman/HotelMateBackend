"""
Test suite for Room Realtime Notifications
Tests real-time notifications for room operational updates
"""
from django.test import TestCase
from unittest.mock import patch, Mock

from hotel.models import Hotel
from rooms.models import Room, RoomType
from notifications.notification_manager import NotificationManager


class RoomRealtimeNotificationTests(TestCase):
    """Test room realtime notifications via Pusher"""

    def setUp(self):
        """Set up test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel"
        )

        # Create room type
        self.room_type = RoomType.objects.create(
            hotel=self.hotel,
            name="Standard Room",
            base_price=100.00,
            max_occupancy=2
        )

        # Create room
        self.room = Room.objects.create(
            hotel=self.hotel,
            room_type=self.room_type,
            room_number="101",
            room_status="CHECKOUT_DIRTY"
        )

        # Initialize notification manager
        self.notification_manager = NotificationManager()

    @patch('notifications.notification_manager.pusher_client')
    def test_realtime_room_updated_basic_payload(self, mock_pusher):
        """Test realtime_room_updated sends correct basic payload"""
        # Configure mock
        mock_pusher.trigger = Mock(return_value=True)

        # Call the method
        result = self.notification_manager.realtime_room_updated(
            room=self.room,
            changed_fields=["room_status", "maintenance_required"],
            source="housekeeping"
        )

        # Verify pusher was called
        self.assertTrue(result)
        mock_pusher.trigger.assert_called_once()

        # Get call arguments
        call_args = mock_pusher.trigger.call_args
        channel, event, data = call_args[0]

        # Verify channel
        self.assertEqual(channel, "test-hotel.rooms")

        # Verify event name
        self.assertEqual(event, "room_updated")

        # Verify event structure
        self.assertEqual(data["category"], "rooms")
        self.assertEqual(data["type"], "room_updated")
        
        # Verify payload structure
        payload = data["payload"]
        self.assertEqual(payload["room_number"], "101")
        self.assertEqual(payload["room_status"], "CHECKOUT_DIRTY")
        self.assertEqual(payload["changed_fields"], ["room_status", "maintenance_required"])
        self.assertIn("is_occupied", payload)
        self.assertIn("is_out_of_order", payload)
        self.assertIn("maintenance_required", payload)

        # Verify meta structure
        meta = data["meta"]
        self.assertEqual(meta["hotel_slug"], "test-hotel")
        self.assertEqual(meta["scope"]["room_number"], "101")
        self.assertIn("event_id", meta)
        self.assertIn("ts", meta)

    @patch('notifications.notification_manager.pusher_client')
    def test_realtime_room_updated_with_room_type(self, mock_pusher):
        """Test realtime_room_updated includes room type info"""
        # Configure mock
        mock_pusher.trigger = Mock(return_value=True)

        # Call the method
        self.notification_manager.realtime_room_updated(
            room=self.room,
            changed_fields=["room_status"],
            source="system"
        )

        # Get payload
        call_args = mock_pusher.trigger.call_args
        data = call_args[0][2]
        payload = data["payload"]

        # Verify room type info is included
        self.assertEqual(payload["room_type"], "Standard Room")
        self.assertEqual(payload["max_occupancy"], 2)

    @patch('notifications.notification_manager.pusher_client')
    def test_realtime_room_updated_channel_naming(self, mock_pusher):
        """Test realtime_room_updated uses correct channel naming"""
        # Configure mock
        mock_pusher.trigger = Mock(return_value=True)

        # Create room in different hotel
        other_hotel = Hotel.objects.create(
            name="Other Hotel",
            slug="other-hotel"
        )
        other_room_type = RoomType.objects.create(
            hotel=other_hotel,
            name="Deluxe Room",
            base_price=200.00
        )
        other_room = Room.objects.create(
            hotel=other_hotel,
            room_type=other_room_type,
            room_number="202",
            room_status="READY_FOR_GUEST"
        )

        # Call the method
        self.notification_manager.realtime_room_updated(
            room=other_room,
            source="front_desk"
        )

        # Verify channel uses correct hotel slug
        call_args = mock_pusher.trigger.call_args
        channel = call_args[0][0]
        self.assertEqual(channel, "other-hotel.rooms")

    @patch('notifications.notification_manager.pusher_client')
    def test_realtime_room_updated_handles_pusher_failure(self, mock_pusher):
        """Test realtime_room_updated handles pusher failures gracefully"""
        # Configure mock to raise exception
        mock_pusher.trigger = Mock(side_effect=Exception("Pusher connection failed"))

        # Call the method - should not raise exception
        result = self.notification_manager.realtime_room_updated(
            room=self.room,
            source="system"
        )

        # Should return False on failure but not crash
        self.assertFalse(result)

    @patch('notifications.notification_manager.pusher_client')
    def test_realtime_room_updated_default_parameters(self, mock_pusher):
        """Test realtime_room_updated works with default parameters"""
        # Configure mock
        mock_pusher.trigger = Mock(return_value=True)

        # Call with minimal parameters
        result = self.notification_manager.realtime_room_updated(self.room)

        # Should succeed
        self.assertTrue(result)

        # Get payload
        call_args = mock_pusher.trigger.call_args
        data = call_args[0][2]
        payload = data["payload"]

        # Should have empty changed_fields list
        self.assertEqual(payload["changed_fields"], [])