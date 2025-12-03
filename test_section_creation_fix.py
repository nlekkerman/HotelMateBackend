"""
Test the fixed section creation endpoint.
This should reproduce the exact frontend call that was failing.
"""
import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from hotel.models import Hotel, PublicSection
from staff.models import Staff

User = get_user_model()

def test_section_creation():
    print("🧪 Testing Section Creation Fix")
    print("=" * 60)
    
    # Get the test hotel and staff user
    try:
        hotel = Hotel.objects.get(id=2)  # Killarney Park Hotel
        print(f"✓ Using hotel: {hotel.name} (slug: {hotel.slug})")
        
        # Find a super staff admin for this hotel
        staff = Staff.objects.filter(
            hotel=hotel,
            access_level='super_staff_admin'
        ).first()
        
        if not staff:
            print("❌ No super staff admin found for this hotel")
            return
            
        user = staff.user
        print(f"✓ Using staff user: {user.username}")
        
    except Hotel.DoesNotExist:
        print("❌ Hotel with id=2 not found")
        return
    
    # Create a test client and authenticate
    client = Client()
    client.force_login(user)
    
    # Test the exact payload that was failing
    test_payload = {
        "section_type": "list",
        "name": "dsadasd", 
        "container_name": "dasdasd"
    }
    
    print(f"\n📤 Sending payload: {json.dumps(test_payload, indent=2)}")
    
    # Make the API call
    response = client.post(
        f'/api/staff/hotel/{hotel.slug}/sections/create/',
        data=json.dumps(test_payload),
        content_type='application/json'
    )
    
    print(f"\n📨 Response Status: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        print("✅ SUCCESS! Section created correctly")
        print(f"📄 Response: {json.dumps(response_data, indent=2)}")
        
        # Check the section_type in the response
        section_type = response_data.get('section', {}).get('section_type')
        print(f"\n🔍 Section type in response: '{section_type}'")
        
        if section_type == 'list':
            print("✅ Section type is correct! (was 'list', not 'unknown')")
        else:
            print(f"❌ Section type is still wrong: expected 'list', got '{section_type}'")
            
        # Check if the list container was created with correct name
        lists = response_data.get('section', {}).get('lists', [])
        if lists:
            container_name = lists[0].get('title', '')
            print(f"🔍 Container name: '{container_name}'")
            if container_name == 'dasdasd':
                print("✅ Container name is correct!")
            else:
                print(f"⚠️  Container name mismatch: expected 'dasdasd', got '{container_name}'")
        else:
            print("❌ No list containers found in response")
            
    else:
        print("❌ FAILED! Error response:")
        try:
            error_data = response.json()
            print(f"📄 Error: {json.dumps(error_data, indent=2)}")
        except:
            print(f"📄 Raw response: {response.content.decode()}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_section_creation()