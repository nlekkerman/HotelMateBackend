"""
Update November 2025 Stocktake to pull opening stock from October 2025.
November stocktake was created before October stocktake existed,
so all opening_qty values are 0.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine
from decimal import Decimal

print("=" * 80)
print("UPDATE NOVEMBER 2025 OPENING STOCK FROM OCTOBER")
print("=" * 80)
print()

# Get November stocktake
nov_stocktake = Stocktake.objects.get(id=4)
print(f"November Stocktake (ID: {nov_stocktake.id})")
print(f"Period: {nov_stocktake.period_start} to {nov_stocktake.period_end}")
print(f"Lines: {nov_stocktake.lines.count()}")
print()

# Get October period
oct_period = StockPeriod.objects.filter(
    hotel=nov_stocktake.hotel,
    period_name="October 2025"
).first()

if not oct_period:
    print("ERROR: October 2025 Period not found!")
    exit(1)

print(f"October Period (ID: {oct_period.id})")
print(f"Snapshots: {oct_period.snapshots.count()}")
print()

# Update November lines with October closing stock
print("Updating November opening stock from October closing...")
updated_count = 0
zero_count = 0

for nov_line in nov_stocktake.lines.all():
    # Find corresponding October snapshot
    oct_snapshot = oct_period.snapshots.filter(item=nov_line.item).first()
    
    if oct_snapshot:
        # October closing becomes November opening
        nov_line.opening_qty = oct_snapshot.closing_partial_units
        nov_line.save()
        updated_count += 1
        
        if oct_snapshot.closing_partial_units > 0:
            zero_count += 1
    
    if updated_count % 50 == 0:
        print(f"  Updated {updated_count} lines...")

print(f"Updated {updated_count} lines")
print(f"Lines with non-zero opening: {zero_count}")
print()

# Verify a few samples
print("=" * 80)
print("VERIFICATION - Sample Items")
print("=" * 80)
print()

from stock_tracker.stock_serializers import StocktakeLineSerializer

sample_items = ['B0070', 'B0075', 'D0005']  # Budweiser, Bulmers, Sample draught
for sku in sample_items:
    line = nov_stocktake.lines.filter(item__sku=sku).first()
    if line:
        data = StocktakeLineSerializer(line).data
        print(f"{data['item_name']} ({data['item_sku']})")
        print(f"  Opening: {data['opening_display_full_units']} + "
              f"{data['opening_display_partial_units']} = {data['opening_qty']}")
        print(f"  Expected: {data['expected_display_full_units']} + "
              f"{data['expected_display_partial_units']} = {data['expected_qty']}")
        print()

print("=" * 80)
print("SUCCESS! November now has opening stock from October")
print("=" * 80)
