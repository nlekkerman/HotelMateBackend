"""
Test script to create a breakfast order for room 101 and verify porter notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from room_services.models import BreakfastItem, BreakfastOrder, BreakfastOrderItem
from hotel.models import Hotel
from staff.models import Staff, Role, Department
from django.contrib.auth.models import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_breakfast_order():
    """Create a breakfast order for room 101 to test notifications"""
    
    # Get or create a hotel
    hotel = Hotel.objects.first()
    if not hotel:
        logger.error("No hotel found in database. Please create a hotel first.")
        return
    
    logger.info(f"Using hotel: {hotel.name} (slug: {hotel.slug})")
    
    # Check for breakfast items
    breakfast_items = BreakfastItem.objects.filter(hotel=hotel, is_on_stock=True)
    if not breakfast_items.exists():
        logger.warning("No breakfast items found. Creating sample items...")
        
        # Create sample breakfast items
        items_to_create = [
            {
                'name': 'Full English Breakfast',
                'description': 'Eggs, bacon, sausages, beans, mushrooms, toast',
                'category': 'Mains'
            },
            {
                'name': 'Scrambled Eggs',
                'description': 'Fresh scrambled eggs with herbs',
                'category': 'Hot Buffet'
            },
            {
                'name': 'Orange Juice',
                'description': 'Freshly squeezed orange juice',
                'category': 'Drinks'
            },
            {
                'name': 'Coffee',
                'description': 'Fresh brewed coffee',
                'category': 'Drinks'
            },
            {
                'name': 'Toast & Butter',
                'description': 'Fresh toast with butter',
                'category': 'Breads'
            }
        ]
        
        for item_data in items_to_create:
            BreakfastItem.objects.create(
                hotel=hotel,
                **item_data
            )
            logger.info(f"Created breakfast item: {item_data['name']}")
        
        breakfast_items = BreakfastItem.objects.filter(hotel=hotel, is_on_stock=True)
    
    logger.info(f"Found {breakfast_items.count()} breakfast items available")
    
    # Check for porter staff
    porter_role = Role.objects.filter(name='porter').first()
    if porter_role:
        porters = Staff.objects.filter(
            hotel=hotel,
            role=porter_role,
            is_on_duty=True
        )
    else:
        porters = Staff.objects.none()
        logger.warning("Porter role not found in database")
    
    if porters.exists():
        logger.info(f"Found {porters.count()} on-duty porter(s):")
        for porter in porters:
            logger.info(f"  - {porter.user.first_name} {porter.user.last_name} (ID: {porter.id})")
    else:
        logger.warning("⚠️ No on-duty porters found. Notifications will not be sent.")
        logger.info("Creating a test porter...")
        
        # Create test user for porter
        test_user, created = User.objects.get_or_create(
            username='test_porter',
            defaults={
                'first_name': 'Test',
                'last_name': 'Porter',
                'email': 'test.porter@hotel.com'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
        
        # Get or create porter role
        porter_role, _ = Role.objects.get_or_create(
            name='porter',
            defaults={'description': 'Porter staff'}
        )
        
        # Create test porter
        test_porter, created = Staff.objects.get_or_create(
            user=test_user,
            hotel=hotel,
            defaults={
                'role': porter_role,
                'is_on_duty': True
            }
        )
        if created:
            logger.info(f"✅ Created test porter: {test_porter.user.get_full_name()}")
        else:
            # Update existing porter to be on duty
            test_porter.is_on_duty = True
            test_porter.role = porter_role
            test_porter.save()
            logger.info(f"✅ Updated existing porter to on-duty: {test_porter.user.get_full_name()}")
    
    # Create the breakfast order
    logger.info("\n" + "="*60)
    logger.info("Creating breakfast order for Room 101...")
    logger.info("="*60)
    
    order = BreakfastOrder.objects.create(
        hotel=hotel,
        room_number=101,
        delivery_time='8:00-8:30',
        status='pending'
    )
    
    logger.info(f"✅ Created BreakfastOrder #{order.id}")
    logger.info(f"   Room: {order.room_number}")
    logger.info(f"   Delivery Time: {order.delivery_time}")
    logger.info(f"   Status: {order.status}")
    logger.info(f"   Created: {order.created_at}")
    
    # Add items to the order
    items_added = []
    for i, item in enumerate(breakfast_items[:3]):  # Add first 3 items
        order_item = BreakfastOrderItem.objects.create(
            order=order,
            item=item,
            quantity=1 if i == 0 else 2,
            notes=f"Special request for {item.name}" if i == 0 else ""
        )
        items_added.append(order_item)
        logger.info(f"   + {order_item.quantity}x {item.name}")
        if order_item.notes:
            logger.info(f"     Notes: {order_item.notes}")
    
    # Now trigger the notifications manually (simulating what happens in the view)
    logger.info("\n" + "="*60)
    logger.info("Triggering Pusher Notifications...")
    logger.info("="*60)
    
    from notifications.pusher_utils import (
        notify_kitchen_staff,
        notify_porters,
        notify_room_service_waiters
    )
    
    order_data = {
        "order_id": order.id,
        "room_number": order.room_number,
        "delivery_time": order.delivery_time if order.delivery_time else None,
        "created_at": order.created_at.isoformat(),
        "status": order.status
    }
    
    # Notify Kitchen staff
    kitchen_count = notify_kitchen_staff(
        hotel, 'new-breakfast-order', order_data
    )
    logger.info(f"✅ Notified {kitchen_count} kitchen staff")
    
    # Notify Room Service Waiters
    waiter_count = notify_room_service_waiters(
        hotel, 'new-breakfast-order', order_data
    )
    logger.info(f"✅ Notified {waiter_count} room service waiters")
    
    # Notify Porters
    porter_count = notify_porters(
        hotel, 'new-breakfast-delivery', order_data
    )
    logger.info(f"✅ Notified {porter_count} porters")
    
    logger.info("\n" + "="*60)
    logger.info("Test Complete!")
    logger.info("="*60)
    logger.info(f"Breakfast Order #{order.id} created for Room 101")
    logger.info(f"Pusher channels triggered:")
    logger.info(f"  - Kitchen Staff: {hotel.slug}-staff-kitchen-<staff_id>")
    logger.info(f"  - Room Service Waiters: {hotel.slug}-staff-room_service_waiter-<staff_id>")
    logger.info(f"  - Porters: {hotel.slug}-staff-porter-<staff_id>")
    logger.info(f"\nEvent Names:")
    logger.info(f"  - Kitchen/Waiters: 'new-breakfast-order'")
    logger.info(f"  - Porters: 'new-breakfast-delivery'")
    
    return order


if __name__ == '__main__':
    try:
        order = create_test_breakfast_order()
        if order:
            print(f"\n✅ SUCCESS: Breakfast order #{order.id} created and notifications sent!")
        else:
            print("\n❌ FAILED: Could not create breakfast order")
    except Exception as e:
        logger.error(f"\n❌ ERROR: {str(e)}", exc_info=True)
