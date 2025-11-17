"""
Check what closing stock exists in January for all categories
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod
from hotel.models import Hotel

hotel = Hotel.objects.first()

# Get January period
jan_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=1, period_type='MONTHLY'
)

print(f"\n{'='*80}")
print(f"JANUARY 2025 CLOSING STOCK SNAPSHOTS")
print(f"{'='*80}\n")

# Get all snapshots
snapshots = StockSnapshot.objects.filter(period=jan_period)

# Group by category
categories = {}
for snap in snapshots:
    cat = snap.item.category.code
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(snap)

print(f"Total snapshots: {snapshots.count()}\n")

for cat_code, cat_snaps in sorted(categories.items()):
    cat_name = cat_snaps[0].item.category.name
    print(f"\n{cat_code} - {cat_name}: {len(cat_snaps)} items")
    print("-" * 80)
    
    for snap in cat_snaps[:3]:  # Show first 3 items
        print(f"  {snap.item.sku} - {snap.item.name}")
        print(f"    Full: {snap.closing_full_units}, Partial: {snap.closing_partial_units}")
        print(f"    Value: €{snap.closing_stock_value}")
    
    if len(cat_snaps) > 3:
        print(f"  ... and {len(cat_snaps) - 3} more items")

print(f"\n{'='*80}\n")
