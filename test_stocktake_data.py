"""
Test Stocktake data - what frontend receives
Similar to period test but for stocktakes
"""
import os
import sys
import django

# Setup Django environment
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

if __name__ == "__main__":
    django.setup()

from stock_tracker.models import Stocktake, StockPeriod
from stock_tracker.stock_serializers import (
    StocktakeSerializer,
    StockPeriodDetailSerializer
)
import json

print("=" * 80)
print("STOCKTAKE DATA TEST - What Frontend Receives")
print("=" * 80)

# Get a stocktake
stocktake = Stocktake.objects.get(id=4)
stocktake_data = StocktakeSerializer(stocktake).data

print(f"\nStocktake ID: {stocktake_data['id']}")
print(f"Status: {stocktake_data['status']}")
print(f"Is Locked: {stocktake_data['is_locked']}")
print(f"Period: {stocktake_data['period_start']} to {stocktake_data['period_end']}")
print(f"Total Lines: {stocktake_data['total_lines']}")

# Get related period
period = StockPeriod.objects.get(
    start_date=stocktake.period_start,
    end_date=stocktake.period_end,
    hotel=stocktake.hotel
)
period_data = StockPeriodDetailSerializer(period).data

print(f"\n{'=' * 80}")
print("RELATIONSHIP: Period → Snapshots → Stocktake → Lines")
print("=" * 80)
print(f"\nPeriod ID: {period_data['id']} ({period_data['period_name']})")
print(f"Snapshots: {period_data['total_items']} items")
print(f"Stocktake ID: {stocktake_data['id']}")
print(f"Stocktake Lines: {stocktake_data['total_lines']} items")

# Compare first snapshot vs first stocktake line
print(f"\n{'=' * 80}")
print("SNAPSHOT vs STOCKTAKE LINE COMPARISON")
print("=" * 80)

snapshot = period_data['snapshots'][0]
line = stocktake_data['lines'][0]

print(f"\n--- SNAPSHOT DATA (from Period) ---")
print(f"Snapshot ID: {snapshot['id']}")
print(f"Item: {snapshot['item']['name']} ({snapshot['item']['sku']})")
print(f"Opening Stock:")
print(f"  Raw: {snapshot['opening_full_units']} full + {snapshot['opening_partial_units']} partial")
print(f"  Display: {snapshot['opening_display_full_units']} + {snapshot['opening_display_partial_units']}")
print(f"  Value: €{snapshot['opening_stock_value']}")
print(f"Closing Stock:")
print(f"  Raw: {snapshot['closing_full_units']} full + {snapshot['closing_partial_units']} partial")
print(f"  Display: {snapshot['closing_display_full_units']} + {snapshot['closing_display_partial_units']}")
print(f"  Value: €{snapshot['closing_stock_value']}")

print(f"\n--- STOCKTAKE LINE DATA ---")
print(f"Line ID: {line['id']}")
print(f"Item: {line['item_name']} ({line['item_sku']})")
print(f"Opening Qty: {line['opening_qty']}")
print(f"Purchases: {line['purchases']}")
print(f"Sales: {line['sales']}")
print(f"Waste: {line['waste']}")
print(f"Expected Qty: {line['expected_qty']}")
print(f"Counted: {line['counted_full_units']} full + {line['counted_partial_units']} partial")
print(f"Counted Qty: {line['counted_qty']}")
print(f"Variance Qty: {line['variance_qty']}")
print(f"Expected Value: €{line['expected_value']}")
print(f"Counted Value: €{line['counted_value']}")
print(f"Variance Value: €{line['variance_value']}")

print(f"\n{'=' * 80}")
print("HOW TO CREATE STOCKTAKE FROM PERIOD")
print("=" * 80)
print("""
STEP 1: Frontend fetches Period data
GET /api/stock_tracker/{hotel_id}/periods/{period_id}/

Response includes:
- period.snapshots (all 254 items with opening/closing stock)
- period.stocktake_id (null if no stocktake exists)

STEP 2: If stocktake_id is null, create Stocktake
POST /api/stock_tracker/{hotel_id}/stocktakes/
{
  "period_start": "2025-11-01",
  "period_end": "2025-11-30",
  "notes": "November 2025 stocktake"
}

Backend automatically creates Stocktake Lines from Period Snapshots:
- opening_qty = snapshot.closing_partial_units (from previous period)
- purchases/sales/waste = from StockMovement table
- expected_qty = opening + purchases - sales - waste
- counted_* = user enters these values
- variance = counted - expected

STEP 3: User enters counts in frontend
For each item, user enters:
- counted_full_units (e.g., 10 cases)
- counted_partial_units (e.g., 5 bottles)

STEP 4: Update Stocktake Line
PATCH /api/stock_tracker/{hotel_id}/stocktake-lines/{line_id}/
{
  "counted_full_units": 10,
  "counted_partial_units": 5
}

Backend automatically calculates:
- counted_qty (total servings)
- variance_qty (counted - expected)
- counted_value (counted × cost_per_serving)
- variance_value (variance × cost_per_serving)
""")

print(f"\n{'=' * 80}")
print("COMPLETE JSON RESPONSES")
print("=" * 80)

print("\n--- PERIOD SNAPSHOT (First Item) ---")
print(json.dumps(snapshot, indent=2, default=str))

print("\n--- STOCKTAKE LINE (First Item) ---")
print(json.dumps(line, indent=2, default=str))

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print("""
✅ Period Snapshots provide:
  - opening_display_full_units, opening_display_partial_units
  - closing_display_full_units, closing_display_partial_units
  - All pre-calculated for display

✅ Stocktake Lines provide:
  - opening_qty (from snapshot)
  - expected_qty (calculated from movements)
  - counted_qty (user enters)
  - variance_qty (auto-calculated)
  - All values (auto-calculated)

✅ Frontend workflow:
  1. Fetch Period (get snapshots)
  2. Create Stocktake (backend creates lines from snapshots)
  3. Display items with opening stock from snapshots
  4. User enters counts
  5. Update lines (backend calculates everything)

✅ NO calculations needed on frontend!
""")
print("=" * 80)
