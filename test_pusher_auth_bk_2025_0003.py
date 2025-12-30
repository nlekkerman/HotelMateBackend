#!/usr/bin/env python
"""
Test script to simulate Pusher auth request for BK-2025-0003
"""
import requests
import json

def test_pusher_auth():
    # Token from the previous script
    correct_token = "gIF9sy-QrN1AkvoCGhqnM8yER-lucswjwNFUifTlvLg"
    booking_id = "BK-2025-0003"
    
    print(f"🧪 Testing Pusher auth for {booking_id}")
    print("=" * 50)
    
    # Test data
    test_data = {
        'socket_id': 'test-socket-123',
        'channel_name': f'private-guest-booking.{booking_id}',
        'token': correct_token
    }
    
    print(f"📋 Request data:")
    print(f"   Socket ID: {test_data['socket_id']}")
    print(f"   Channel: {test_data['channel_name']}")
    print(f"   Token: {test_data['token'][:20]}...")
    
    # Test endpoint
    url = "http://localhost:8000/api/notifications/pusher/auth/"
    
    print(f"\n📡 Making request to: {url}")
    
    try:
        response = requests.post(url, data=test_data, timeout=10)
        
        print(f"\n📊 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Auth response:")
            try:
                response_data = response.json()
                print(f"   Auth: {response_data.get('auth', 'N/A')}")
                print(f"   Channel Data: {response_data.get('channel_data', 'N/A')}")
            except:
                print(f"   Raw Response: {response.text}")
        else:
            print(f"❌ FAILED! Response:")
            print(f"   {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - is Django server running?")
        print(f"   Try: python manage.py runserver")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"💡 If this works, the frontend needs to use the correct token!")

if __name__ == '__main__':
    test_pusher_auth()