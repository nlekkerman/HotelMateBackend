"""
Copy October 2025 CLOSING stock to November 2025 OPENING stock
Uses the counted values from October stocktake as November opening
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("COPYING OCTOBER CLOSING STOCK TO NOVEMBER OPENING STOCK")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get October and November periods
oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)
nov_period = StockPeriod.objects.filter(
    hotel=hotel, year=2025, month=11, period_type='MONTHLY'
).first()

if not nov_period:
    print("November period not found - please create it first")
    exit(1)

print(f"October Period: {oct_period.start_date} to {oct_period.end_date}")
print(f"November Period: {nov_period.start_date} to {nov_period.end_date}")
print()

# Get all October snapshots
oct_snapshots = StockSnapshot.objects.filter(period=oct_period).select_related('item')

updated = 0
not_found = []
total_value = Decimal('0.00')

print(f"Processing {oct_snapshots.count()} items...")
print()

for oct_snap in oct_snapshots:
    # Find corresponding November snapshot
    nov_snap = StockSnapshot.objects.filter(
        period=nov_period,
        item=oct_snap.item
    ).first()
    
    if not nov_snap:
        not_found.append(oct_snap.item.sku)
        print(f"⚠️  {oct_snap.item.sku} not found in November period")
        continue
    
    # Copy October CLOSING to November snapshot as CLOSING
    # (November opening is implicitly October's closing)
    nov_snap.closing_full_units = oct_snap.closing_full_units
    nov_snap.closing_partial_units = oct_snap.closing_partial_units
    nov_snap.closing_stock_value = oct_snap.closing_stock_value
    nov_snap.save()
    
    total_value += oct_snap.closing_stock_value
    updated += 1
    
    # Show items with stock
    if oct_snap.closing_full_units > 0 or oct_snap.closing_partial_units > 0:
        category = oct_snap.item.sku[0]  # First letter (B, D, M, S, W)
        
        if category == 'D':  # Draught - kegs + pints
            print(f"✓ {oct_snap.item.sku}: {oct_snap.closing_full_units} kegs + "
                  f"{oct_snap.closing_partial_units} pints = €{oct_snap.closing_stock_value}")
        elif category in ['B', 'M']:  # Bottled/Minerals - cases + bottles
            print(f"✓ {oct_snap.item.sku}: {oct_snap.closing_full_units} cases + "
                  f"{oct_snap.closing_partial_units} bottles = €{oct_snap.closing_stock_value}")
        elif category in ['S', 'W']:  # Spirits/Wine - bottles + fractional
            print(f"✓ {oct_snap.item.sku}: {oct_snap.closing_full_units} + "
                  f"{oct_snap.closing_partial_units} = €{oct_snap.closing_stock_value}")

print()
print("-" * 100)
print(f"✅ Updated: {updated} items")
print(f"⚠️  Not found: {len(not_found)} items")
if not_found:
    print(f"Missing SKUs: {', '.join(not_found)}")
print()
print(f"Total Opening Stock Value for November: €{total_value:.2f}")
print()
print("=" * 100)
print("November opening stock is now set from October closing stock!")
print("=" * 100)
