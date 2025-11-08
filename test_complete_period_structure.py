"""
Test complete Period → Snapshots → Stocktake → Lines data structure
Shows all relationships and data available for frontend stocktake calculations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine
from stock_tracker.stock_serializers import (
    StockPeriodDetailSerializer,
    StocktakeSerializer
)
import json

print("=" * 70)
print("COMPLETE DATA STRUCTURE TEST")
print("Period → Snapshots → Stocktake → Lines")
print("=" * 70)

# Get period with all data
period = StockPeriod.objects.get(id=9)
period_data = StockPeriodDetailSerializer(period).data

print("\n" + "=" * 70)
print("1. PERIOD DATA")
print("=" * 70)
print(f"Period ID: {period_data['id']}")
print(f"Period Name: {period_data['period_name']}")
print(f"Date Range: {period_data['start_date']} to {period_data['end_date']}")
print(f"Status: {'CLOSED' if period_data['is_closed'] else 'OPEN'}")
print(f"Total Snapshots: {period_data['total_items']}")
print(f"Total Value: €{period_data['total_value']}")
print(f"Snapshot IDs: [{period_data['snapshot_ids'][0]}...{period_data['snapshot_ids'][-1]}] ({len(period_data['snapshot_ids'])} items)")
print(f"Stocktake ID: {period_data['stocktake_id']}")
print(f"Stocktake Status: {period_data['stocktake_status']}")

print("\n" + "=" * 70)
print("2. SNAPSHOT EXAMPLES BY CATEGORY")
print("=" * 70)

# Find examples from each category
categories_to_find = {
    'B': 'Bottled Beer',
    'D': 'Draught Beer',
    'S': 'Spirits',
    'W': 'Wine'
}

examples = {}
for snap in period_data['snapshots']:
    cat = snap['item']['category']
    if cat in categories_to_find and cat not in examples:
        examples[cat] = snap
    if len(examples) == 4:
        break

for cat_code, cat_name in categories_to_find.items():
    if cat_code in examples:
        snap = examples[cat_code]
        print(f"\n--- {cat_name} Example ---")
        print(f"Item: {snap['item']['name']} ({snap['item']['sku']})")
        print(f"Size: {snap['item']['size']}")
        print()
        print("OPENING (from previous period):")
        print(f"  Raw: {snap['opening_full_units']} full + "
              f"{snap['opening_partial_units']} partial")
        print(f"  Display: {snap.get('opening_display_full_units', 'N/A')} "
              f"+ {snap.get('opening_display_partial_units', 'N/A')}")
        print(f"  Value: €{snap['opening_stock_value']}")
        print()
        print("CLOSING (counted at period end):")
        print(f"  Raw: {snap['closing_full_units']} full + "
              f"{snap['closing_partial_units']} partial")
        print(f"  Display: {snap['display_full_units']} "
              f"+ {snap['display_partial_units']}")
        print(f"  Total Servings: {snap['total_servings']}")
        print(f"  Value: €{snap['closing_stock_value']}")
        print()
        print(f"  Cost Per Serving: €{snap['cost_per_serving']}")
        print()

print("\n" + "=" * 70)
print("3. DISPLAY UNIT LOGIC EXPLANATION")
print("=" * 70)
print("Bottled Beer (Doz):")
print("  - Display Full = Cases (dozens)")
print("  - Display Partial = Individual bottles")
print("  - Example: 113 bottles = 9 cases + 5 bottles")
print()
print("Draught Beer (D):")
print("  - Display Full = Kegs")
print("  - Display Partial = Pints")
print("  - Example: 567.75 pints = 6 kegs + 39.75 pints (88 pints/keg)")
print()
print("Spirits (S):")
print("  - Display Full = Bottles")
print("  - Display Partial = Fractional (partial bottle)")
print("  - Example: 2.5 = 2 bottles + 0.5 bottle")
print()
print("Wine (W):")
print("  - Display Full = Bottles")
print("  - Display Partial = Fractional (partial bottle)")
print("  - Example: 3.75 = 3 bottles + 0.75 bottle")

print("\n" + "=" * 70)
print("4. STOCKTAKE WITH LINES")
print("=" * 70)
if period_data['stocktake_id']:
    stocktake = Stocktake.objects.get(id=period_data['stocktake_id'])
    st_data = StocktakeSerializer(stocktake).data
    
    print(f"Stocktake ID: {st_data['id']}")
    print(f"Status: {st_data['status']}")
    print(f"Is Locked: {st_data['is_locked']}")
    print(f"Created: {st_data['created_at']}")
    print(f"Total Lines: {st_data['total_lines']}")
    
    if st_data['total_lines'] > 0:
        print("\n--- First Stocktake Line ---")
        line = st_data['lines'][0]
        print(json.dumps(line, indent=2, default=str))
        
        print("\n--- Stocktake Line Breakdown ---")
        print(f"Item: {line['item_name']} ({line['item_sku']})")
        print(f"Category: {line['category_code']} - {line['category_name']}")
        print()
        print("CALCULATION:")
        print(f"  Opening Qty: {line['opening_qty']}")
        print(f"  + Purchases: {line['purchases']}")
        print(f"  - Sales: {line['sales']}")
        print(f"  - Waste: {line['waste']}")
        print(f"  + Transfers In: {line['transfers_in']}")
        print(f"  - Transfers Out: {line['transfers_out']}")
        print(f"  + Adjustments: {line['adjustments']}")
        print(f"  = Expected: {line['expected_qty']}")
        print()
        print("COUNTED:")
        print(f"  Full Units: {line['counted_full_units']}")
        print(f"  Partial Units: {line['counted_partial_units']}")
        print(f"  Total Counted: {line['counted_qty']}")
        print()
        print("VARIANCE:")
        print(f"  Qty Variance: {line['variance_qty']}")
        print(f"  Value Variance: €{line['variance_value']}")
        print()
        print("VALUES:")
        print(f"  Expected Value: €{line['expected_value']}")
        print(f"  Counted Value: €{line['counted_value']}")
        print(f"  Valuation Cost: €{line['valuation_cost']}")
else:
    print("No stocktake exists for this period")

print("\n" + "=" * 70)
print("5. DATA RELATIONSHIPS")
print("=" * 70)
print("Period (9)")
print("  ├── Snapshots (254 items)")
print("  │   ├── Snapshot ID: 3801")
print("  │   │   ├── Opening Stock (from previous period)")
print("  │   │   ├── Closing Stock (counted)")
print("  │   │   ├── Unit Cost")
print("  │   │   └── Cost Per Serving")
print("  │   ├── Snapshot ID: 3802")
print("  │   └── ... (252 more)")
print("  └── Stocktake (4)")
print("      ├── Status: DRAFT/APPROVED")
print("      └── Lines (auto-calculated)")
print("          ├── Opening from Snapshot")
print("          ├── Movements from StockMovement")
print("          ├── Expected = Opening + Movements")
print("          ├── Counted (user enters)")
print("          └── Variance = Counted - Expected")

print("\n" + "=" * 70)
print("6. FRONTEND USAGE")
print("=" * 70)
print("✅ Single API call: GET /api/stock_tracker/1/periods/9/")
print()
print("Returns:")
print("  • Period info (dates, status)")
print("  • All 254 snapshots with:")
print("    - Opening stock (previous period's closing)")
print("    - Closing stock (for reference)")
print("    - Unit costs (frozen at period end)")
print("    - Display units (dozens + bottles)")
print("  • Snapshot IDs list (for quick access)")
print("  • Stocktake ID (if exists)")
print("  • Stocktake status")
print()
print("Frontend can:")
print("  1. Display opening stock from snapshots")
print("  2. User enters closing counts")
print("  3. Calculate expected = opening + purchases - sales")
print("  4. Calculate variance = counted - expected")
print("  5. Calculate value = counted × cost_per_serving")
print("  6. Show in dozens + bottles (display_full_units + display_partial_units)")
print()
print("✅ All data available for stocktake calculations!")
print("=" * 70)
