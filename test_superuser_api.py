#!/usr/bin/env python
"""
Test script to verify superuser login data and provide frontend integration guide
"""
import requests
import json
import sys

def test_superuser_login():
    """Test the actual login endpoint and show what frontend should receive"""
    
    print("=== TESTING SUPERUSER LOGIN ENDPOINT ===\n")
    
    # Login endpoint
    login_url = "http://127.0.0.1:8000/api/staff/login/"
    
    # Test credentials for superuser
    login_data = {
        "username": "nikola",
        "password": input("Enter password for superuser 'nikola': ")
    }
    
    print(f"Testing login at: {login_url}")
    print(f"Username: {login_data['username']}")
    
    try:
        # Make login request
        response = requests.post(login_url, data=login_data)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            login_response = response.json()
            
            print(f"\n✅ LOGIN SUCCESSFUL")
            print(f"Raw Response Data:")
            print(json.dumps(login_response, indent=2))
            
            # Analyze what frontend should save
            print(f"\n=== FRONTEND STORAGE GUIDE ===")
            
            # Essential data to save in localStorage/sessionStorage
            essential_data = {
                'token': login_response.get('token'),
                'staff_id': login_response.get('staff_id'),
                'username': login_response.get('username'),
                'is_superuser': login_response.get('is_superuser'),
                'access_level': login_response.get('access_level'),
                'hotel': login_response.get('hotel'),
                'allowed_navs': login_response.get('allowed_navs'),
                'role': login_response.get('role'),
                'department': login_response.get('department')
            }
            
            print("Essential data for frontend to save:")
            print(json.dumps(essential_data, indent=2))
            
            # Check superuser privileges
            print(f"\n=== SUPERUSER PRIVILEGES ===")
            print(f"✅ Is Superuser: {login_response.get('is_superuser', False)}")
            print(f"✅ Access Level: {login_response.get('access_level')}")
            print(f"✅ Navigation Count: {len(login_response.get('allowed_navs', []))}")
            print(f"✅ All Navigation Items: {login_response.get('allowed_navs', [])}")
            
            # Frontend implementation example
            print(f"\n=== FRONTEND IMPLEMENTATION EXAMPLE ===")
            print("""
// After successful login response
const loginData = response.data;

// Save essential authentication data
localStorage.setItem('authToken', loginData.token);
localStorage.setItem('staffId', loginData.staff_id);
localStorage.setItem('username', loginData.username);
localStorage.setItem('isSuperuser', loginData.is_superuser);
localStorage.setItem('accessLevel', loginData.access_level);

// Save hotel context
localStorage.setItem('hotelId', loginData.hotel.id);
localStorage.setItem('hotelName', loginData.hotel.name);
localStorage.setItem('hotelSlug', loginData.hotel.slug);

// Save navigation permissions (MOST IMPORTANT)
localStorage.setItem('allowedNavs', JSON.stringify(loginData.allowed_navs));

// Save user profile data
localStorage.setItem('userRole', loginData.role);
localStorage.setItem('userDepartment', loginData.department);

// For API requests, use Authorization header:
headers: {
    'Authorization': `Token ${loginData.token}`,
    'Content-Type': 'application/json'
}
            """)
            
            # Available API endpoints for superuser
            print(f"\n=== AVAILABLE API ENDPOINTS FOR SUPERUSER ===")
            base_url = "http://127.0.0.1:8000/api"
            hotel_slug = login_response.get('hotel', {}).get('slug', 'hotel-killarney')
            
            endpoints = {
                "Staff Management": f"{base_url}/{hotel_slug}/staff/",
                "Navigation Items": f"{base_url}/staff/navigation-items/",
                "Departments": f"{base_url}/staff/departments/",
                "Roles": f"{base_url}/staff/roles/",
                "Roster Management": f"{base_url}/{hotel_slug}/attendance/roster/",
                "Clock Logs": f"{base_url}/{hotel_slug}/attendance/clock-logs/",
                "Hotel Info": f"{base_url}/{hotel_slug}/hotel/",
                "Rooms": f"{base_url}/{hotel_slug}/rooms/",
                "Bookings": f"{base_url}/{hotel_slug}/bookings/",
                "Stock Tracker": f"{base_url}/{hotel_slug}/stock-tracker/stock-items/",
                "User Profile": f"{base_url}/staff/me/"
            }
            
            for category, url in endpoints.items():
                print(f"{category}: {url}")
            
            return True
            
        else:
            print(f"❌ LOGIN FAILED")
            print(f"Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Cannot connect to {login_url}")
        print(f"Make sure Django server is running on http://127.0.0.1:8000/")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_authenticated_request(token):
    """Test making an authenticated request with the token"""
    print(f"\n=== TESTING AUTHENTICATED REQUEST ===")
    
    me_url = "http://127.0.0.1:8000/api/staff/me/"
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(me_url, headers=headers)
        print(f"Testing: {me_url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Authenticated request successful")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Authenticated request failed")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error testing authenticated request: {e}")

if __name__ == "__main__":
    success = test_superuser_login()
    
    if success:
        token = input("\nEnter the token to test authenticated requests (or press Enter to skip): ").strip()
        if token:
            test_authenticated_request(token)