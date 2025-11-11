"""
Verify October opening = September closing (100% match required)
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
print("VERIFICATION: October Opening = September Closing")
print("=" * 100)
print()

hotel = Hotel.objects.first()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)
print(f"September Period ID: {sept_period.id}")

# Get October stocktake
oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)
oct_stocktake = Stocktake.objects.get(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date
)
print(f"October Stocktake ID: {oct_stocktake.id}")
print()

# Get all September snapshots
sept_snapshots = StockSnapshot.objects.filter(
    period=sept_period
).select_related('item').order_by('item__sku')

print(f"September snapshots: {sept_snapshots.count()}")

# Get all October lines
oct_lines = StocktakeLine.objects.filter(
    stocktake=oct_stocktake
).select_related('item').order_by('item__sku')

print(f"October lines: {oct_lines.count()}")
print()

if sept_snapshots.count() != oct_lines.count():
    print(f"❌ COUNT MISMATCH: {sept_snapshots.count()} vs {oct_lines.count()}")
    exit(1)

print("Checking item by item...")
print("-" * 100)

mismatches = []
matches = 0

for sept_snap in sept_snapshots:
    # Find matching October line
    oct_line = oct_lines.filter(item=sept_snap.item).first()
    
    if not oct_line:
        mismatches.append(f"Missing: {sept_snap.item.sku}")
        continue
    
    # Calculate September closing in servings
    sept_servings = sept_snap.total_servings
    
    # October opening should equal September closing
    oct_opening = oct_line.opening_qty
    
    # Compare
    diff = abs(sept_servings - oct_opening)
    
    if diff > Decimal('0.001'):  # Allow tiny rounding
        mismatches.append(
            f"{sept_snap.item.sku}: Sept closing={sept_servings}, "
            f"Oct opening={oct_opening}, diff={diff}"
        )
    else:
        matches += 1

print(f"✓ Matched items: {matches}")
print(f"❌ Mismatches: {len(mismatches)}")
print()

if mismatches:
    print("MISMATCHES FOUND:")
    print("-" * 100)
    for m in mismatches[:20]:  # Show first 20
        print(f"  {m}")
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more")
    print()
    print("❌ VERIFICATION FAILED - Opening != Closing")
else:
    print("✅ SUCCESS - October opening = September closing (100% match)")

print()

# Show category totals
print("=" * 100)
print("CATEGORY TOTALS COMPARISON")
print("=" * 100)
print()

categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

print(f"{'Category':<30} {'Sept Closing':<15} {'Oct Opening':<15} "
      f"{'Difference':<15}")
print("-" * 100)

for cat_code, cat_name in categories.items():
    # September closing total
    sept_total = Decimal('0.00')
    for snap in sept_snapshots.filter(item__category_id=cat_code):
        sept_total += snap.closing_stock_value
    
    # October opening total
    oct_total = Decimal('0.00')
    for line in oct_lines.filter(item__category_id=cat_code):
        oct_total += line.opening_qty * line.valuation_cost
    
    diff = oct_total - sept_total
    status = "✓" if abs(diff) < 1 else "❌"
    
    print(f"{status} {cat_name:<27} €{sept_total:>13.2f} "
          f"€{oct_total:>13.2f} €{diff:>13.2f}")

print()
print("=" * 100)
