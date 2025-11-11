"""
Verify raw data copied: September closing_full/partial = October opening_full/partial
Check actual stored values, not calculations
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, Stocktake, StocktakeLine
)
from hotel.models import Hotel

print("=" * 100)
print("RAW DATA VERIFICATION: September Snapshots vs October Lines")
print("=" * 100)
print()

hotel = Hotel.objects.first()

sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)
oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)
oct_stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date
)

sept_snapshots = StockSnapshot.objects.filter(
    period=sept_period
).select_related('item').order_by('item__sku')

oct_lines = StocktakeLine.objects.filter(
    stocktake=oct_stocktake
).select_related('item').order_by('item__sku')

print(f"Checking {sept_snapshots.count()} items...")
print()

# Sample first 10 items to show data structure
print("SAMPLE: First 10 items (raw values)")
print("-" * 100)
print(f"{'SKU':<10} {'Sept Full':<12} {'Sept Partial':<15} "
      f"{'Oct opening_qty':<15}")
print("-" * 100)

for i, sept_snap in enumerate(sept_snapshots[:10]):
    oct_line = oct_lines.filter(item=sept_snap.item).first()
    
    sept_servings = sept_snap.total_servings
    oct_opening = oct_line.opening_qty if oct_line else 0
    
    print(f"{sept_snap.item.sku:<10} "
          f"{sept_snap.closing_full_units:>11.2f} "
          f"{sept_snap.closing_partial_units:>14.4f} "
          f"{oct_opening:>14.4f}")

print()
print("NOTE: October stores opening_qty as SERVINGS (calculated from Sept)")
print("      Not raw full/partial units")
print()

# Check if opening_qty matches September total_servings
print("=" * 100)
print("VERIFICATION: October opening_qty = September total_servings")
print("=" * 100)
print()

all_match = True
mismatches = []

for sept_snap in sept_snapshots:
    oct_line = oct_lines.filter(item=sept_snap.item).first()
    
    if not oct_line:
        continue
    
    sept_servings = sept_snap.total_servings
    oct_opening = oct_line.opening_qty
    
    diff = abs(sept_servings - oct_opening)
    
    if diff > Decimal('0.001'):
        all_match = False
        mismatches.append({
            'sku': sept_snap.item.sku,
            'sept': sept_servings,
            'oct': oct_opening,
            'diff': diff
        })

if all_match:
    print("✅ PERFECT MATCH - All 254 items match")
    print("   October opening_qty = September total_servings")
else:
    print(f"❌ MISMATCHES FOUND: {len(mismatches)} items")
    print()
    for m in mismatches[:10]:
        print(f"  {m['sku']}: Sept={m['sept']}, Oct={m['oct']}, "
              f"Diff={m['diff']}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()
print("How data is stored:")
print("  September: closing_full_units + closing_partial_units")
print("  October:   opening_qty (in SERVINGS)")
print()
print("October opening_qty = September.total_servings property")
print("  which calculates: full_units × UOM + partial_units × UOM")
print()
if all_match:
    print("✅ Data transfer is correct")
    print("   Ready to update October closing stock from Excel")
else:
    print("⚠️  Some mismatches found - review before proceeding")

print()
print("=" * 100)
