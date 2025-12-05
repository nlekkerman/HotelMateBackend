#!/usr/bin/env python
"""
Test actual login API endpoint
"""
import os
import sys
import django
import json

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.test import Client
from django.urls import reverse

def test_login_api():
    print("=== TESTING LOGIN API ===")
    
    client = Client()
    
    # Test login
    login_data = {
        'username': 'sanja',
        'password': 'niki1234'
    }
    
    try:
        # Make POST request to login endpoint
        response = client.post('/api/auth/login/', login_data, content_type='application/json')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("=== LOGIN RESPONSE DATA ===")
            for key, value in response_data.items():
                print(f"{key}: {value}")
            print("==========================")
            
            # Check specific fields
            print("\n=== KEY FIELD ANALYSIS ===")
            print(f"is_superuser: {response_data.get('is_superuser')}")
            print(f"access_level: {response_data.get('access_level')}")
            print(f"allowed_navs count: {len(response_data.get('allowed_navs', []))}")
            print(f"allowed_navs: {response_data.get('allowed_navs')}")
            print(f"navigation_items: {response_data.get('navigation_items')}")
            
        else:
            print(f"Login failed: {response.content}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_login_api()