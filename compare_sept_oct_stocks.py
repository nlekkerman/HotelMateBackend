import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod, StockItem
from decimal import Decimal

# Get September period
sept_period = StockPeriod.objects.filter(
    hotel__name='Hotel Killarney',
    start_date__year=2025,
    start_date__month=9
).first()

# Get October period
oct_period = StockPeriod.objects.filter(
    hotel__name='Hotel Killarney',
    start_date__year=2025,
    start_date__month=10
).first()

if not sept_period:
    print("❌ September period not found")
    exit()

if not oct_period:
    print("❌ October period not found")
    exit()

print(f"September period: {sept_period.start_date} to {sept_period.end_date}")
print(f"October period: {oct_period.start_date} to {oct_period.end_date}")

# Get all active items
items = StockItem.objects.filter(hotel__name='Hotel Killarney', active=True)
print(f"\nTotal active items: {items.count()}")

# Get September closing snapshots
sept_snapshots = StockSnapshot.objects.filter(
    period=sept_period,
    item__in=items
).select_related('item')

# Get October opening snapshots
oct_snapshots = StockSnapshot.objects.filter(
    period=oct_period,
    item__in=items
).select_related('item')

print(f"September closing snapshots: {sept_snapshots.count()}")
print(f"October opening snapshots: {oct_snapshots.count()}")

# Create dictionaries for comparison
sept_closing = {
    snap.item.sku: {
        'full': snap.closing_full_units,
        'partial': snap.closing_partial_units,
        'value': snap.closing_stock_value
    }
    for snap in sept_snapshots
}

# For October, check if period correctly references September as previous
# Get October's StocktakeLine to see opening_qty values
from stock_tracker.models import Stocktake, StocktakeLine

oct_stocktake = Stocktake.objects.filter(
    hotel__name='Hotel Killarney',
    period_start=oct_period.start_date
).first()

print(f"\nOctober stocktake: {oct_stocktake}")

if oct_stocktake:
    oct_lines = StocktakeLine.objects.filter(stocktake=oct_stocktake).select_related('item')
    print(f"October stocktake lines: {oct_lines.count()}")
    
    oct_opening_from_stocktake = {
        line.item.sku: {
            'opening_qty': line.opening_qty,
            'full': line.counted_full_units or 0,
            'partial': line.counted_partial_units or 0
        }
        for line in oct_lines
    }
else:
    print("⚠️ No October stocktake found - October opening will be calculated from September closing")
    oct_opening_from_stocktake = {}

# Compare September closing with October opening
matches = 0
mismatches = []

for sku in sept_closing.keys():
    sept = sept_closing[sku]
    
    if oct_stocktake and sku in oct_opening_from_stocktake:
        oct_line = oct_opening_from_stocktake[sku]
        # Calculate expected opening_qty from September closing
        item = StockItem.objects.get(sku=sku, hotel__name='Hotel Killarney')
        expected_opening = sept['full'] * item.uom + sept['partial']
        
        if abs(oct_line['opening_qty'] - expected_opening) < 0.01:
            matches += 1
        else:
            mismatches.append({
                'sku': sku,
                'issue': 'Opening qty mismatch',
                'sept_full': sept['full'],
                'sept_partial': sept['partial'],
                'expected_opening_qty': expected_opening,
                'actual_opening_qty': oct_line['opening_qty']
            })
    else:
        # No October stocktake, just note we have September closing
        matches += 1

print(f"\n✅ Matching items: {matches}")
print(f"❌ Mismatches: {len(mismatches)}")

if mismatches:
    print("\n=== MISMATCHES ===")
    for i, mismatch in enumerate(mismatches[:20], 1):
        print(f"\n{i}. {mismatch['sku']} - {mismatch['issue']}")
        if 'expected_opening_qty' in mismatch:
            print(f"   Sept closing: {mismatch['sept_full']} full + {mismatch['sept_partial']} partial")
            print(f"   Expected opening qty: {mismatch['expected_opening_qty']:.2f}")
            print(f"   Actual opening qty: {mismatch['actual_opening_qty']:.2f}")
    
    if len(mismatches) > 20:
        print(f"\n... and {len(mismatches) - 20} more mismatches")
else:
    if oct_stocktake:
        print("\n✅ All September closing stocks match October opening stocks!")
    else:
        print("\n✅ September closing stock ready - no October stocktake yet to compare")

# Calculate totals
sept_total = sum(snap['value'] for snap in sept_closing.values())

print(f"\n=== SEPTEMBER CLOSING TOTALS ===")
print(f"September closing value: €{sept_total:,.2f}")
print(f"Items with stock: {sum(1 for s in sept_closing.values() if s['value'] > 0)}/{len(sept_closing)}")
