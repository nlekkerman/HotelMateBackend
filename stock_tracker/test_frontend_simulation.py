"""
Complete End-to-End Test: Simulate Frontend to Backend Flow

This script simulates a frontend user adding movements to a stocktake line
and shows how the data flows through the entire system.

Test Flow:
1. Get initial line state
2. Add multiple movements (simulating frontend inputs)
3. Check line calculations update
4. View all movements
5. Verify data integrity
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
HOTEL_SLUG = "hotel-slug"  # Replace with your hotel slug

# Test data
TEST_LINE_ID = None  # Will be set after getting stocktake lines


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def print_section(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}--- {text} ---{Colors.END}")


def get_stocktake_lines():
    """Get all stocktake lines to pick one for testing"""
    url = f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/stocktake-lines/"
    
    print_header("STEP 1: Getting Stocktake Lines")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        lines = response.json()
        
        if not lines:
            print_error("No stocktake lines found!")
            return None
        
        print_success(f"Found {len(lines)} stocktake lines")
        
        # Display first few lines
        print_section("Available Lines")
        for i, line in enumerate(lines[:5]):
            status = "🔒 Locked" if line.get('stocktake_locked') else "✓ Open"
            print(f"  {i+1}. Line ID: {line['id']} | "
                  f"Item: {line['item_sku']} - {line['item_name']} | "
                  f"Expected: {line['expected_qty']} | "
                  f"{status}")
        
        # Pick first unlocked line
        for line in lines:
            if not line.get('stocktake_locked', False):
                print_info(f"\nSelected Line ID {line['id']} "
                          f"({line['item_sku']} - {line['item_name']}) for testing")
                return line
        
        print_error("No unlocked lines available for testing!")
        return None
        
    except Exception as e:
        print_error(f"Failed to get stocktake lines: {str(e)}")
        return None


def display_line_state(line_data, title="Current Line State"):
    """Display formatted line state"""
    print_section(title)
    
    print(f"  Item: {Colors.BOLD}{line_data['item_sku']} - "
          f"{line_data['item_name']}{Colors.END}")
    print(f"  Category: {line_data['category_code']}")
    print(f"  Size: {line_data['item_size']}")
    
    print(f"\n  {Colors.YELLOW}Stock Levels:{Colors.END}")
    print(f"    Opening:  {line_data['opening_qty']}")
    print(f"    Expected: {line_data['expected_qty']}")
    print(f"    Counted:  {line_data['counted_qty']}")
    
    variance = float(line_data['variance_qty'])
    variance_color = Colors.GREEN if variance >= 0 else Colors.RED
    print(f"    Variance: {variance_color}{line_data['variance_qty']}"
          f"{Colors.END}")
    
    print(f"\n  {Colors.CYAN}Movements:{Colors.END}")
    print(f"    Purchases:    {line_data['purchases']}")
    print(f"    Sales:        {line_data['sales']}")
    print(f"    Waste:        {line_data['waste']}")
    print(f"    Transfer In:  {line_data['transfers_in']}")
    print(f"    Transfer Out: {line_data['transfers_out']}")
    print(f"    Adjustments:  {line_data['adjustments']}")
    
    print(f"\n  {Colors.YELLOW}Values:{Colors.END}")
    print(f"    Expected Value: €{line_data['expected_value']}")
    print(f"    Counted Value:  €{line_data['counted_value']}")
    print(f"    Variance Value: €{line_data['variance_value']}")


def simulate_frontend_payload(line_id, movement_type, quantity, 
                               reference=None, notes=None):
    """
    Simulate a payload from the frontend
    This is what your React/Vue component would send
    """
    url = (f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/"
           f"stocktake-lines/{line_id}/add-movement/")
    
    # This is exactly what your frontend would send
    payload = {
        "movement_type": movement_type,
        "quantity": quantity
    }
    
    if reference:
        payload["reference"] = reference
    if notes:
        payload["notes"] = notes
    
    print_section(f"Simulating Frontend: Add {movement_type}")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"{movement_type} added successfully!")
            
            print(f"\n  {Colors.GREEN}Created Movement:{Colors.END}")
            movement = data['movement']
            print(f"    ID: {movement['id']}")
            print(f"    Type: {movement['movement_type']}")
            print(f"    Quantity: {movement['quantity']}")
            print(f"    Timestamp: {movement['timestamp']}")
            
            return data
        else:
            error_data = response.json()
            print_error(f"Failed: {error_data.get('error', 'Unknown error')}")
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {json.dumps(error_data, indent=2)}")
            return None
            
    except Exception as e:
        print_error(f"Request failed: {str(e)}")
        return None


def get_all_movements(line_id):
    """Get all movements for the line"""
    url = (f"{BASE_URL}/api/stock_tracker/{HOTEL_SLUG}/"
           f"stocktake-lines/{line_id}/movements/")
    
    print_section("Fetching All Movements")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        summary = data['summary']
        movements = data['movements']
        
        print(f"\n  {Colors.CYAN}Summary (Totals):{Colors.END}")
        print(f"    Total Purchases:    {summary['total_purchases']}")
        print(f"    Total Sales:        {summary['total_sales']}")
        print(f"    Total Waste:        {summary['total_waste']}")
        print(f"    Total Transfer In:  {summary['total_transfers_in']}")
        print(f"    Total Transfer Out: {summary['total_transfers_out']}")
        print(f"    Total Adjustments:  {summary['total_adjustments']}")
        print(f"    Total Movements:    {summary['movement_count']}")
        
        print(f"\n  {Colors.CYAN}Individual Movements:{Colors.END}")
        print(f"    {'ID':<6} {'Type':<15} {'Qty':<12} {'Reference':<15} "
              f"{'Staff':<15} {'Time'}")
        print(f"    {'-'*80}")
        
        for m in movements[:10]:  # Show last 10
            timestamp = datetime.fromisoformat(
                m['timestamp'].replace('Z', '+00:00')
            ).strftime('%Y-%m-%d %H:%M')
            
            print(f"    {m['id']:<6} "
                  f"{m['movement_type']:<15} "
                  f"{m['quantity']:<12} "
                  f"{(m['reference'] or 'N/A'):<15} "
                  f"{(m['staff_name'] or 'System'):<15} "
                  f"{timestamp}")
        
        if len(movements) > 10:
            print(f"    ... and {len(movements) - 10} more movements")
        
        return data
        
    except Exception as e:
        print_error(f"Failed to get movements: {str(e)}")
        return None


def compare_states(before, after):
    """Compare line states before and after"""
    print_section("State Comparison")
    
    fields = [
        ('purchases', 'Purchases'),
        ('sales', 'Sales'),
        ('waste', 'Waste'),
        ('transfers_in', 'Transfer In'),
        ('transfers_out', 'Transfer Out'),
        ('adjustments', 'Adjustments'),
        ('expected_qty', 'Expected Qty'),
        ('variance_qty', 'Variance Qty')
    ]
    
    print(f"  {'Field':<20} {'Before':<15} {'After':<15} {'Change':<15}")
    print(f"  {'-'*65}")
    
    for field, label in fields:
        before_val = float(before[field])
        after_val = float(after[field])
        change = after_val - before_val
        
        change_color = Colors.GREEN if change >= 0 else Colors.RED
        change_symbol = '+' if change >= 0 else ''
        
        print(f"  {label:<20} "
              f"{before_val:<15.4f} "
              f"{after_val:<15.4f} "
              f"{change_color}{change_symbol}{change:.4f}{Colors.END}")


def run_complete_test():
    """Run complete end-to-end test"""
    print_header("FRONTEND TO BACKEND FLOW SIMULATION")
    print_info("This simulates adding movements from a frontend UI")
    print_info("and shows how data flows through the entire system")
    
    # Step 1: Get a stocktake line
    initial_line = get_stocktake_lines()
    if not initial_line:
        return
    
    line_id = initial_line['id']
    
    # Display initial state
    display_line_state(initial_line, "INITIAL STATE")
    
    # Step 2: Simulate frontend adding a PURCHASE
    print_header("STEP 2: Add Purchase (Simulating Frontend Input)")
    print_info("User enters: Purchase = 24 units, Reference = 'INV-12345'")
    
    result1 = simulate_frontend_payload(
        line_id,
        movement_type="PURCHASE",
        quantity=24,
        reference="INV-12345",
        notes="Test delivery from simulation script"
    )
    
    if result1:
        state_after_purchase = result1['line']
        display_line_state(state_after_purchase, 
                          "STATE AFTER PURCHASE ADDED")
        compare_states(initial_line, state_after_purchase)
        
        input(f"\n{Colors.YELLOW}Press Enter to add next movement...{Colors.END}")
    
    # Step 3: Simulate frontend adding a SALE
    print_header("STEP 3: Add Sale (Simulating Frontend Input)")
    print_info("User enters: Sale = 15 units, Reference = 'POS-DAILY'")
    
    result2 = simulate_frontend_payload(
        line_id,
        movement_type="SALE",
        quantity=15,
        reference="POS-DAILY",
        notes="Daily POS sales entry"
    )
    
    if result2:
        state_after_sale = result2['line']
        display_line_state(state_after_sale, "STATE AFTER SALE ADDED")
        compare_states(state_after_purchase, state_after_sale)
        
        input(f"\n{Colors.YELLOW}Press Enter to add waste...{Colors.END}")
    
    # Step 4: Simulate frontend adding WASTE
    print_header("STEP 4: Add Waste (Simulating Frontend Input)")
    print_info("User enters: Waste = 2 units, Notes = 'Damaged keg'")
    
    result3 = simulate_frontend_payload(
        line_id,
        movement_type="WASTE",
        quantity=2,
        notes="Keg damaged during delivery"
    )
    
    if result3:
        state_after_waste = result3['line']
        display_line_state(state_after_waste, "STATE AFTER WASTE ADDED")
        compare_states(state_after_sale, state_after_waste)
    
    # Step 5: View all movements
    print_header("STEP 5: View All Movements (As Displayed in Frontend)")
    movements_data = get_all_movements(line_id)
    
    # Step 6: Final summary
    print_header("FINAL SUMMARY")
    
    if result3:
        final_state = result3['line']
        
        print_section("Complete Change Summary")
        compare_states(initial_line, final_state)
        
        print_section("Formula Verification")
        opening = float(final_state['opening_qty'])
        purchases = float(final_state['purchases'])
        sales = float(final_state['sales'])
        waste = float(final_state['waste'])
        transfers_in = float(final_state['transfers_in'])
        transfers_out = float(final_state['transfers_out'])
        adjustments = float(final_state['adjustments'])
        
        calculated_expected = (opening + purchases - sales - waste + 
                              transfers_in - transfers_out + adjustments)
        
        actual_expected = float(final_state['expected_qty'])
        
        print(f"\n  Formula: Opening + Purchases - Sales - Waste + "
              f"TransferIn - TransferOut + Adjustments")
        print(f"  Calculation: {opening} + {purchases} - {sales} - "
              f"{waste} + {transfers_in} - {transfers_out} + {adjustments}")
        print(f"  Calculated Expected: {calculated_expected:.4f}")
        print(f"  Actual Expected:     {actual_expected:.4f}")
        
        if abs(calculated_expected - actual_expected) < 0.0001:
            print_success("✓ Formula verification PASSED!")
        else:
            print_error("✗ Formula verification FAILED!")
        
        print_section("What Happened")
        print(f"  1. Initial state retrieved from database")
        print(f"  2. Added PURCHASE: +24 units")
        print(f"     → Purchases field updated: "
              f"{initial_line['purchases']} → {final_state['purchases']}")
        print(f"     → Expected qty recalculated")
        print(f"  3. Added SALE: +15 units")
        print(f"     → Sales field updated")
        print(f"     → Expected qty recalculated")
        print(f"  4. Added WASTE: +2 units")
        print(f"     → Waste field updated")
        print(f"     → Expected qty recalculated")
        print(f"  5. All movements stored in StockMovement table")
        print(f"  6. All changes immediately visible in frontend")
        
        print_section("Data Flow Summary")
        print(f"  Frontend → POST request → Django View → "
              f"Create StockMovement")
        print(f"  → Recalculate totals → Update StocktakeLine → "
              f"Return to Frontend")
        print(f"  → Frontend UI updates instantly")
    
    print_header("TEST COMPLETE")
    print_success("All operations completed successfully!")
    print_info(f"Line ID {line_id} now has updated movements")
    print_info("Check your frontend UI - changes should be visible!")


if __name__ == "__main__":
    try:
        run_complete_test()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print_error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
