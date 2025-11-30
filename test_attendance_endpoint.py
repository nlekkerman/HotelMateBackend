#!/usr/bin/env python
"""
Test script to debug the attendance shifts endpoint
"""
import os
import sys
import django
import requests
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from hotel.models import Hotel
from staff.models import Staff, Department

def test_endpoint():
    """Test the attendance endpoint with proper authentication"""
    
    # Check if hotel-killarney exists
    try:
        hotel = Hotel.objects.get(slug='hotel-killarney')
        print(f"✓ Hotel found: {hotel.name}")
    except Hotel.DoesNotExist:
        print("✗ Hotel 'hotel-killarney' not found")
        # List available hotels
        hotels = Hotel.objects.all()
        print("Available hotels:")
        for h in hotels:
            print(f"  - {h.slug}: {h.name}")
        return False
    
    # Check if there are staff members for this hotel
    staff_members = Staff.objects.filter(hotel=hotel)
    if not staff_members.exists():
        print("✗ No staff members found for this hotel")
        return False
    
    # Get first staff member
    staff = staff_members.first()
    print(f"✓ Staff found: {staff.user.username}")
    
    # Get or create auth token
    token, created = Token.objects.get_or_create(user=staff.user)
    print(f"✓ Token: {token.key}")
    
    # Test the endpoint
    url = f'http://localhost:8000/api/staff/hotel/{hotel.slug}/attendance/shifts/'
    headers = {
        'Authorization': f'Token {token.key}',
        'Content-Type': 'application/json'
    }
    params = {'date': '2025-11-30'}
    
    print(f"\n🔍 Testing URL: {url}")
    print(f"Parameters: {params}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 500:
            print("❌ 500 Internal Server Error")
            print("Response content:")
            print(response.text)
        elif response.status_code == 200:
            print("✅ Success!")
            print("Response JSON:")
            print(response.json())
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print("Response content:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure Django server is running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Testing attendance shifts endpoint...")
    test_endpoint()