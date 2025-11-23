"""
Test script to verify the Hotel Public API endpoints are working correctly.
Run this while the Django server is running on http://127.0.0.1:8000/
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_list_endpoint():
    """Test GET /api/hotel/public/ - List all active hotels"""
    print("\n" + "="*60)
    print("Testing: GET /api/hotel/public/")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/hotel/public/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {len(data)} active hotels:")
            print(json.dumps(data, indent=2))
            
            # Verify structure
            if data:
                first_hotel = data[0]
                expected_fields = [
                    'id', 'name', 'slug', 'city', 'country', 'short_description',
                    'logo_url', 'guest_base_path', 'staff_base_path',
                    'guest_portal_enabled', 'staff_portal_enabled'
                ]
                missing_fields = [f for f in expected_fields if f not in first_hotel]
                if missing_fields:
                    print(f"\n❌ Missing fields: {missing_fields}")
                else:
                    print(f"\n✅ All expected fields present")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_detail_endpoint():
    """Test GET /api/hotel/public/<slug>/ - Get single hotel by slug"""
    print("\n" + "="*60)
    print("Testing: GET /api/hotel/public/hotel-killarney/")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/hotel/public/hotel-killarney/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nHotel Details:")
            print(json.dumps(data, indent=2))
            
            # Verify it's the correct hotel
            if data.get('slug') == 'hotel-killarney':
                print("\n✅ Correct hotel returned")
            else:
                print(f"\n❌ Expected slug 'hotel-killarney', got '{data.get('slug')}'")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_nonexistent_hotel():
    """Test that non-existent hotel returns 404"""
    print("\n" + "="*60)
    print("Testing: GET /api/hotel/public/nonexistent-hotel/")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/hotel/public/nonexistent-hotel/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Correctly returns 404 for non-existent hotel")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("\n🧪 Hotel Public API Live Tests")
    print("Make sure Django server is running on http://127.0.0.1:8000/")
    
    test_list_endpoint()
    test_detail_endpoint()
    test_nonexistent_hotel()
    
    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)
