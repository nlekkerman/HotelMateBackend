"""
Test FCM Push Notification System
Tests that FCM notifications are sent when new orders are created
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff.models import Staff
from room_services.models import Order
from hotel.models import Hotel
from notifications.utils import notify_porters_of_room_service_order

def test_fcm_notifications():
    print("\n" + "="*60)
    print("TESTING FCM PUSH NOTIFICATION SYSTEM")
    print("="*60)
    
    # Get test data
    hotel = Hotel.objects.get(slug='hotel-killarney')
    print(f"\n✓ Hotel: {hotel.name}")
    
    # Get porter with FCM token
    porters = Staff.objects.filter(
        hotel=hotel,
        role__slug='porter',
        is_active=True,
        is_on_duty=True
    )
    
    print(f"\n📱 On-Duty Porters ({porters.count()}):")
    for porter in porters:
        has_token = "✓ Has FCM token" if porter.fcm_token else "✗ No FCM token"
        print(f"  - {porter.first_name} {porter.last_name} (ID: {porter.id}) - {has_token}")
    
    # Get recent order
    recent_order = Order.objects.filter(hotel=hotel).order_by('-created_at').first()
    
    if not recent_order:
        print("\n✗ No orders found to test with")
        return
    
    print(f"\n📦 Test Order:")
    print(f"  - Order ID: {recent_order.id}")
    print(f"  - Room: {recent_order.room_number}")
    print(f"  - Total: €{recent_order.total_price}")
    print(f"  - Status: {recent_order.status}")
    
    # Test notification
    print("\n" + "-"*60)
    print("SENDING TEST NOTIFICATIONS...")
    print("-"*60)
    
    notify_porters_of_room_service_order(recent_order)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNOTE: FCM notifications will only be sent to porters with FCM tokens.")
    print("To receive push notifications:")
    print("1. Open mobile app")
    print("2. Login as porter")
    print("3. Grant notification permissions")
    print("4. App will automatically save FCM token to backend")
    print("5. Close the app")
    print("6. Create a new order")
    print("7. You should receive a push notification!")
    print("\nSee FIREBASE_FCM_FRONTEND_GUIDE.md for frontend implementation.\n")

if __name__ == '__main__':
    test_fcm_notifications()
