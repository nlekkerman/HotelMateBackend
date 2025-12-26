#!/usr/bin/env python
"""
Test script to verify cancellation policy functionality
"""
import os
import sys
import django
import json
import requests

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

try:
    django.setup()
    
    from hotel.models import Hotel, CancellationPolicy
    
    def test_hotel_policy():
        """Test that Hotel Killarney has the expected default policy"""
        try:
            hotel = Hotel.objects.get(slug="hotel-killarney")
            print(f"✅ Hotel: {hotel.name}")
            
            if hotel.default_cancellation_policy:
                policy = hotel.default_cancellation_policy
                print(f"✅ Default Policy: {policy.name} ({policy.code})")
                print(f"   Description: {policy.description}")
                print(f"   Template: {policy.template_type}")
                print(f"   Free until: {policy.free_until_hours} hours")
                print(f"   Penalty: {policy.penalty_type}")
                print(f"   No-show penalty: {policy.no_show_penalty_type}")
                return True
            else:
                print("❌ No default cancellation policy set")
                return False
                
        except Hotel.DoesNotExist:
            print(f"❌ Hotel 'hotel-killarney' not found")
            return False

    def test_api_endpoints():
        """Test API endpoints"""
        base_url = "http://127.0.0.1:8000"
        
        # Test cancellation policy endpoint
        try:
            response = requests.get(f"{base_url}/api/public/hotels/hotel-killarney/cancellation-policy/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Cancellation Policy API works")
                print(f"   Policy: {data['policy']['name']}")
                print(f"   Description: {data['policy']['description']}")
            else:
                print(f"❌ Cancellation Policy API failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Cancellation Policy API error: {e}")
        
        # Test pricing quote with cancellation policy
        try:
            quote_data = {
                "room_type_code": "STANDARD",
                "check_in": "2025-01-15", 
                "check_out": "2025-01-17",
                "adults": 2,
                "children": 0
            }
            response = requests.post(
                f"{base_url}/api/public/hotels/hotel-killarney/pricing/quote/",
                json=quote_data
            )
            if response.status_code == 200:
                data = response.json()
                if 'cancellation_policy' in data:
                    print(f"✅ Quote API includes cancellation policy")
                    if data['cancellation_policy']:
                        policy = data['cancellation_policy']
                        print(f"   Policy: {policy['name']}")
                        print(f"   Code: {policy['code']}")
                    else:
                        print(f"   No policy data (hotel has no default policy)")
                else:
                    print(f"❌ Quote API missing cancellation_policy field")
            else:
                print(f"❌ Quote API failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Quote API error: {e}")

    if __name__ == "__main__":
        print("=== Cancellation Policy Test ===\n")
        
        # Test database state
        print("1. Testing Hotel Policy Configuration:")
        if test_hotel_policy():
            print()
            
            # Test API endpoints
            print("2. Testing API Endpoints:")
            test_api_endpoints()
        
except Exception as e:
    print(f"❌ Setup error: {e}")