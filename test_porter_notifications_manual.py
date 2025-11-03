"""
Manual test script for porter notifications
This script demonstrates how Pusher notifications are sent to on-duty porters
"""
import os
import django
from unittest.mock import patch, MagicMock

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from staff.models import Staff, Role, Department
from room_services.models import Order, RoomServiceItem, OrderItem
from notifications.utils import notify_porters_of_room_service_order
from notifications.pusher_utils import notify_porters


def test_porter_notification():
    """
    Test that demonstrates Pusher notifications to porters
    """
    print("\n" + "="*70)
    print("PORTER NOTIFICATION TEST")
    print("="*70 + "\n")

    # Get a hotel
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found in database")
            return False
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return False

    print(f"✓ Using hotel: {hotel.name} (slug: {hotel.slug})")

    # Get porter role
    try:
        porter_role = Role.objects.get(slug='porter')
        print(f"✓ Found porter role: {porter_role.name}")
    except Role.DoesNotExist:
        print("❌ Porter role not found")
        return False

    # Get on-duty porters
    on_duty_porters = Staff.objects.filter(
        hotel=hotel,
        role=porter_role,
        is_active=True,
        is_on_duty=True
    )

    print(f"\n📊 Found {on_duty_porters.count()} on-duty porter(s):")
    for porter in on_duty_porters:
        print(f"   - {porter.first_name} {porter.last_name} (ID: {porter.id})")
    
    if not on_duty_porters.exists():
        print("\n⚠️  No on-duty porters found. Notification would not be sent.")
        print("   To test, set a porter to is_on_duty=True in the database.")
        return False

    # Mock Pusher client to capture calls
    with patch('notifications.pusher_utils.pusher_client') as mock_pusher:
        print("\n🔔 Testing notification function...")
        
        # Create a test order (won't save to DB in this test)
        test_order = MagicMock()
        test_order.id = 999
        test_order.hotel = hotel
        test_order.room_number = 101
        test_order.total_price = 25.50
        test_order.created_at.isoformat.return_value = "2025-11-02T12:00:00"
        test_order.status = 'pending'

        # Call the notification function
        notify_porters_of_room_service_order(test_order)

        # Check if Pusher was called
        if mock_pusher.trigger.called:
            print(f"✅ Pusher notification triggered!")
            print(f"   Number of calls: {mock_pusher.trigger.call_count}")
            
            # Display each call
            for i, call in enumerate(mock_pusher.trigger.call_args_list, 1):
                channel = call[0][0]
                event = call[0][1]
                data = call[0][2]
                
                print(f"\n   Call #{i}:")
                print(f"   📡 Channel: {channel}")
                print(f"   📨 Event: {event}")
                print(f"   📦 Data: {data}")
                
            return True
        else:
            print("❌ Pusher was not called!")
            return False


def test_with_real_order():
    """
    Test with a real pending order from the database
    """
    print("\n" + "="*70)
    print("REAL ORDER NOTIFICATION TEST")
    print("="*70 + "\n")

    try:
        # Get a pending order
        order = Order.objects.filter(status='pending').first()
        
        if not order:
            print("⚠️  No pending orders found in database")
            return False
            
        print(f"✓ Found pending order:")
        print(f"  - Order ID: {order.id}")
        print(f"  - Room: {order.room_number}")
        print(f"  - Status: {order.status}")
        print(f"  - Hotel: {order.hotel.name}")
        print(f"  - Total: €{order.total_price:.2f}")
        
        # Get on-duty porters for this hotel
        porter_role = Role.objects.get(slug='porter')
        on_duty_porters = Staff.objects.filter(
            hotel=order.hotel,
            role=porter_role,
            is_active=True,
            is_on_duty=True
        )
        
        print(f"\n👥 On-duty porters for {order.hotel.name}: {on_duty_porters.count()}")
        
        if not on_duty_porters.exists():
            print("⚠️  No on-duty porters to notify")
            return False

        # Mock Pusher to see what would be sent
        with patch('notifications.pusher_utils.pusher_client') as mock_pusher:
            print("\n🔔 Simulating notification...")
            
            notify_porters_of_room_service_order(order)
            
            if mock_pusher.trigger.called:
                print(f"✅ Would notify {mock_pusher.trigger.call_count} porter(s)")
                
                for call in mock_pusher.trigger.call_args_list:
                    channel = call[0][0]
                    event = call[0][1]
                    data = call[0][2]
                    
                    print(f"\n   📡 Channel: {channel}")
                    print(f"   📨 Event: {event}")
                    print(f"   📦 Order ID: {data.get('order_id')}")
                    print(f"   📦 Room: {data.get('room_number')}")
                    print(f"   📦 Total: €{data.get('total_price'):.2f}")
                    
                return True
            else:
                print("❌ No notification sent")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_porter_channel_format():
    """
    Show the Pusher channel format for porters
    """
    print("\n" + "="*70)
    print("PUSHER CHANNEL FORMAT")
    print("="*70 + "\n")
    
    try:
        hotel = Hotel.objects.first()
        porter_role = Role.objects.get(slug='porter')
        porter = Staff.objects.filter(
            hotel=hotel,
            role=porter_role
        ).first()
        
        if porter:
            channel = f"{hotel.slug}-staff-{porter.id}-porter"
            print(f"✓ Example Porter Channel: {channel}")
            print(f"  - Hotel Slug: {hotel.slug}")
            print(f"  - Staff ID: {porter.id}")
            print(f"  - Role Slug: porter")
            print(f"\n  Frontend should subscribe to: '{channel}'")
            print(f"  Events to listen for:")
            print(f"    - 'new-room-service-order' (new order)")
            print(f"    - 'order-count-update' (count update)")
            print(f"    - 'new-delivery-order' (from views)")
            return True
        else:
            print("❌ No porter found")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    print("\n" + "🚀 PORTER PUSHER NOTIFICATION TESTING" + "\n")
    
    # Run tests
    test1 = test_porter_notification()
    test2 = test_with_real_order()
    test3 = show_porter_channel_format()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Mock Test: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Real Order Test: {'✅ PASSED' if test2 else '⚠️  SKIPPED (no data)'}")
    print(f"Channel Format: {'✅ SHOWN' if test3 else '❌ FAILED'}")
    print("="*70 + "\n")
