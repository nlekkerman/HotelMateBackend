import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockPeriod, StockSnapshot, StockItem

# Get Stocktake #17
stocktake = Stocktake.objects.get(id=17)

# Get corresponding period
try:
    period = StockPeriod.objects.get(
        hotel=stocktake.hotel,
        start_date=stocktake.period_start,
        end_date=stocktake.period_end
    )
except StockPeriod.DoesNotExist:
    period = None

print("=" * 80)
print(f"CHECKING WINE DATA FOR STOCKTAKE #{stocktake.id}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print("=" * 80)

# Check Wine items in StocktakeLine
print("\n1. WINE IN STOCKTAKE LINES:")
print("-" * 80)
wine_lines = stocktake.lines.filter(item__category__name="Wine")
print(f"Total Wine lines: {wine_lines.count()}")

if wine_lines.exists():
    print("\nWine Stocktake Lines:")
    for line in wine_lines:
        print(f"\n  Item: {line.item.name}")
        print(f"  Opening Qty: {line.opening_qty}")
        print(f"  Purchases: {line.purchases}")
        print(f"  Waste: {line.waste}")
        print(f"  Expected Qty: {line.expected_qty}")
        print(f"  Counted Full: {line.counted_full_units}")
        print(f"  Counted Partial: {line.counted_partial_units}")
        print(f"  Counted Qty: {line.counted_qty}")
        print(f"  Valuation Cost: €{line.valuation_cost}")
        print(f"  Expected Value: €{line.expected_value:,.2f}")
        print(f"  Counted Value: €{line.counted_value:,.2f}")
        print(f"  Variance Value: €{line.variance_value:,.2f}")
else:
    print("❌ NO WINE LINES FOUND IN STOCKTAKE!")

# Check Wine items in StockSnapshot
print("\n\n2. WINE IN STOCK SNAPSHOTS:")
print("-" * 80)
if period:
    wine_snapshots = period.snapshots.filter(item__category__name="Wine")
    print(f"Total Wine snapshots: {wine_snapshots.count()}")
else:
    wine_snapshots = StockSnapshot.objects.none()
    print("No period found for this stocktake")

if wine_snapshots.exists():
    print("\nWine Stock Snapshots:")
    total_opening = 0
    total_purchases = 0
    total_sales = 0
    total_waste = 0
    total_closing = 0
    
    for snapshot in wine_snapshots:
        opening_val = snapshot.closing_full_units * snapshot.unit_cost + snapshot.closing_partial_units * snapshot.unit_cost
        print(f"\n  Item: {snapshot.item.name}")
        print(f"  Unit Cost: €{snapshot.unit_cost}")
        print(f"  Closing Full Units: {snapshot.closing_full_units}")
        print(f"  Closing Partial Units: {snapshot.closing_partial_units}")
        print(f"  Closing Value: €{opening_val:,.2f}")
        
        total_closing += opening_val
    
    print("\n  WINE TOTALS FROM SNAPSHOTS:")
    print(f"  Total Closing Value: €{total_closing:,.2f}")
else:
    print("❌ NO WINE SNAPSHOTS FOUND IN PERIOD!")

# Check all Wine items in system
print("\n\n3. ALL WINE ITEMS IN SYSTEM:")
print("-" * 80)
all_wine_items = StockItem.objects.filter(category__name="Wine", hotel=stocktake.hotel)
print(f"Total Wine items for this hotel: {all_wine_items.count()}")

if all_wine_items.exists():
    print("\nWine Items:")
    for item in all_wine_items:
        print(f"  - {item.name} (ID: {item.id})")
else:
    print("❌ NO WINE ITEMS FOUND FOR THIS HOTEL!")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Wine Stocktake Lines: {wine_lines.count()}")
print(f"Wine Stock Snapshots: {wine_snapshots.count()}")
print(f"Total Wine Items in Hotel: {all_wine_items.count()}")

if wine_lines.count() == 0:
    print("\n⚠️  WARNING: No wine lines in stocktake - this explains €0.00 counted value!")
    print("   Wine was not included in the physical stocktake count.")
    
if wine_snapshots.count() == 0:
    print("\n⚠️  WARNING: No wine snapshots in period - no sales/movement data!")
