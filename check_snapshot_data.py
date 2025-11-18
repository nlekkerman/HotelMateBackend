"""
Check StockSnapshot data - why beers populate but others don't
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal

print('='*100)
print('CHECKING STOCKSNAPSHOT DATA - THE REAL PROBLEM')
print('='*100)

# Get the most recent closed period
closed_period = StockPeriod.objects.filter(
    hotel_id=2,
    is_closed=True
).order_by('-end_date').first()

if not closed_period:
    print('\n❌ No closed periods found!')
    exit()

print(f'\nMost recent closed period: {closed_period.period_name}')
print(f'  Start: {closed_period.start_date}')
print(f'  End: {closed_period.end_date}')
print(f'  Closed: {closed_period.is_closed}')

# Get snapshots by category
print('\n' + '='*100)
print('SNAPSHOTS BY CATEGORY')
print('='*100)

categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals'
}

for cat_id, cat_name in categories.items():
    snapshots = StockSnapshot.objects.filter(
        period=closed_period,
        item__category_id=cat_id
    )
    
    total = snapshots.count()
    with_closing = snapshots.exclude(
        closing_full_units=0,
        closing_partial_units=0
    ).count()
    
    print(f'\n{cat_name} ({cat_id}):')
    print(f'  Total snapshots: {total}')
    print(f'  With closing stock: {with_closing}')
    print(f'  Empty (both 0): {total - with_closing}')
    
    if total > 0:
        # Show first few with stock
        with_stock = snapshots.exclude(
            closing_full_units=0,
            closing_partial_units=0
        )[:3]
        
        if with_stock.exists():
            print(f'  Sample with closing stock:')
            for snap in with_stock:
                print(f'    {snap.item.sku}: full={snap.closing_full_units}, partial={snap.closing_partial_units}')

print('\n' + '='*100)
print('THE ANSWER!')
print('='*100)

# Compare
draught_snaps = StockSnapshot.objects.filter(
    period=closed_period,
    item__category_id='D'
).exclude(closing_full_units=0, closing_partial_units=0).count()

bottled_snaps = StockSnapshot.objects.filter(
    period=closed_period,
    item__category_id='B'
).exclude(closing_full_units=0, closing_partial_units=0).count()

spirits_snaps = StockSnapshot.objects.filter(
    period=closed_period,
    item__category_id='S'
).exclude(closing_full_units=0, closing_partial_units=0).count()

wine_snaps = StockSnapshot.objects.filter(
    period=closed_period,
    item__category_id='W'
).exclude(closing_full_units=0, closing_partial_units=0).count()

minerals_snaps = StockSnapshot.objects.filter(
    period=closed_period,
    item__category_id='M'
).exclude(closing_full_units=0, closing_partial_units=0).count()

print(f'\nClosed period snapshots WITH closing stock:')
print(f'  Draught: {draught_snaps}')
print(f'  Bottled: {bottled_snaps}')
print(f'  Spirits: {spirits_snaps}')
print(f'  Wine: {wine_snaps}')
print(f'  Minerals: {minerals_snaps}')

if spirits_snaps == 0 and wine_snaps == 0 and minerals_snaps == 0:
    print('\n' + '='*100)
    print('🎯 FOUND THE PROBLEM!')
    print('='*100)
    print(f'\nIn period {closed_period.period_name}:')
    print(f'  ✅ Beers have closing stock in snapshots')
    print(f'  ❌ Other categories have NO closing stock in snapshots')
    print()
    print('This means:')
    print('  1. When stocktake was approved, snapshots were NOT updated for other categories')
    print('  2. The approve_stocktake() function may have a bug')
    print('  3. Or the snapshots were never created for non-beers')
    print()
    print('Next step: Check if the fix in OPENING_STOCK_FIX.md was applied!')
else:
    print(f'\n✅ All categories have snapshots with closing stock')
    print('The problem must be elsewhere')
