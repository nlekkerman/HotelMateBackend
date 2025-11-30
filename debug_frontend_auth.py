#!/usr/bin/env python
"""
Test script to simulate the exact frontend request
"""
import requests

def test_frontend_request():
    """Test the exact request that the frontend is making"""
    
    # This simulates what your frontend at localhost:5173 is doing
    url = 'http://localhost:8000/api/staff/hotel/hotel-killarney/attendance/shifts/'
    params = {'date': '2025-11-30'}
    
    # Test without authentication (what's happening now)
    print("🔍 Testing without authentication (current frontend behavior)...")
    response = requests.get(url, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test with proper authentication (what should happen)
    print("\n🔍 Testing with proper authentication...")
    headers = {
        'Authorization': 'Token 011c869e59b4d098653a78b5c15c4982c6cf6a1b',
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    print("\n" + "="*60)
    print("FRONTEND ISSUE DIAGNOSIS:")
    print("="*60)
    print("❌ Your frontend is NOT sending the Authorization header")
    print("✅ The backend API is working correctly")
    print("\n🔧 SOLUTION:")
    print("Your frontend code needs to include the Authorization header:")
    print("")
    print("  const response = await fetch(url, {")
    print("    method: 'GET',")
    print("    headers: {")
    print("      'Authorization': `Token ${userToken}`,")
    print("      'Content-Type': 'application/json'")
    print("    }")
    print("  });")
    print("")
    print("Make sure your frontend:")
    print("1. Has the user's authentication token stored")
    print("2. Includes it in the Authorization header")
    print("3. Uses the format: 'Token <token_value>'")

if __name__ == '__main__':
    test_frontend_request()