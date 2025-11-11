"""
Sync September StockSnapshot closing quantities to StocktakeLine counted quantities
"""
import os
import sys
import django

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockSnapshot, StockPeriod
from hotel.models import Hotel
from datetime import date

print("=" * 100)
print("SYNCING SEPTEMBER STOCK SNAPSHOTS TO STOCKTAKE LINES")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get September stocktake and period
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=date(2025, 9, 1),
    period_end=date(2025, 9, 30)
).first()

if not stocktake:
    print("❌ No September stocktake found!")
    exit()

period = StockPeriod.objects.filter(
    hotel=hotel,
    start_date=stocktake.period_start,
    end_date=stocktake.period_end
).first()

if not period:
    print("❌ No September period found!")
    exit()

print(f"Stocktake ID: {stocktake.id}")
print(f"Status: {stocktake.status}")
print(f"Period: {period.period_name}")
print()

# Get all lines
lines = StocktakeLine.objects.filter(stocktake=stocktake).select_related('item')

print(f"Total lines: {lines.count()}")
print()

updated = 0
skipped = 0

for line in lines:
    # Get corresponding snapshot
    snapshot = StockSnapshot.objects.filter(
        period=period,
        item=line.item
    ).first()
    
    if not snapshot:
        print(f"⚠️  No snapshot for {line.item.sku}")
        skipped += 1
        continue
    
    # Copy snapshot closing to line counted
    line.counted_full_units = snapshot.closing_full_units
    line.counted_partial_units = snapshot.closing_partial_units
    line.save()
    
    updated += 1
    
    if updated <= 10:
        print(f"✓ {line.item.sku}: "
              f"Full {snapshot.closing_full_units:.2f}, "
              f"Partial {snapshot.closing_partial_units:.4f}")

print()
print("-" * 100)
print(f"Updated: {updated} lines")
print(f"Skipped: {skipped} lines")
print()
print("✅ September stocktake lines updated with counted values from snapshots!")
print()
print("=" * 100)
