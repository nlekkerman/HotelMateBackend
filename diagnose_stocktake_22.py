import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockPeriod, StockSnapshot, StockItem

print("=" * 80)
print("DIAGNOSTIC: Stocktake #22 Opening Balance Issue")
print("=" * 80)

# Check stocktake
try:
    stocktake = Stocktake.objects.get(id=22)
    print(f"\n✅ Stocktake #22 found:")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"   Status: {stocktake.status}")
    print(f"   Total lines: {stocktake.lines.count()}")
except Stocktake.DoesNotExist:
    print("\n❌ Stocktake #22 NOT FOUND")
    exit(1)

# Check previous periods
print(f"\n🔍 Looking for periods ending BEFORE {stocktake.period_start}:")
previous_periods = StockPeriod.objects.filter(
    hotel=stocktake.hotel,
    end_date__lt=stocktake.period_start
).order_by('-end_date')[:3]

if previous_periods.exists():
    print(f"   Found {previous_periods.count()} previous periods:")
    for p in previous_periods:
        print(f"   - {p.period_name}: {p.start_date} to {p.end_date} (closed: {p.is_closed})")
else:
    print("   ❌ NO previous periods found!")

# Check snapshots
print(f"\n🔍 Looking for snapshots from previous periods:")
snapshots = StockSnapshot.objects.filter(
    period__hotel=stocktake.hotel,
    period__end_date__lt=stocktake.period_start
).order_by('-period__end_date')[:5]

if snapshots.exists():
    print(f"   Found {snapshots.count()} snapshots:")
    for s in snapshots[:3]:
        print(f"   - {s.period.period_name}, Item {s.item.sku}: closing = {s.closing_partial_units}")
else:
    print("   ❌ NO snapshots found!")
    print("   This is why opening balances are ZERO!")

# Check a specific line
print(f"\n🔍 Checking first stocktake line:")
first_line = stocktake.lines.first()
if first_line:
    print(f"   Item: {first_line.item.sku} - {first_line.item.name}")
    print(f"   Opening Qty: {first_line.opening_qty}")
    print(f"   Purchases: {first_line.purchases}")
    print(f"   Expected: {first_line.expected_qty}")
    
    # Check if snapshot exists for this item
    item_snapshot = StockSnapshot.objects.filter(
        item=first_line.item,
        period__end_date__lt=stocktake.period_start
    ).order_by('-period__end_date').first()
    
    if item_snapshot:
        print(f"   ✅ Previous snapshot found: {item_snapshot.period.period_name}, closing = {item_snapshot.closing_partial_units}")
    else:
        print(f"   ❌ No previous snapshot for this item")
        print(f"   Item current stock: {first_line.item.total_stock_in_servings}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSIS:")
if not previous_periods.exists():
    print("❌ No previous periods found - this might be the first stocktake")
    print("   Opening should use current inventory, but shows zero instead")
elif not snapshots.exists():
    print("❌ Previous periods exist BUT no snapshots!")
    print("   Previous periods were NOT properly closed")
    print("   SOLUTION: Need to close the previous period to create snapshots")
else:
    print("✅ Previous periods and snapshots exist")
    print("   The fix should work - but opening is still zero?")
    print("   CHECK: Is the latest code deployed? Did server reload?")
print("=" * 80)
