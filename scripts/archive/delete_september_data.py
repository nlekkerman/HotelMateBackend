"""
Delete all September 2025 stocktake data (periods, snapshots, lines)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, Stocktake, StockSnapshot, StocktakeLine
)
from hotel.models import Hotel

print("=" * 80)
print("DELETE SEPTEMBER 2025 DATA")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Find September data
sept_period = StockPeriod.objects.filter(
    hotel=hotel,
    period_name__icontains='September 2025'
).first()

sept_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
).first()

# Count items to delete
snapshot_count = 0
line_count = 0

if sept_period:
    snapshot_count = StockSnapshot.objects.filter(period=sept_period).count()
    print(f"Found September Period (ID: {sept_period.id})")
    print(f"  - Snapshots to delete: {snapshot_count}")

if sept_stocktake:
    line_count = StocktakeLine.objects.filter(stocktake=sept_stocktake).count()
    print(f"Found September Stocktake (ID: {sept_stocktake.id})")
    print(f"  - Lines to delete: {line_count}")

print()

if not sept_period and not sept_stocktake:
    print("✓ No September data found - nothing to delete")
    exit(0)

# Confirm deletion
print("⚠️  This will DELETE:")
if sept_period:
    print(f"  - September Period (ID: {sept_period.id})")
    print(f"  - {snapshot_count} StockSnapshots")
if sept_stocktake:
    print(f"  - September Stocktake (ID: {sept_stocktake.id})")
    print(f"  - {line_count} StocktakeLines")
print()

response = input("Continue? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

print()
print("Deleting...")
print("-" * 80)

# Delete in correct order (child objects first)
deleted_counts = {
    'snapshots': 0,
    'lines': 0,
    'periods': 0,
    'stocktakes': 0
}

# Delete snapshots
if sept_period:
    deleted_counts['snapshots'] = StockSnapshot.objects.filter(
        period=sept_period
    ).delete()[0]
    print(f"✓ Deleted {deleted_counts['snapshots']} snapshots")

# Delete stocktake lines
if sept_stocktake:
    deleted_counts['lines'] = StocktakeLine.objects.filter(
        stocktake=sept_stocktake
    ).delete()[0]
    print(f"✓ Deleted {deleted_counts['lines']} stocktake lines")

# Delete stocktake
if sept_stocktake:
    sept_stocktake.delete()
    deleted_counts['stocktakes'] = 1
    print(f"✓ Deleted stocktake (ID: {sept_stocktake.id})")

# Delete period
if sept_period:
    sept_period.delete()
    deleted_counts['periods'] = 1
    print(f"✓ Deleted period (ID: {sept_period.id})")

print()
print("=" * 80)
print("DELETION COMPLETE")
print("=" * 80)
print(f"Periods deleted: {deleted_counts['periods']}")
print(f"Snapshots deleted: {deleted_counts['snapshots']}")
print(f"Stocktakes deleted: {deleted_counts['stocktakes']}")
print(f"Lines deleted: {deleted_counts['lines']}")
print()
print("✅ All September 2025 data has been deleted")
print("=" * 80)
