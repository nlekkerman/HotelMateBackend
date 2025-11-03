"""
Test Guest FCM and Pusher Notifications
Simulates the complete guest workflow
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import Room
from room_services.models import Order
from hotel.models import Hotel
from notifications.pusher_utils import notify_guest_in_room
from notifications.fcm_service import send_fcm_notification

def test_guest_notifications():
    print("\n🧪 GUEST NOTIFICATION TESTING\n")
    print("=" * 70)
    
    # 1. Setup test data
    print("\n1️⃣ SETUP")
    print("-" * 70)
    
    hotel = Hotel.objects.filter(slug='hotel-killarney').first()
    if not hotel:
        print("❌ Hotel not found")
        return
    
    print(f"✓ Hotel: {hotel.name}")
    
    # Get or create a test room
    room, created = Room.objects.get_or_create(
        hotel=hotel,
        room_number=101,
        defaults={'guest_id_pin': '1234'}
    )
    
    print(f"✓ Room: {room.room_number}")
    print(f"  PIN: {room.guest_id_pin}")
    
    # 2. Simulate FCM token save (happens after PIN verification)
    print("\n2️⃣ SIMULATE FCM TOKEN SAVE")
    print("-" * 70)
    
    test_fcm_token = "fXYZ_test_token_for_room_101"
    room.guest_fcm_token = test_fcm_token
    room.save()
    
    print(f"✓ FCM token saved to room: {test_fcm_token[:30]}...")
    
    # 3. Test Pusher notification to guest
    print("\n3️⃣ TEST PUSHER NOTIFICATION")
    print("-" * 70)
    
    order_data = {
        "order_id": "999",
        "room_number": str(room.room_number),
        "total_price": "25.50",
        "status": "preparing",
        "old_status": "pending"
    }
    
    pusher_success = notify_guest_in_room(
        hotel,
        str(room.room_number),
        'order-status-update',
        order_data
    )
    
    if pusher_success:
        print(f"✅ Pusher notification sent to guest")
        print(f"   Channel: {hotel.slug}-room-{room.room_number}")
        print(f"   Event: order-status-update")
        print(f"   Data: {order_data}")
    else:
        print("❌ Pusher notification failed")
    
    # 4. Test FCM push notification to guest
    print("\n4️⃣ TEST FCM PUSH NOTIFICATION")
    print("-" * 70)
    
    if room.guest_fcm_token:
        title = "🔔 Order Status Update"
        body = f"Your order is now {order_data['status']}"
        
        fcm_success = send_fcm_notification(
            room.guest_fcm_token,
            title,
            body,
            data=order_data
        )
        
        if fcm_success:
            print("✅ FCM push notification sent to guest")
            print(f"   Title: {title}")
            print(f"   Body: {body}")
            print(f"   Token: {room.guest_fcm_token[:30]}...")
        else:
            print("❌ FCM notification failed")
            print("   Note: This is expected with test token")
            print("   Use real FCM token from frontend to test")
    else:
        print("⚠️  No FCM token saved for this room")
    
    # 5. Test actual order status change (simulates porter updating order)
    print("\n5️⃣ TEST WITH REAL ORDER (if exists)")
    print("-" * 70)
    
    # Find an existing order for this room
    existing_order = Order.objects.filter(
        hotel=hotel,
        room_number=room.room_number
    ).first()
    
    if existing_order:
        print(f"✓ Found existing order #{existing_order.id}")
        print(f"  Current status: {existing_order.status}")
        print(f"  Room: {existing_order.room_number}")
        
        # Simulate status change
        old_status = existing_order.status
        new_status = 'preparing' if old_status == 'pending' else 'ready'
        
        print(f"\n📝 Simulating status change: {old_status} → {new_status}")
        print("   (In real app, porter would do this via API)")
        
        # This would trigger notifications in views.py
        print(f"\n   Backend would send:")
        print(f"   ✓ Pusher to: {hotel.slug}-room-{room.room_number}")
        print(f"   ✓ FCM to: {room.guest_fcm_token[:30] if room.guest_fcm_token else 'None'}...")
        
    else:
        print("⚠️  No existing orders for this room")
        print("   Create an order from frontend to test complete flow")
    
    # 6. Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\n✅ Room Setup: Room {room.room_number} with PIN {room.guest_id_pin}")
    print(f"✅ FCM Token: {'Saved' if room.guest_fcm_token else 'Not saved'}")
    print(f"✅ Pusher: {'Working' if pusher_success else 'Failed'}")
    print(f"⚠️  FCM: Test token (use real token from frontend)")
    
    print("\n📱 FRONTEND TEST STEPS:")
    print("-" * 70)
    print("1. Visit: http://localhost:5173/room-service/hotel-killarney/101")
    print("2. Enter PIN: 1234")
    print("3. Allow notifications (FCM token will be saved)")
    print("4. Place an order")
    print("5. As porter, change order status")
    print("6. Guest should receive:")
    print("   - Pusher update (if browser open)")
    print("   - FCM push (if browser closed)")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_guest_notifications()
