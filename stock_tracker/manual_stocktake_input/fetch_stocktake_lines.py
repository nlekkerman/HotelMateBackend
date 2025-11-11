"""
Fetch first stocktake lines to see what numbers are in closing quantities
"""
import os
import sys
import django
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("FETCHING OCTOBER STOCKTAKE LINES")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get October stocktake
from datetime import date
stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=date(2025, 10, 1),
    period_end=date(2025, 10, 31)
).first()

if not stocktake:
    print("❌ No October stocktake found!")
    exit()

print(f"Stocktake ID: {stocktake.id}")
print(f"Status: {stocktake.status}")
print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
print()

# Get first 20 lines
lines = StocktakeLine.objects.filter(
    stocktake=stocktake
).select_related('item')[:20]

print(f"Total lines: {StocktakeLine.objects.filter(stocktake=stocktake).count()}")
print()
print("First 20 lines:")
print("-" * 100)
print(f"{'SKU':<20} {'Category':<10} {'Opening':<12} {'Counted Full':<15} {'Counted Partial':<18} {'Cost':<10}")
print("-" * 100)

for line in lines:
    print(f"{line.item.sku:<20} {line.item.category_id:<10} "
          f"{line.opening_qty:<12.2f} {line.counted_full_units:<15.2f} "
          f"{line.counted_partial_units:<18.4f} €{line.valuation_cost:<10.4f}")

print()
print("=" * 100)
print()

# Check if any lines have counted values
lines_with_counts = StocktakeLine.objects.filter(
    stocktake=stocktake
).exclude(
    counted_full_units=0,
    counted_partial_units=0
).count()

print(f"Lines with counted values (non-zero): {lines_with_counts}")
print()

# Compare with StockSnapshot
print("COMPARING WITH STOCK SNAPSHOTS")
print("-" * 100)

for line in lines[:10]:
    # Get the corresponding period
    from stock_tracker.models import StockPeriod
    period = StockPeriod.objects.filter(
        hotel=hotel,
        start_date=stocktake.period_start,
        end_date=stocktake.period_end
    ).first()
    
    if not period:
        continue
        
    snapshot = StockSnapshot.objects.filter(
        period=period,
        item=line.item
    ).first()
    
    if snapshot:
        print(f"\n{line.item.sku}:")
        print(f"  Line - Opening: {line.opening_qty:.2f}, "
              f"Counted Full: {line.counted_full_units:.2f}, "
              f"Counted Partial: {line.counted_partial_units:.4f}")
        print(f"  Snapshot - Full: {snapshot.closing_full_units:.2f}, "
              f"Partial: {snapshot.closing_partial_units:.4f}, "
              f"Value: €{snapshot.closing_stock_value:.2f}")

print()
print("=" * 100)
