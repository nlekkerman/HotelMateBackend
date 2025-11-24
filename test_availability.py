"""
Quick test script for the availability endpoint
"""
import requests
import json

BASE_URL = "https://hotel-porter-d25ad83b12cf.herokuapp.com"

def test_availability():
    """Test the availability endpoint"""
    url = f"{BASE_URL}/api/hotel/hotel-killarney/availability/"
    
    params = {
        'check_in': '2025-11-25',
        'check_out': '2025-11-27',
        'adults': 2,
        'children': 0
    }
    
    print(f"Testing: {url}")
    print(f"Params: {params}\n")
    
    response = requests.get(url, params=params)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_availability()
