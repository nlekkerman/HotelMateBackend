"""
Test suite for Porter Pusher Notifications
Tests real-time notifications sent to porters on duty for room service orders
"""
from django.test import TestCase
from unittest.mock import patch

from hotel.models import Hotel
from staff.models import Staff, Role, Department
from room_services.models import Order, RoomServiceItem, OrderItem
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_porters_order_count
)
from notifications.pusher_utils import notify_porters


class PorterNotificationTests(TestCase):
    """Test porter notifications via Pusher"""

    def setUp(self):
        """Set up test data"""
        # Create hotel
        self.hotel = Hotel.objects.create(
            name="Test Hotel",
            slug="test-hotel",
            email="test@hotel.com"
        )

        # Create porter role
        self.porter_role = Role.objects.create(
            name="Porter",
            slug="porter"
        )

        # Create front office department
        self.department = Department.objects.create(
            name="Front Office",
            slug="front-office"
        )

        # Create on-duty porter
        self.porter_on_duty = Staff.objects.create(
            hotel=self.hotel,
            first_name="John",
            last_name="Porter",
            email="john.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=True,
            is_on_duty=True
        )

        # Create off-duty porter
        self.porter_off_duty = Staff.objects.create(
            hotel=self.hotel,
            first_name="Jane",
            last_name="Porter",
            email="jane.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=True,
            is_on_duty=False
        )

        # Create inactive porter
        self.porter_inactive = Staff.objects.create(
            hotel=self.hotel,
            first_name="Bob",
            last_name="Porter",
            email="bob.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=False,
            is_on_duty=True
        )

        # Create room service item
        self.item = RoomServiceItem.objects.create(
            hotel=self.hotel,
            name="Coffee",
            price=5.00
        )

    @patch('notifications.pusher_utils.pusher_client')
    def test_notify_porter_on_new_room_service_order(self, mock_pusher):
        """
        Test that on-duty porters receive notification
        for new room service order
        """
        # Create order
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=101,
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            item=self.item,
            quantity=2,
            hotel=self.hotel
        )

        # Call notification function
        notify_porters_of_room_service_order(order)

        # Verify Pusher was called
        self.assertTrue(mock_pusher.trigger.called)
        
        # Get call arguments
        call_args = mock_pusher.trigger.call_args

        # Verify channel format
        expected_channel = (
            f"{self.hotel.slug}-staff-{self.porter_on_duty.id}-porter"
        )
        self.assertEqual(call_args[0][0], expected_channel)

        # Verify event name
        self.assertEqual(call_args[0][1], 'new-room-service-order')

        # Verify data payload
        data = call_args[0][2]
        self.assertEqual(data['order_id'], order.id)
        self.assertEqual(data['room_number'], 101)
        self.assertEqual(data['status'], 'pending')
        self.assertIn('total_price', data)
        self.assertIn('created_at', data)

        # Verify only one call (only on-duty porter)
        self.assertEqual(mock_pusher.trigger.call_count, 1)

    @patch('notifications.pusher_utils.pusher_client')
    def test_only_on_duty_porters_notified(self, mock_pusher):
        """Test that only on-duty porters receive notifications"""
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=102,
            status='pending'
        )

        notify_porters_of_room_service_order(order)

        # Should only notify the on-duty porter
        self.assertEqual(mock_pusher.trigger.call_count, 1)
        
        # Verify it was the on-duty porter
        channel = mock_pusher.trigger.call_args[0][0]
        self.assertIn(str(self.porter_on_duty.id), channel)

    @patch('notifications.pusher_utils.pusher_client')
    def test_multiple_on_duty_porters_all_notified(self, mock_pusher):
        """Test that multiple on-duty porters all receive notifications"""
        # Create another on-duty porter
        porter2 = Staff.objects.create(
            hotel=self.hotel,
            first_name="Alice",
            last_name="Porter",
            email="alice.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=True,
            is_on_duty=True
        )

        order = Order.objects.create(
            hotel=self.hotel,
            room_number=103,
            status='pending'
        )

        notify_porters_of_room_service_order(order)

        # Should notify both on-duty porters
        self.assertEqual(mock_pusher.trigger.call_count, 2)

        # Verify both channels were called
        calls = mock_pusher.trigger.call_args_list
        channels = [c[0][0] for c in calls]
        
        expected_channel_1 = (
            f"{self.hotel.slug}-staff-{self.porter_on_duty.id}-porter"
        )
        expected_channel_2 = (
            f"{self.hotel.slug}-staff-{porter2.id}-porter"
        )
        
        self.assertIn(expected_channel_1, channels)
        self.assertIn(expected_channel_2, channels)

    @patch('notifications.pusher_utils.pusher_client')
    def test_order_count_notification(self, mock_pusher):
        """Test that porters receive order count updates"""
        # Create multiple pending orders
        Order.objects.create(
            hotel=self.hotel, room_number=101, status='pending'
        )
        Order.objects.create(
            hotel=self.hotel, room_number=102, status='pending'
        )
        Order.objects.create(
            hotel=self.hotel, room_number=103, status='completed'
        )

        notify_porters_order_count(self.hotel)

        # Verify notification sent
        self.assertTrue(mock_pusher.trigger.called)
        
        # Verify event and data
        call_args = mock_pusher.trigger.call_args
        self.assertEqual(call_args[0][1], 'order-count-update')
        
        data = call_args[0][2]
        self.assertEqual(data['pending_count'], 2)
        self.assertEqual(data['type'], 'room_service_orders')

    @patch('notifications.pusher_utils.pusher_client')
    def test_notification_with_order_items(self, mock_pusher):
        """Test notification data includes order total from items"""
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=104,
            status='pending'
        )
        
        # Add multiple items
        OrderItem.objects.create(
            order=order,
            item=self.item,
            quantity=2,
            hotel=self.hotel
        )
        
        item2 = RoomServiceItem.objects.create(
            hotel=self.hotel,
            name="Sandwich",
            price=8.00
        )
        OrderItem.objects.create(
            order=order,
            item=item2,
            quantity=1,
            hotel=self.hotel
        )

        notify_porters_of_room_service_order(order)

        # Verify total price
        data = mock_pusher.trigger.call_args[0][2]
        expected_total = (2 * 5.00) + (1 * 8.00)  # 18.00
        self.assertEqual(data['total_price'], expected_total)

    @patch('notifications.pusher_utils.pusher_client')
    def test_pusher_error_handling(self, mock_pusher):
        """Test that Pusher errors are handled gracefully"""
        # Make Pusher raise an exception
        mock_pusher.trigger.side_effect = Exception("Pusher connection error")

        order = Order.objects.create(
            hotel=self.hotel,
            room_number=105,
            status='pending'
        )

        # Should not raise exception
        try:
            notify_porters_of_room_service_order(order)
        except Exception as e:
            self.fail(f"Notification raised exception: {e}")

    @patch('notifications.pusher_utils.pusher_client')
    def test_channel_format(self, mock_pusher):
        """Test that channel names follow correct format"""
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=106,
            status='pending'
        )

        notify_porters_of_room_service_order(order)

        # Verify channel format: {hotel-slug}-staff-{staff-id}-porter
        channel = mock_pusher.trigger.call_args[0][0]
        expected_channel = (
            f"{self.hotel.slug}-staff-{self.porter_on_duty.id}-porter"
        )
        self.assertEqual(channel, expected_channel)

    @patch('notifications.pusher_utils.pusher_client')
    def test_notify_porters_function_returns_count(self, mock_pusher):
        """Test that notify_porters returns the count of notified staff"""
        order_data = {
            "order_id": 1,
            "room_number": 107,
            "status": "pending"
        }

        count = notify_porters(self.hotel, 'test-event', order_data)

        # Should return 1 (one on-duty porter)
        self.assertEqual(count, 1)

    @patch('notifications.pusher_utils.pusher_client')
    def test_different_hotels_isolated(self, mock_pusher):
        """
        Test that porters from different hotels
        don't receive notifications
        """
        # Create another hotel with a porter
        other_hotel = Hotel.objects.create(
            name="Other Hotel",
            slug="other-hotel",
            email="other@hotel.com"
        )
        
        other_porter = Staff.objects.create(
            hotel=other_hotel,
            first_name="Other",
            last_name="Porter",
            email="other.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=True,
            is_on_duty=True
        )

        # Create order in first hotel
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=108,
            status='pending'
        )

        notify_porters_of_room_service_order(order)

        # Should only notify porter from self.hotel
        self.assertEqual(mock_pusher.trigger.call_count, 1)
        
        channel = mock_pusher.trigger.call_args[0][0]
        self.assertIn(str(self.porter_on_duty.id), channel)
        self.assertNotIn(str(other_porter.id), channel)


class PorterNotificationIntegrationTests(TestCase):
    """Integration tests for porter notifications with signals"""

    def setUp(self):
        """Set up test data"""
        self.hotel = Hotel.objects.create(
            name="Integration Test Hotel",
            slug="integration-hotel",
            email="integration@hotel.com"
        )

        self.porter_role = Role.objects.create(
            name="Porter",
            slug="porter"
        )

        self.department = Department.objects.create(
            name="Front Office",
            slug="front-office"
        )

        self.porter = Staff.objects.create(
            hotel=self.hotel,
            first_name="Test",
            last_name="Porter",
            email="test.porter@hotel.com",
            role=self.porter_role,
            department=self.department,
            is_active=True,
            is_on_duty=True
        )

        self.item = RoomServiceItem.objects.create(
            hotel=self.hotel,
            name="Tea",
            price=3.50
        )

    @patch('notifications.pusher_utils.pusher_client')
    def test_signal_triggers_notification_on_order_creation(self, mock_pusher):
        """Test that creating an order triggers signal and notification"""
        # Create order - this should trigger the post_save signal
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=201,
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            item=self.item,
            quantity=1,
            hotel=self.hotel
        )

        # Signal should have triggered notification
        # Note: May be called twice (order notification + count notification)
        self.assertTrue(mock_pusher.trigger.called)
        
        # Verify at least one call was for new-room-service-order
        events = [call[0][1] for call in mock_pusher.trigger.call_args_list]
        self.assertIn('new-room-service-order', events)

    @patch('notifications.pusher_utils.pusher_client')
    def test_order_update_does_not_trigger_notification(self, mock_pusher):
        """Test that updating an order doesn't trigger new notifications"""
        order = Order.objects.create(
            hotel=self.hotel,
            room_number=202,
            status='pending'
        )

        # Reset mock after creation
        mock_pusher.reset_mock()

        # Update order status
        order.status = 'completed'
        order.save()

        # Should not trigger porter notification for update
        # (signals only trigger on created=True)
        calls = mock_pusher.trigger.call_args_list
        events = [call[0][1] for call in calls if len(call[0]) > 1]
        
        # new-room-service-order should not be in events
        self.assertNotIn('new-room-service-order', events)


def run_tests():
    """Helper function to run tests"""
    import unittest
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(PorterNotificationTests))
    suite.addTests(
        loader.loadTestsFromTestCase(PorterNotificationIntegrationTests)
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_tests()
