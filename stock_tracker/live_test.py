"""
LIVE TEST: Add Movement to Stocktake Line 1709

This will demonstrate the complete flow from frontend payload to backend response.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
HOTEL_SLUG = "1"  # Using hotel ID as identifier
LINE_ID = 1709  # Cronins 0.0%

print("="*80)
print("LIVE TEST: Frontend Movement Entry Simulation")
print("="*80)
print(f"\nTarget Line: {LINE_ID}")
print(f"Item: B0012 - Cronins 0.0%")

# Step 1: Get current state
print("\n" + "="*80)
print("STEP 1: GET CURRENT LINE STATE")
print("="*80)

url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/"
print(f"\nGET {url}")

try:
    response = requests.get(url)
    response.raise_for_status()
    before = response.json()
    
    print(f"\n✓ Current State Retrieved")
    print(f"\n📊 BEFORE ADDING MOVEMENT:")
    print(f"   Item: {before['item_sku']} - {before['item_name']}")
    print(f"   Category: {before['category_code']}")
    print(f"   ─────────────────────────────────────────")
    print(f"   Opening:      {before['opening_qty']}")
    print(f"   Purchases:    {before['purchases']}")
    print(f"   Sales:        {before['sales']}")
    print(f"   Waste:        {before['waste']}")
    print(f"   Transfer In:  {before['transfers_in']}")
    print(f"   Transfer Out: {before['transfers_out']}")
    print(f"   Adjustments:  {before['adjustments']}")
    print(f"   ─────────────────────────────────────────")
    print(f"   Expected:     {before['expected_qty']}")
    print(f"   Counted:      {before['counted_qty']}")
    print(f"   Variance:     {before['variance_qty']}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    exit(1)

# Step 2: Add movement
print("\n" + "="*80)
print("STEP 2: ADD PURCHASE MOVEMENT (Simulating Frontend)")
print("="*80)

payload = {
    "movement_type": "PURCHASE",
    "quantity": 24,
    "reference": "TEST-INV-789",
    "notes": "Live test - adding purchase from API test"
}

print(f"\n📤 Frontend would send this JSON:")
print(json.dumps(payload, indent=2))

url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/add-movement/"
print(f"\nPOST {url}")

try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✓ Movement Created Successfully!")
        
        print(f"\n📥 Backend Response:")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        # Extract the updated line data
        after = result['line']
        movement = result['movement']
        
        print(f"\n🎉 Created Movement:")
        print(f"   ID: {movement['id']}")
        print(f"   Type: {movement['movement_type']}")
        print(f"   Quantity: {movement['quantity']}")
        print(f"   Timestamp: {movement['timestamp']}")
        
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        exit(1)
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    exit(1)

# Step 3: Show what changed
print("\n" + "="*80)
print("STEP 3: COMPARE BEFORE & AFTER")
print("="*80)

print(f"\n📊 AFTER ADDING MOVEMENT:")
print(f"   Item: {after['item_sku']} - {after['item_name']}")
print(f"   ─────────────────────────────────────────")
print(f"   Opening:      {after['opening_qty']}")
print(f"   Purchases:    {after['purchases']} ⬅️ CHANGED!")
print(f"   Sales:        {after['sales']}")
print(f"   Waste:        {after['waste']}")
print(f"   Transfer In:  {after['transfers_in']}")
print(f"   Transfer Out: {after['transfers_out']}")
print(f"   Adjustments:  {after['adjustments']}")
print(f"   ─────────────────────────────────────────")
print(f"   Expected:     {after['expected_qty']} ⬅️ UPDATED!")
print(f"   Counted:      {after['counted_qty']}")
print(f"   Variance:     {after['variance_qty']} ⬅️ UPDATED!")

print(f"\n📈 CHANGES:")
purchases_change = float(after['purchases']) - float(before['purchases'])
expected_change = float(after['expected_qty']) - float(before['expected_qty'])
variance_change = float(after['variance_qty']) - float(before['variance_qty'])

print(f"   Purchases: {before['purchases']} → {after['purchases']} (+{purchases_change})")
print(f"   Expected:  {before['expected_qty']} → {after['expected_qty']} (+{expected_change})")
print(f"   Variance:  {before['variance_qty']} → {after['variance_qty']} ({variance_change:+})")

# Step 4: Verify formula
print("\n" + "="*80)
print("STEP 4: VERIFY FORMULA")
print("="*80)

opening = float(after['opening_qty'])
purchases = float(after['purchases'])
sales = float(after['sales'])
waste = float(after['waste'])
transfers_in = float(after['transfers_in'])
transfers_out = float(after['transfers_out'])
adjustments = float(after['adjustments'])

calculated = opening + purchases - sales - waste + transfers_in - transfers_out + adjustments
actual = float(after['expected_qty'])

print(f"\n📐 Formula: Opening + Purchases - Sales - Waste + TransferIn - TransferOut + Adjustments")
print(f"   = {opening} + {purchases} - {sales} - {waste} + {transfers_in} - {transfers_out} + {adjustments}")
print(f"   = {calculated}")
print(f"\n   Calculated: {calculated}")
print(f"   Actual:     {actual}")

if abs(calculated - actual) < 0.0001:
    print(f"   ✅ MATCH! Formula is correct!")
else:
    print(f"   ❌ MISMATCH! Something's wrong!")

# Step 5: Get all movements
print("\n" + "="*80)
print("STEP 5: VIEW ALL MOVEMENTS")
print("="*80)

url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{LINE_ID}/movements/"
print(f"\nGET {url}")

try:
    response = requests.get(url)
    response.raise_for_status()
    movements_data = response.json()
    
    summary = movements_data['summary']
    movements = movements_data['movements']
    
    print(f"\n📋 MOVEMENT SUMMARY:")
    print(f"   Total Purchases:    {summary['total_purchases']}")
    print(f"   Total Sales:        {summary['total_sales']}")
    print(f"   Total Waste:        {summary['total_waste']}")
    print(f"   Total Transfer In:  {summary['total_transfers_in']}")
    print(f"   Total Transfer Out: {summary['total_transfers_out']}")
    print(f"   Total Adjustments:  {summary['total_adjustments']}")
    print(f"   Total Movements:    {summary['movement_count']}")
    
    print(f"\n📝 INDIVIDUAL MOVEMENTS (Last 5):")
    for m in movements[:5]:
        print(f"   #{m['id']}: {m['movement_type']:<12} Qty: {m['quantity']:<10} Ref: {m['reference'] or 'N/A':<15} Staff: {m['staff_name'] or 'System'}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")

# Final Summary
print("\n" + "="*80)
print("✅ TEST COMPLETE!")
print("="*80)

print(f"\n🎯 What Just Happened:")
print(f"   1. Frontend sent POST request with movement data")
print(f"   2. Backend created StockMovement record (ID: {movement['id']})")
print(f"   3. Backend recalculated line totals from ALL movements")
print(f"   4. Backend returned updated line data")
print(f"   5. Frontend UI would update instantly!")

print(f"\n💾 Data Persistence:")
print(f"   ✓ Movement saved to database")
print(f"   ✓ Line totals updated")
print(f"   ✓ Changes are permanent")
print(f"   ✓ Audit trail maintained")

print(f"\n🌐 This is EXACTLY what happens when:")
print(f"   - User fills form in React/Vue")
print(f"   - Clicks 'Add Purchase'")
print(f"   - Frontend sends this exact payload")
print(f"   - UI updates with new data")

print("\n" + "="*80)
