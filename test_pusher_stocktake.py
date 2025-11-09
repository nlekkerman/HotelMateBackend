"""
Test Pusher Integration for Stocktakes
Run this to verify Pusher is broadcasting correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.pusher_utils import (
    broadcast_stocktake_created,
    broadcast_line_counted_updated,
    broadcast_line_movement_added,
)

def test_pusher_broadcasts():
    """Test that Pusher broadcasts work"""
    
    print("=" * 70)
    print("TESTING PUSHER BROADCASTS")
    print("=" * 70)
    
    hotel_identifier = "hotel-killarney"
    
    # Test 1: Stocktake Created
    print("\n1. Testing stocktake-created broadcast...")
    result = broadcast_stocktake_created(
        hotel_identifier,
        {
            "id": 999,
            "period_start": "2025-12-01",
            "period_end": "2025-12-31",
            "status": "DRAFT"
        }
    )
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Test 2: Line Counted Updated
    print("\n2. Testing line-counted-updated broadcast...")
    result = broadcast_line_counted_updated(
        hotel_identifier,
        5,  # stocktake_id
        {
            "line_id": 1709,
            "item_sku": "D0030",
            "line": {
                "id": 1709,
                "counted_full_units": "2.00",
                "counted_partial_units": "50.00"
            }
        }
    )
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    # Test 3: Movement Added
    print("\n3. Testing line-movement-added broadcast...")
    result = broadcast_line_movement_added(
        hotel_identifier,
        5,  # stocktake_id
        {
            "line_id": 1709,
            "item_sku": "D0030",
            "movement": {
                "id": 9999,
                "movement_type": "PURCHASE",
                "quantity": "88.0000"
            },
            "line": {
                "id": 1709,
                "purchases": "264.0000"
            }
        }
    )
    print(f"   Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
    print("\n📋 To verify these broadcasts:")
    print("1. Open browser console")
    print("2. Subscribe to Pusher:")
    print("   const pusher = new Pusher(YOUR_KEY, { cluster: YOUR_CLUSTER });")
    print(f"   const channel = pusher.subscribe('{hotel_identifier}-stocktakes');")
    print(f"   const channel2 = pusher.subscribe('{hotel_identifier}-stocktake-5');")
    print("   channel.bind_global((event, data) => console.log(event, data));")
    print("   channel2.bind_global((event, data) => console.log(event, data));")
    print("3. Run this script again")
    print("4. Check console for events")
    print()

if __name__ == '__main__':
    test_pusher_broadcasts()
