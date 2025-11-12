"""
Check existing stocktakes and simulate repopulation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockSnapshot, StockPeriod
from datetime import date

print("="*60)
print("EXISTING STOCKTAKES")
print("="*60)

stocktakes = Stocktake.objects.all().order_by('period_start')
for st in stocktakes:
    print(f"\nStocktake #{st.id}:")
    print(f"  Period: {st.period_start} to {st.period_end}")
    print(f"  Status: {st.status}")
    print(f"  Lines: {st.lines.count()}")
    
    if st.lines.exists():
        sample = st.lines.first()
        print(f"  Sample opening: {sample.opening_qty}")
        print(f"  Sample counted: {sample.counted_qty}")

print("\n" + "="*60)
print("STOCK SNAPSHOTS (Closing Stock)")
print("="*60)

periods = StockPeriod.objects.all().order_by('end_date')
for period in periods:
    snapshots = StockSnapshot.objects.filter(period=period)
    print(f"\nPeriod: {period.period_name} ({period.start_date} to {period.end_date})")
    print(f"  Status: {'CLOSED' if period.is_closed else 'OPEN'}")
    print(f"  Snapshots: {snapshots.count()}")
    
    if snapshots.exists():
        sample = snapshots.first()
        print(f"  Sample item: {sample.item.sku}")
        print(f"  Sample closing: {sample.closing_partial_units} servings")

print("\n" + "="*60)
print("NOVEMBER OPENING STOCK SIMULATION")
print("="*60)

# Find October's closing stock for first 3 items
november_start = date(2025, 11, 1)
print(f"\nLooking for previous period ending before {november_start}...")

from stock_tracker.models import StockItem
items = StockItem.objects.all()[:3]

for item in items:
    print(f"\n{item.sku} - {item.name}:")
    
    # Find previous snapshot
    prev_snapshot = StockSnapshot.objects.filter(
        item=item,
        period__end_date__lt=november_start,
        period__hotel=item.hotel
    ).order_by('-period__end_date').first()
    
    if prev_snapshot:
        print(f"  ✓ Found October closing: {prev_snapshot.closing_partial_units}")
        print(f"    Period: {prev_snapshot.period.period_name}")
        print(f"  → November opening would be: {prev_snapshot.closing_partial_units}")
    else:
        print(f"  ✗ No previous snapshot found")
        print(f"  → Would use current stock: {item.total_stock_in_servings}")
