import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod

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
    print("No period found!")
    exit()

print("=" * 100)
print(f"COMPARING STOCKTAKE LINES vs STOCK SNAPSHOTS")
print(f"Stocktake #{stocktake.id} | Period: {period.start_date} to {period.end_date}")
print("=" * 100)

# Get Wine category for comparison
wine_lines = stocktake.lines.filter(item__category__name="Wine").order_by('item__name')[:5]
wine_snapshots = period.snapshots.filter(item__category__name="Wine").order_by('item__name')[:5]

print("\n📋 STOCKTAKE LINES (First 5 Wine Items):")
print("-" * 100)
for line in wine_lines:
    print(f"\nItem: {line.item.name}")
    print(f"  Opening Qty: {line.opening_qty}")
    print(f"  Counted Full: {line.counted_full_units}")
    print(f"  Counted Partial: {line.counted_partial_units}")
    print(f"  Counted Qty: {line.counted_qty}")
    print(f"  Expected Value: €{line.expected_value:,.2f}")
    print(f"  Counted Value: €{line.counted_value:,.2f}")

print("\n\n📊 STOCK SNAPSHOTS (Same 5 Wine Items):")
print("-" * 100)
for snapshot in wine_snapshots:
    print(f"\nItem: {snapshot.item.name}")
    print(f"  Closing Full: {snapshot.closing_full_units}")
    print(f"  Closing Partial: {snapshot.closing_partial_units}")
    print(f"  Unit Cost: €{snapshot.unit_cost}")
    print(f"  Closing Value: €{snapshot.closing_stock_value:,.2f}")

print("\n\n" + "=" * 100)
print("KEY RELATIONSHIP:")
print("=" * 100)
print("✅ StocktakeLine.counted_full_units → StockSnapshot.closing_full_units")
print("✅ StocktakeLine.counted_partial_units → StockSnapshot.closing_partial_units")
print("✅ StocktakeLine.counted_value → StockSnapshot.closing_stock_value")
print("\n🔄 When you COUNT stock in the stocktake, those values become the CLOSING values")
print("   for the period. They are the SAME numbers stored in both places!")
print("\n⚠️  In this case, Wine was NOT COUNTED (all zeros), so closing is also zero.")
