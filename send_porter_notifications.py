"""
Send real Pusher notifications to on-duty porters in Hotel Killarney
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.models import Hotel
from staff.models import Staff, Role
from room_services.models import Order
from notifications.utils import notify_porters_of_room_service_order, notify_porters_order_count


def send_real_notifications():
    """Send real Pusher notifications to on-duty porters"""
    print("\n" + "="*70)
    print("🔔 SENDING REAL PUSHER NOTIFICATIONS TO ON-DUTY PORTERS")
    print("="*70 + "\n")

    # Get Hotel Killarney
    try:
        hotel = Hotel.objects.get(slug='hotel-killarney')
        print(f"✓ Hotel: {hotel.name}")
    except Hotel.DoesNotExist:
        print("❌ Hotel Killarney not found")
        return

    # Get porter role
    try:
        porter_role = Role.objects.get(slug='porter')
        print(f"✓ Porter Role: {porter_role.name}")
    except Role.DoesNotExist:
        print("❌ Porter role not found")
        return

    # Get ALL porters for this hotel
    all_porters = Staff.objects.filter(
        hotel=hotel,
        role=porter_role,
        is_active=True
    )

    print(f"\n👥 All Active Porters in {hotel.name}:")
    for porter in all_porters:
        status = "🟢 ON DUTY" if porter.is_on_duty else "⚪ OFF DUTY"
        print(f"   {status} - {porter.first_name} {porter.last_name} (ID: {porter.id})")

    # Get on-duty porters
    on_duty_porters = all_porters.filter(is_on_duty=True)

    if not on_duty_porters.exists():
        print(f"\n⚠️  No on-duty porters found!")
        print("   Set a porter to is_on_duty=True to receive notifications.")
        return

    print(f"\n🎯 Porters who will receive notifications: {on_duty_porters.count()}")
    for porter in on_duty_porters:
        channel = f"{hotel.slug}-staff-{porter.id}-porter"
        print(f"   📡 {porter.first_name} {porter.last_name} → {channel}")

    # Get a pending order to use for notification
    pending_order = Order.objects.filter(hotel=hotel, status='pending').first()

    if pending_order:
        print(f"\n📋 Using real pending order:")
        print(f"   Order ID: {pending_order.id}")
        print(f"   Room: {pending_order.room_number}")
        print(f"   Total: €{pending_order.total_price:.2f}")
        print(f"   Status: {pending_order.status}")

        # Send notification for this order
        print(f"\n🚀 Sending order notification...")
        notify_porters_of_room_service_order(pending_order)
        print(f"✅ Order notification sent!")

    # Send count update
    print(f"\n🚀 Sending order count update...")
    notify_porters_order_count(hotel)
    print(f"✅ Count update sent!")

    # Summary
    print(f"\n" + "="*70)
    print("📊 NOTIFICATION SUMMARY")
    print("="*70)
    print(f"Hotel: {hotel.name}")
    print(f"On-Duty Porters: {on_duty_porters.count()}")
    print(f"Notifications Sent: 2 types")
    print(f"  1. Order notification (new-room-service-order)")
    print(f"  2. Count update (order-count-update)")
    
    # Show what frontend should listen for
    print(f"\n📱 Frontend Integration:")
    for porter in on_duty_porters:
        channel = f"{hotel.slug}-staff-{porter.id}-porter"
        print(f"\n   Porter: {porter.first_name} {porter.last_name}")
        print(f"   Subscribe to: '{channel}'")
        print(f"   Events:")
        print(f"     - 'new-room-service-order'")
        print(f"     - 'order-count-update'")
        print(f"     - 'new-breakfast-order'")
        print(f"     - 'new-delivery-order'")

    print("\n" + "="*70)
    print("✅ REAL NOTIFICATIONS SENT VIA PUSHER!")
    print("="*70 + "\n")


if __name__ == '__main__':
    send_real_notifications()
