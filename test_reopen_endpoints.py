"""
Test Period Reopen Endpoints
Run this to verify all endpoints are working
"""
import requests

BASE_URL = "http://127.0.0.1:8000"
# Or use: BASE_URL = "https://hotel-porter-d25ad83b12cf.herokuapp.com"

hotel = "hotel-killarney"
token = "YOUR_AUTH_TOKEN_HERE"  # Replace with actual token

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("🧪 Testing Period Reopen Endpoints\n")

# Test 1: Get reopen permissions
print("1. Testing GET /periods/reopen_permissions/")
url = f"{BASE_URL}/api/stock_tracker/{hotel}/periods/reopen_permissions/"
response = requests.get(url, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Success: {len(response.json())} permissions found")
elif response.status_code == 403:
    print(f"   ⚠️  Forbidden (need superuser)")
else:
    print(f"   ❌ Error: {response.text}")

print()

# Test 2: Get a period (check can_reopen field)
print("2. Testing GET /periods/8/")
url = f"{BASE_URL}/api/stock_tracker/{hotel}/periods/8/"
response = requests.get(url, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Success")
    print(f"   Period: {data.get('period_name')}")
    print(f"   Is Closed: {data.get('is_closed')}")
    print(f"   Can Reopen: {data.get('can_reopen')}")
    print(f"   Reopened At: {data.get('reopened_at')}")
    print(f"   Reopened By: {data.get('reopened_by')}")
else:
    print(f"   ❌ Error: {response.text}")

print()

# Test 3: Get a stocktake (check status)
print("3. Testing GET /stocktakes/8/")
url = f"{BASE_URL}/api/stock_tracker/{hotel}/stocktakes/8/"
response = requests.get(url, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Success")
    print(f"   Status: {data.get('status')}")
    print(f"   Approved At: {data.get('approved_at')}")
else:
    print(f"   ❌ Error: {response.text}")

print()
print("=" * 60)
print("If all tests show 200 status, endpoints are configured correctly!")
print("Note: You need a valid auth token to test these endpoints")
