"""
Simple test to verify the section creation fix works.
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from hotel.models import Hotel
from staff.models import Staff

def test_section_creation_fix():
    print("🧪 Testing Section Creation Fix")
    print("=" * 50)
    
    try:
        # Get a test hotel
        hotel = Hotel.objects.get(id=2)
        print(f"✓ Found hotel: {hotel.name} (slug: {hotel.slug})")
        
        # Get a super staff admin for this hotel
        staff = Staff.objects.filter(
            hotel=hotel,
            access_level='super_staff_admin'
        ).first()
        
        if not staff:
            print("❌ No super staff admin found")
            return False
            
        user = staff.user
        print(f"✓ Found super staff admin: {user.username}")
        
        # Create test client
        client = Client()
        
        # Login user
        client.force_login(user)
        print("✓ User logged in successfully")
        
        # Test payload that was failing
        test_payload = {
            "section_type": "list",
            "name": "Test List Section", 
            "container_name": "Test Container"
        }
        
        print(f"\n📤 Testing payload: {json.dumps(test_payload, indent=2)}")
        
        # Make API call
        url = f'/api/staff/hotel/{hotel.slug}/sections/create/'
        print(f"📍 Making POST request to: {url}")
        
        response = client.post(
            url,
            data=json.dumps(test_payload),
            content_type='application/json'
        )
        
        print(f"\n📨 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            section = response_data.get('section', {})
            section_type = section.get('section_type')
            lists = section.get('lists', [])
            
            print("✅ SUCCESS! Section created correctly")
            print(f"   Section ID: {section.get('id')}")
            print(f"   Section Type: '{section_type}' (expected: 'list')")
            
            if section_type == 'list':
                print("✅ Section type is CORRECT!")
            else:
                print(f"❌ Section type is WRONG: expected 'list', got '{section_type}'")
                return False
                
            if lists:
                container_title = lists[0].get('title', '')
                print(f"   Container Title: '{container_title}' (expected: 'Test Container')")
                
                if container_title == 'Test Container':
                    print("✅ Container name is CORRECT!")
                else:
                    print(f"⚠️  Container name different: expected 'Test Container', got '{container_title}'")
            else:
                print("❌ No list containers found in response")
                return False
                
            return True
            
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_section_creation_fix()
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST PASSED - Section creation fix is working!")
    else:
        print("💥 TEST FAILED - Section creation still has issues")