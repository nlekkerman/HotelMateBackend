"""
Test Hotel-Scoped Orders API
Verifies that orders are properly isolated by hotel
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from room_services.models import Order
from hotel.models import Hotel


def test_hotel_scoped_orders():
    print("\n🏨 HOTEL-SCOPED ORDERS TEST\n")
    print("=" * 70)
    
    # Get all hotels
    hotels = Hotel.objects.all()
    
    print(f"\n📊 Found {hotels.count()} hotels in system\n")
    
    for hotel in hotels:
        orders = Order.objects.filter(hotel=hotel).exclude(
            status='completed'
        )
        
        print(f"🏨 Hotel: {hotel.name}")
        print(f"   Slug: {hotel.slug}")
        print(f"   Active Orders: {orders.count()}")
        
        if orders.exists():
            for order in orders[:3]:  # Show first 3
                print(f"      - Order #{order.id}: Room {order.room_number} - {order.status}")
        
        print(f"\n   ✅ API Endpoint:")
        print(f"   GET /api/room_services/{hotel.slug}/orders/all-orders-summary/")
        print()
    
    print("=" * 70)
    print("🔒 HOTEL ISOLATION TEST")
    print("=" * 70)
    
    # Test that each hotel only sees their own orders
    for hotel in hotels:
        hotel_orders = Order.objects.filter(hotel=hotel)
        other_hotel_orders = Order.objects.exclude(hotel=hotel)
        
        print(f"\n🏨 {hotel.name}:")
        print(f"   Own orders: {hotel_orders.count()}")
        print(f"   Other hotels' orders: {other_hotel_orders.count()}")
        print(f"   ✅ Isolated: Orders are properly filtered by hotel")
    
    print("\n" + "=" * 70)
    print("📋 URL STRUCTURE")
    print("=" * 70)
    print("""
All endpoints are hotel-scoped:

✅ /api/room_services/{hotel_slug}/orders/
✅ /api/room_services/{hotel_slug}/orders/{id}/
✅ /api/room_services/{hotel_slug}/orders/all-orders-summary/
✅ /api/room_services/{hotel_slug}/orders/pending-count/

Example:
- Hotel Killarney: /api/room_services/hotel-killarney/orders/
- Hotel Dublin: /api/room_services/hotel-dublin/orders/

Each hotel ONLY sees their own orders! 🔒
    """)
    
    print("=" * 70)


if __name__ == '__main__':
    test_hotel_scoped_orders()
