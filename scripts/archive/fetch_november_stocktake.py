"""
Fetch November 2025 stocktake and add counted numbers so it can be closed.
Following the same pattern as October 2025 stocktake creation.
"""
import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake, StocktakeLine
from hotel.models import Hotel
from django.utils import timezone

print("=" * 80)
print("FETCH NOVEMBER 2025 STOCKTAKE")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}")
print()

# Get November 2025 period
try:
    nov_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2025,
        month=11
    )
    print(f"✅ November 2025 period found")
    print(f"   Period ID: {nov_period.id}")
    print(f"   Name: {nov_period.period_name}")
    print(f"   Status: {'CLOSED' if nov_period.is_closed else 'OPEN'}")
    print(f"   Dates: {nov_period.start_date} to {nov_period.end_date}")
    print()
except StockPeriod.DoesNotExist:
    print("❌ November 2025 period not found!")
    exit(1)

# Check for snapshots
snapshots = StockSnapshot.objects.filter(
    hotel=hotel,
    period=nov_period
)
print(f"📸 Snapshots: {snapshots.count()}")
if snapshots.count() > 0:
    total_value = sum(s.closing_stock_value for s in snapshots)
    print(f"💰 Total Snapshot Value: €{total_value:,.2f}")
print()

# Check for existing stocktake
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=nov_period.start_date,
    period_end=nov_period.end_date
).first()

if stocktake:
    print(f"✅ Stocktake exists")
    print(f"   Stocktake ID: {stocktake.id}")
    print(f"   Status: {stocktake.status}")
    print(f"   Lines: {stocktake.lines.count()}")
    print()
    
    # Check if lines have counted values
    lines_with_counted = stocktake.lines.filter(
        counted_full_units__gt=0
    ).count()
    lines_without_counted = stocktake.lines.filter(
        counted_full_units=0,
        counted_partial_units=0
    ).count()
    
    print(f"📊 Lines Analysis:")
    print(f"   Total lines: {stocktake.lines.count()}")
    print(f"   Lines with counted values: {lines_with_counted}")
    print(f"   Lines without counted values: {lines_without_counted}")
    print()
else:
    print("❌ No stocktake exists for November 2025!")
    print()

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)

if not stocktake:
    print("1. Create November stocktake first")
    print("2. Then add counted values")
elif stocktake.status == Stocktake.APPROVED:
    print("✅ Stocktake is already APPROVED!")
elif lines_without_counted > 0:
    print("📝 Add counted values to stocktake lines")
    print()
    print("To populate counted values (like October):")
    print(f"   Use opening_qty as counted_qty for all lines")
    print()
    print("Would you like to:")
    print("1. Copy opening values to counted (for baseline)")
    print("2. Enter actual counted values manually")
else:
    print("✅ Lines have counted values")
    print("Ready to approve stocktake!")

print("=" * 80)
