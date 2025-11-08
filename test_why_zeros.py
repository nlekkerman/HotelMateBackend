"""
Check why Cronins 0.0% has all zeros in stocktake line
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

from stock_tracker.models import (
    StocktakeLine,
    StockSnapshot,
    StockPeriod,
    StockMovement
)

print("=" * 80)
print("WHY CRONINS 0.0% HAS ALL ZEROS")
print("=" * 80)

# Get the stocktake line
line = StocktakeLine.objects.get(id=1709)
print(f"\nStocktake Line: {line.item.name} ({line.item.sku})")
print(f"Opening qty: {line.opening_qty}")
print(f"Purchases: {line.purchases}")
print(f"Sales: {line.sales}")
print(f"Expected: {line.expected_qty}")
print(f"Counted: {line.counted_qty}")

# Get current period
period = StockPeriod.objects.get(
    start_date=line.stocktake.period_start,
    end_date=line.stocktake.period_end,
    hotel=line.stocktake.hotel
)
print(f"\nCurrent Period: {period.period_name}")
print(f"Dates: {period.start_date} to {period.end_date}")

# Get snapshot for current period
snapshot = StockSnapshot.objects.filter(
    period=period,
    item=line.item
).first()

if snapshot:
    print(f"\nCurrent Period Snapshot:")
    print(f"Closing: {snapshot.closing_full_units} + "
          f"{snapshot.closing_partial_units} = "
          f"{snapshot.closing_partial_units} servings")
    print(f"Value: €{snapshot.closing_stock_value}")
else:
    print(f"\nNo snapshot for this period!")

# Get previous period
prev_period = StockPeriod.objects.filter(
    hotel=period.hotel,
    end_date__lt=period.start_date
).order_by('-end_date').first()

if prev_period:
    print(f"\nPrevious Period: {prev_period.period_name}")
    print(f"Dates: {prev_period.start_date} to {prev_period.end_date}")
    
    # Get previous snapshot
    prev_snapshot = StockSnapshot.objects.filter(
        period=prev_period,
        item=line.item
    ).first()
    
    if prev_snapshot:
        print(f"\nPrevious Period Snapshot:")
        print(f"Closing: {prev_snapshot.closing_full_units} + "
              f"{prev_snapshot.closing_partial_units} = "
              f"{prev_snapshot.closing_partial_units} servings")
        print(f"Value: €{prev_snapshot.closing_stock_value}")
    else:
        print(f"\nNo snapshot in previous period!")
else:
    print(f"\nNo previous period found!")

# Check for any movements
movements = StockMovement.objects.filter(
    hotel=line.stocktake.hotel,
    item=line.item,
    timestamp__gte=period.start_date,
    timestamp__lte=period.end_date
)

print(f"\n{'=' * 80}")
print("MOVEMENTS DURING THIS PERIOD")
print("=" * 80)
if movements.exists():
    for mv in movements:
        print(f"{mv.movement_type}: {mv.quantity} @ {mv.timestamp}")
else:
    print("No movements recorded for this item during this period")

print(f"\n{'=' * 80}")
print("CONCLUSION")
print("=" * 80)
print(f"""
The item '{line.item.name}' shows all zeros because:

1. Opening qty = {line.opening_qty}
   → This comes from PREVIOUS period's closing stock
   → If previous period had 0 stock, opening = 0

2. Purchases = {line.purchases}
   → No purchases recorded for this item in this period

3. Sales = {line.sales}
   → No sales recorded for this item in this period

4. Expected = Opening + Purchases - Sales - Waste
   → {line.opening_qty} + {line.purchases} - {line.sales} - {line.waste}
   → {line.expected_qty}

5. Counted = {line.counted_full_units} + {line.counted_partial_units}
   → User hasn't entered count yet (or counted 0)

This is NORMAL for items that:
- Had no stock at end of previous period
- Had no purchases this period
- Had no sales this period
- Are not currently in stock
""")
print("=" * 80)
