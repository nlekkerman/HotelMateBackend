"""
Test script to verify all_orders_summary endpoint includes completed orders by default
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
HOTEL_SLUG = "hotel-killarney"  # Replace with actual hotel slug

def test_orders_summary():
    """Test the all_orders_summary endpoint with different parameters"""
    
    print("=" * 80)
    print("Testing all_orders_summary endpoint - Completed Orders Inclusion")
    print("=" * 80)
    
    # Test 1: Default behavior (should include completed orders)
    print("\n📋 Test 1: Default behavior (include_completed should default to true)")
    print("-" * 80)
    url = f"{BASE_URL}/api/{HOTEL_SLUG}/room-service/orders/all-orders-summary/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Response structure:")
            print(f"   Total Orders: {data['pagination']['total_orders']}")
            print(f"   Filters Applied: {json.dumps(data['filters'], indent=6)}")
            print(f"   Status Breakdown: {json.dumps(data['status_breakdown'], indent=6)}")
            
            # Check if completed orders are included
            has_completed = any(
                item['status'] == 'completed' 
                for item in data['status_breakdown']
            )
            print(f"\n   Completed orders in breakdown: {'✅ YES' if has_completed else '❌ NO'}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Explicitly include completed orders
    print("\n📋 Test 2: Explicitly set include_completed=true")
    print("-" * 80)
    url_with_param = f"{BASE_URL}/api/{HOTEL_SLUG}/room-service/orders/all-orders-summary/?include_completed=true"
    
    try:
        response = requests.get(url_with_param)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Response structure:")
            print(f"   Total Orders: {data['pagination']['total_orders']}")
            print(f"   Filters Applied: {json.dumps(data['filters'], indent=6)}")
            completed_count = sum(
                item['count'] for item in data['status_breakdown']
                if item['status'] == 'completed'
            )
            print(f"   Completed Orders Count: {completed_count}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Exclude completed orders
    print("\n📋 Test 3: Set include_completed=false (exclude completed)")
    print("-" * 80)
    url_exclude = f"{BASE_URL}/api/{HOTEL_SLUG}/room-service/orders/all-orders-summary/?include_completed=false"
    
    try:
        response = requests.get(url_exclude)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Response structure:")
            print(f"   Total Orders: {data['pagination']['total_orders']}")
            print(f"   Filters Applied: {json.dumps(data['filters'], indent=6)}")
            print(f"   Status Breakdown: {json.dumps(data['status_breakdown'], indent=6)}")
            
            # Verify no completed orders
            has_completed = any(
                item['status'] == 'completed' 
                for item in data['status_breakdown']
            )
            print(f"\n   Completed orders in breakdown: {'❌ SHOULD BE NONE' if has_completed else '✅ CORRECTLY EXCLUDED'}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Combine filters
    print("\n📋 Test 4: Combined filters (room_number=101 + include_completed=true)")
    print("-" * 80)
    url_combined = f"{BASE_URL}/api/{HOTEL_SLUG}/room-service/orders/all-orders-summary/?room_number=101&include_completed=true"
    
    try:
        response = requests.get(url_combined)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Response structure:")
            print(f"   Total Orders: {data['pagination']['total_orders']}")
            print(f"   Filters Applied: {json.dumps(data['filters'], indent=6)}")
            print(f"   Orders by Room: {json.dumps(data['orders_by_room'], indent=6)}")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)

if __name__ == "__main__":
    test_orders_summary()
