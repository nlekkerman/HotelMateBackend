"""
Test if Pusher is working from backend
Run: python test_pusher_working.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.pusher_utils import broadcast_line_counted_updated

print("=" * 60)
print("🔔 PUSHER TEST - Broadcasting Test Event")
print("=" * 60)

# Test broadcast
hotel_identifier = "hotel-test"
stocktake_id = 999
test_data = {
    "line_id": 123,
    "item_sku": "TEST-SKU",
    "line": {
        "id": 123,
        "counted_qty": 10,
        "test": True
    }
}

print(f"\n📡 Broadcasting to channel: {hotel_identifier}-stocktake-{stocktake_id}")
print(f"   Event: line-counted-updated")
print(f"   Data: {test_data}")

try:
    result = broadcast_line_counted_updated(
        hotel_identifier,
        stocktake_id,
        test_data
    )
    
    if result:
        print("\n✅ SUCCESS: Pusher event sent!")
        print("\n💡 To verify:")
        print(f"   1. Subscribe to channel: '{hotel_identifier}-stocktake-{stocktake_id}'")
        print(f"   2. Listen for event: 'line-counted-updated'")
        print(f"   3. You can use Pusher Debug Console: https://dashboard.pusher.com/")
    else:
        print("\n❌ FAILED: Pusher event was NOT sent")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n💡 Possible issues:")
    print("   - Check .env has PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET, PUSHER_CLUSTER")
    print("   - Make sure 'pusher' package is installed: pip install pusher")
    
print("\n" + "=" * 60)
