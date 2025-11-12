"""
Check November movements and stocktake data for item B0012
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockMovement, StockPeriod, Stocktake, StocktakeLine
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print("=" * 80)

# Find item B0012
item = StockItem.objects.filter(hotel=hotel, sku='B0012').first()
if not item:
    print("❌ Item B0012 not found!")
    exit()

print(f"\nItem: {item.sku} - {item.name}")
print(f"Category: {item.category}")
print(f"UOM: {item.uom}")
print("=" * 80)

# Check November period
nov_period = StockPeriod.objects.filter(hotel=hotel, year=2025, month=11).first()
if not nov_period:
    print("❌ November period not found!")
    exit()

print(f"\nNovember Period: {nov_period.id}")
print(f"Date Range: {nov_period.start_date} to {nov_period.end_date}")
print(f"Status: {'CLOSED' if nov_period.is_closed else 'OPEN'}")
print("=" * 80)

# Check for November stocktake
nov_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=nov_period.start_date,
    period_end=nov_period.end_date
).first()

if not nov_stocktake:
    print("❌ November stocktake not found!")
    exit()

print(f"\nNovember Stocktake: {nov_stocktake.id}")
print(f"Status: {nov_stocktake.status}")
print("=" * 80)

# Check movements in November period
print("\nSTOCK MOVEMENTS IN NOVEMBER PERIOD:")
print("-" * 80)

movements = StockMovement.objects.filter(
    item=item,
    period=nov_period
).order_by('timestamp')

print(f"Total movements: {movements.count()}")

if movements.exists():
    for m in movements:
        print(f"  {m.movement_type}: {m.quantity} servings")
        print(f"    Timestamp: {m.timestamp}")
        print(f"    Notes: {m.notes or 'N/A'}")
        print(f"    Reference: {m.reference or 'N/A'}")
        print()
else:
    print("  ✓ No movements found in November period")

print("=" * 80)

# Check movements by timestamp range (in case period is wrong)
print("\nSTOCK MOVEMENTS BY DATE RANGE:")
print("-" * 80)

movements_by_date = StockMovement.objects.filter(
    item=item,
    timestamp__gte=nov_period.start_date,
    timestamp__lte=nov_period.end_date
).order_by('timestamp')

print(f"Total movements by date: {movements_by_date.count()}")

if movements_by_date.exists():
    for m in movements_by_date:
        print(f"  {m.movement_type}: {m.quantity} servings")
        print(f"    Period: {m.period.period_name if m.period else 'None'}")
        print(f"    Timestamp: {m.timestamp}")
        print(f"    Notes: {m.notes or 'N/A'}")
        print()
else:
    print("  ✓ No movements found by date range")

print("=" * 80)

# Check stocktake line for B0012
print("\nSTOCKTAKE LINE FOR B0012:")
print("-" * 80)

line = StocktakeLine.objects.filter(
    stocktake=nov_stocktake,
    item=item
).first()

if line:
    print(f"Opening Qty: {line.opening_qty}")
    print(f"Purchases: {line.purchases}")
    print(f"Waste: {line.waste}")
    print(f"Transfers In: {line.transfers_in}")
    print(f"Transfers Out: {line.transfers_out}")
    print(f"Adjustments: {line.adjustments}")
    print(f"Expected Qty: {line.expected_qty}")
    print(f"Counted: {line.counted_full_units} + {line.counted_partial_units}")
    print()
    print(f"Opening Value: €{line.opening_value}")
    print(f"Purchases Value: €{line.purchases_value}")
    print(f"Expected Value: €{line.expected_value}")
    print(f"Counted Value: €{line.counted_value}")
    print(f"Variance Value: €{line.variance_value}")
else:
    print("❌ No stocktake line found for B0012")

print("=" * 80)
print("\nDIAGNOSIS:")
print("-" * 80)

if line and line.purchases > 0:
    print(f"⚠️  Line shows {line.purchases} purchases even though movements were deleted")
    print()
    print("Possible causes:")
    print("1. The purchases field is stored in database and not recalculated automatically")
    print("2. The line may have been populated before movements were deleted")
    print("3. The calculation logic may be using cached values")
    print()
    print("SOLUTION:")
    print("The purchases field needs to be recalculated from current movements.")
    print("This is typically done when:")
    print("  - Creating/updating/deleting movements through the API")
    print("  - Manually calling the recalculate endpoint")
    print("  - Re-populating the stocktake")
