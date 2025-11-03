"""
Create a real room service order to test notifications
This will trigger the actual notification system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from room_services.models import Order, RoomServiceItem, OrderItem
from hotel.models import Hotel


def create_test_order():
    print("\n" + "="*60)
    print("CREATING TEST ROOM SERVICE ORDER")
    print("="*60)
    
    # Get hotel
    hotel = Hotel.objects.get(slug='hotel-killarney')
    print(f"\n✓ Hotel: {hotel.name}")
    
    # Get a room service item
    menu_item = RoomServiceItem.objects.filter(hotel=hotel).first()
    
    if not menu_item:
        print("\n✗ No room service items found!")
        return
    
    print(f"✓ Menu Item: {menu_item.name} - €{menu_item.price}")
    
    # Create the order
    order = Order.objects.create(
        hotel=hotel,
        room_number=999,  # Test room number
        status="pending"
    )
    
    # Add item to the order
    OrderItem.objects.create(
        hotel=hotel,
        order=order,
        item=menu_item,
        quantity=1
    )
    
    print(f"\n✓ Order Created: #{order.id}")
    print(f"  - Room: {order.room_number}")
    print(f"  - Item: {menu_item.name}")
    print(f"  - Total: €{order.total_price}")
    print(f"  - Status: {order.status}")
    
    print("\n" + "="*60)
    print("ORDER CREATED - NOTIFICATIONS SHOULD BE SENT!")
    print("="*60)
    print("\nThe post_save signal should have triggered:")
    print("✓ notify_porters_of_room_service_order()")
    print("✓ Pusher notification sent to on-duty porters")
    print("✓ FCM notification sent (if porter has FCM token)")
    
    print("\nCheck the logs above to see if notifications were sent!")
    print()


if __name__ == '__main__':
    create_test_order()
