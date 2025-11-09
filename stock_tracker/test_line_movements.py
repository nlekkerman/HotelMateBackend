"""
Test script for manual movement entry from stocktake lines.

This script demonstrates:
1. Creating a stocktake line movement
2. Fetching all movements for a line
3. Verifying calculations update correctly
"""

import requests

# Configuration
BASE_URL = "http://localhost:8000"
HOTEL_SLUG = "your-hotel-slug"  # Replace with your hotel slug
LINE_ID = 1  # Replace with a real stocktake line ID

# Optional: Add authentication token if required
HEADERS = {
    "Content-Type": "application/json",
    # "Authorization": "Token your-auth-token-here"
}


def add_movement(line_id, movement_type, quantity, reference=None, notes=None):
    """Add a movement to a stocktake line."""
    url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{line_id}/add-movement/"
    
    payload = {
        "movement_type": movement_type,
        "quantity": quantity,
    }
    
    if reference:
        payload["reference"] = reference
    if notes:
        payload["notes"] = notes
    
    print(f"\n{'='*60}")
    print(f"Adding {movement_type} movement to line {line_id}")
    print(f"Quantity: {quantity}")
    print(f"{'='*60}")
    
    response = requests.post(url, json=payload, headers=HEADERS)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ Success! Movement ID: {data['movement']['id']}")
        print(f"\nUpdated Line Data:")
        line = data['line']
        print(f"  Opening:      {line['opening_qty']}")
        print(f"  Purchases:    {line['purchases']}")
        print(f"  Sales:        {line['sales']}")
        print(f"  Waste:        {line['waste']}")
        print(f"  Transfer In:  {line['transfers_in']}")
        print(f"  Transfer Out: {line['transfers_out']}")
        print(f"  Adjustments:  {line['adjustments']}")
        print(f"  ---")
        print(f"  Expected:     {line['expected_qty']}")
        print(f"  Counted:      {line['counted_qty']}")
        print(f"  Variance:     {line['variance_qty']}")
        return data
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.json())
        return None


def get_line_movements(line_id):
    """Get all movements for a stocktake line."""
    url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/{line_id}/movements/"
    
    print(f"\n{'='*60}")
    print(f"Fetching movements for line {line_id}")
    print(f"{'='*60}")
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        summary = data['summary']
        movements = data['movements']
        
        print(f"\nSummary:")
        print(f"  Total Purchases:    {summary['total_purchases']}")
        print(f"  Total Sales:        {summary['total_sales']}")
        print(f"  Total Waste:        {summary['total_waste']}")
        print(f"  Total Transfer In:  {summary['total_transfers_in']}")
        print(f"  Total Transfer Out: {summary['total_transfers_out']}")
        print(f"  Total Adjustments:  {summary['total_adjustments']}")
        print(f"  Total Movements:    {summary['movement_count']}")
        
        print(f"\nIndividual Movements ({len(movements)}):")
        print(f"{'ID':<6} {'Type':<15} {'Qty':<10} {'Reference':<15} {'Staff':<20}")
        print("-" * 80)
        
        for m in movements:
            print(
                f"{m['id']:<6} "
                f"{m['movement_type']:<15} "
                f"{m['quantity']:<10} "
                f"{m['reference'] or 'N/A':<15} "
                f"{m['staff_name'] or 'System':<20}"
            )
        
        return data
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.json())
        return None


def test_all_movement_types():
    """Test adding all types of movements."""
    
    print("\n" + "="*60)
    print("TESTING ALL MOVEMENT TYPES")
    print("="*60)
    
    # Test data for each movement type
    test_movements = [
        {
            "movement_type": "PURCHASE",
            "quantity": 24,
            "reference": "TEST-INV-001",
            "notes": "Test purchase"
        },
        {
            "movement_type": "SALE",
            "quantity": 15,
            "reference": "TEST-SALE-001",
            "notes": "Test sale"
        },
        {
            "movement_type": "WASTE",
            "quantity": 2,
            "reference": "TEST-WASTE-001",
            "notes": "Test waste"
        },
        {
            "movement_type": "TRANSFER_IN",
            "quantity": 10,
            "reference": "TEST-XFR-IN-001",
            "notes": "Test transfer in"
        },
        {
            "movement_type": "TRANSFER_OUT",
            "quantity": 5,
            "reference": "TEST-XFR-OUT-001",
            "notes": "Test transfer out"
        },
        {
            "movement_type": "ADJUSTMENT",
            "quantity": -1.5,
            "reference": "TEST-ADJ-001",
            "notes": "Test adjustment"
        }
    ]
    
    for movement in test_movements:
        result = add_movement(
            LINE_ID,
            movement["movement_type"],
            movement["quantity"],
            movement["reference"],
            movement["notes"]
        )
        
        if not result:
            print(f"Failed to add {movement['movement_type']}")
            return False
    
    print("\n✓ All movement types added successfully!")
    return True


def main():
    """Main test function."""
    print("="*60)
    print("STOCKTAKE LINE MOVEMENT TEST SCRIPT")
    print("="*60)
    print(f"Hotel: {HOTEL_SLUG}")
    print(f"Line ID: {LINE_ID}")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Add a single purchase
    print("\n\nTEST 1: Add a single purchase")
    add_movement(
        LINE_ID,
        "PURCHASE",
        24.0,
        reference="TEST-INV-12345",
        notes="Test delivery from script"
    )
    
    # Test 2: Add a sale
    print("\n\nTEST 2: Add a sale")
    add_movement(
        LINE_ID,
        "SALE",
        15.0,
        reference="TEST-SALE-001",
        notes="Test sale from script"
    )
    
    # Test 3: Get all movements
    print("\n\nTEST 3: Fetch all movements")
    get_line_movements(LINE_ID)
    
    # Test 4: Test all movement types (commented out by default)
    # print("\n\nTEST 4: Test all movement types")
    # test_all_movement_types()
    # get_line_movements(LINE_ID)
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
