import requests
import json
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

def test_login_api():
    print("=== TESTING ACTUAL LOGIN API ENDPOINT ===")
    
    # Test the login endpoint
    url = "http://127.0.0.1:8000/staff/auth/login/"
    login_data = {
        "username": "sanja",
        "password": "niki1234"
    }
    
    print(f"Making POST request to: {url}")
    print(f"Login data: {login_data}")
    
    try:
        response = requests.post(url, json=login_data, headers={
            'Content-Type': 'application/json'
        })
        
        print(f"\n=== RESPONSE STATUS ===")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"\n=== RESPONSE DATA ===")
            response_data = response.json()
            
            # Pretty print the JSON response
            print("Raw JSON response:")
            print(json.dumps(response_data, indent=2))
            
            print(f"\n=== CRITICAL FIELDS IN RESPONSE ===")
            critical_fields = ['is_superuser', 'access_level', 'allowed_navs', 'staff_id', 'is_staff', 'username', 'token']
            for field in critical_fields:
                if field in response_data:
                    value = response_data[field]
                    print(f'✅ {field}: {repr(value)} (type: {type(value).__name__})')
                else:
                    print(f'❌ {field}: MISSING from response')
                    
        else:
            print(f"❌ LOGIN FAILED")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Django server is not running")
        print("Please start the Django server with: python manage.py runserver")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_api()