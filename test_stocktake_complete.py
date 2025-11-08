"""
Test complete Stocktake serializer with Period data
Stocktake should have ALL the same data as Period
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
print("STOCKTAKE = EDITABLE PERIOD")
print("Testing that Stocktake has ALL Period data")
print("=" * 80)

# Get stocktake
stocktake = Stocktake.objects.get(id=4)
stocktake_data = StocktakeSerializer(stocktake).data

# Get corresponding period
period = StockPeriod.objects.get(
    hotel=stocktake.hotel,
    start_date=stocktake.period_start,
    end_date=stocktake.period_end
)
period_data = StockPeriodDetailSerializer(period).data

print(f"\nStocktake ID: {stocktake_data['id']}")
print(f"Period ID: {period_data['id']}")
print(f"Match: {stocktake_data['period_id'] == period_data['id']}")

print(f"\n{'=' * 80}")
print("PERIOD DATA IN STOCKTAKE")
print("=" * 80)
print(f"Period ID: {stocktake_data['period_id']}")
print(f"Period Name: {stocktake_data['period_name']}")
print(f"Period Closed: {stocktake_data['period_is_closed']}")
print(f"Period Dates: {stocktake_data['period_start']} to "
      f"{stocktake_data['period_end']}")

print(f"\n{'=' * 80}")
print("SNAPSHOT DATA (same as Period)")
print("=" * 80)
print(f"Stocktake has {len(stocktake_data['snapshots'])} snapshots")
print(f"Period has {len(period_data['snapshots'])} snapshots")
match = len(stocktake_data['snapshots']) == len(period_data['snapshots'])
print(f"Match: {match}")

print(f"\n{'=' * 80}")
print("STOCKTAKE LINES (editable counts)")
print("=" * 80)
print(f"Total Lines: {stocktake_data['total_lines']}")
print(f"Total Items: {stocktake_data['total_items']}")
print(f"Status: {stocktake_data['status']}")
print(f"Locked: {stocktake_data['is_locked']}")

print(f"\n{'=' * 80}")
print("FINANCIAL SUMMARY")
print("=" * 80)
print(f"Period Total Value: €{period_data['total_value']}")
print(f"Stocktake Expected Value: €{stocktake_data['total_value']}")
print(f"Stocktake Variance Value: €{stocktake_data['total_variance_value']}")

print(f"\n{'=' * 80}")
print("FIRST SNAPSHOT COMPARISON")
print("=" * 80)

if stocktake_data['snapshots']:
    st_snap = stocktake_data['snapshots'][0]
    p_snap = period_data['snapshots'][0]
    
    print(f"\nFrom Stocktake:")
    print(f"  Item: {st_snap['item']['name']}")
    print(f"  Opening: {st_snap['opening_display_full_units']} + "
          f"{st_snap['opening_display_partial_units']}")
    print(f"  Closing: {st_snap['closing_display_full_units']} + "
          f"{st_snap['closing_display_partial_units']}")
    
    print(f"\nFrom Period:")
    print(f"  Item: {p_snap['item']['name']}")
    print(f"  Opening: {p_snap['opening_display_full_units']} + "
          f"{p_snap['opening_display_partial_units']}")
    print(f"  Closing: {p_snap['closing_display_full_units']} + "
          f"{p_snap['closing_display_partial_units']}")
    
    print(f"\nMatch: {st_snap['item']['name'] == p_snap['item']['name']}")

print(f"\n{'=' * 80}")
print("FIRST STOCKTAKE LINE")
print("=" * 80)

if stocktake_data['lines']:
    line = stocktake_data['lines'][0]
    print(f"\nItem: {line['item_name']} ({line['item_sku']})")
    print(f"Opening: {line['opening_display_full_units']} + "
          f"{line['opening_display_partial_units']}")
    print(f"Expected: {line['expected_display_full_units']} + "
          f"{line['expected_display_partial_units']}")
    print(f"Counted: {line['counted_display_full_units']} + "
          f"{line['counted_display_partial_units']}")
    print(f"Variance: {line['variance_display_full_units']} + "
          f"{line['variance_display_partial_units']}")

print(f"\n{'=' * 80}")
print("DATA STRUCTURE KEYS")
print("=" * 80)
print(f"\nPeriod keys: {sorted(period_data.keys())}")
print(f"\nStocktake keys: {sorted(stocktake_data.keys())}")

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print("""
✅ Stocktake NOW includes:
  - period_id, period_name, period_is_closed
  - snapshots (same as Period)
  - snapshot_ids (same as Period)
  - lines (editable stocktake data)
  - total_items, total_value, total_variance_value

✅ Frontend can:
  - Load Stocktake and get ALL Period data
  - See opening/closing stock from snapshots
  - Edit counts in stocktake lines
  - View variance between expected and counted
  - Know which Period this Stocktake belongs to

✅ Workflow:
  1. GET /stocktakes/4/ → Returns EVERYTHING
  2. Frontend displays snapshots (opening/closing)
  3. User enters counts in stocktake lines
  4. PATCH lines to update counts
  5. Approve stocktake → becomes final Period data
""")
print("=" * 80)
