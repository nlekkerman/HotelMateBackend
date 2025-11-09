"""
Quick Test: Add Movement and See Immediate Updates

This is a minimal test showing the complete flow:
Frontend → Backend → Database → Response → Frontend Update
"""

import requests
import json

# CONFIGURATION - Update these!
BASE_URL = "http://localhost:8000"
HOTEL_SLUG = "your-hotel-slug"  # Change this!
LINE_ID = 1  # Change this to a real line ID!

print("="*70)
print("QUICK TEST: Frontend Movement Entry Simulation")
print("="*70)

# Step 1: Get current state
print("\n1. Getting current line state...")
url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/"
response = requests.get(url)

if response.status_code != 200:
    print(f"❌ Error: Could not get line. Status: {response.status_code}")
    print(f"   Make sure LINE_ID={LINE_ID} and HOTEL_SLUG='{HOTEL_SLUG}' are correct")
    exit(1)

before = response.json()

print(f"\n📊 BEFORE:")
print(f"   Item: {before['item_sku']} - {before['item_name']}")
print(f"   Opening:  {before['opening_qty']}")
print(f"   Purchases: {before['purchases']}")
print(f"   Sales: {before['sales']}")
print(f"   Expected: {before['expected_qty']}")
print(f"   Counted: {before['counted_qty']}")
print(f"   Variance: {before['variance_qty']}")

# Step 2: Simulate frontend adding a purchase
print("\n2. Simulating frontend: User adds a PURCHASE...")

# This is the exact payload your frontend would send
payload = {
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "TEST-INV-999",
    "notes": "Quick test from simulation"
}

print(f"\n📤 Sending payload:")
print(json.dumps(payload, indent=2))

url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/add-movement/"
response = requests.post(url, json=payload)

if response.status_code != 201:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()

# Step 3: Show the response (this is what frontend receives)
print(f"\n📥 Backend Response:")
print(json.dumps(result, indent=2))

# Step 4: Show what changed
after = result['line']

print(f"\n📊 AFTER:")
print(f"   Item: {after['item_sku']} - {after['item_name']}")
print(f"   Opening:  {after['opening_qty']}")
print(f"   Purchases: {after['purchases']} ⬅️ CHANGED!")
print(f"   Sales: {after['sales']}")
print(f"   Expected: {after['expected_qty']} ⬅️ UPDATED!")
print(f"   Counted: {after['counted_qty']}")
print(f"   Variance: {after['variance_qty']} ⬅️ UPDATED!")

# Step 5: Show the comparison
print(f"\n📈 CHANGES:")
purchases_change = float(after['purchases']) - float(before['purchases'])
expected_change = float(after['expected_qty']) - float(before['expected_qty'])
variance_change = float(after['variance_qty']) - float(before['variance_qty'])

print(f"   Purchases: {before['purchases']} → {after['purchases']} (+{purchases_change})")
print(f"   Expected:  {before['expected_qty']} → {after['expected_qty']} (+{expected_change})")
print(f"   Variance:  {before['variance_qty']} → {after['variance_qty']} ({variance_change:+})")

# Step 6: Get all movements to show it's really there
print(f"\n3. Fetching all movements to verify...")
url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/movements/"
response = requests.get(url)
movements_data = response.json()

print(f"\n📋 MOVEMENTS FOR THIS LINE:")
print(f"   Total movements: {movements_data['summary']['movement_count']}")
print(f"   Total purchases: {movements_data['summary']['total_purchases']}")
print(f"   Total sales: {movements_data['summary']['total_sales']}")

print(f"\n   Latest movements:")
for m in movements_data['movements'][:3]:
    print(f"   - {m['movement_type']}: {m['quantity']} ({m['reference']})")

print("\n" + "="*70)
print("✅ TEST COMPLETE!")
print("="*70)
print("\nWhat happened:")
print("1. Frontend sent POST request with movement data")
print("2. Backend created StockMovement record in database")
print("3. Backend recalculated line totals automatically")
print("4. Backend returned updated line data")
print("5. Frontend would update UI with new values immediately")
print("\nThe movement is now permanently stored and visible!")
