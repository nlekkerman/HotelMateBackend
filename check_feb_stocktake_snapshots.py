"""
Check where the February stocktake snapshots went
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockSnapshot
from decimal import Decimal

print('='*100)
print('FEBRUARY STOCKTAKE ANALYSIS')
print('='*100)

stocktake = Stocktake.objects.get(id=37)
print(f'\nStocktake 37:')
print(f'  Dates: {stocktake.period_start} to {stocktake.period_end}')
print(f'  Status: {stocktake.status}')
print(f'  Approved: {stocktake.approved_at}')
print(f'  Lines: {stocktake.lines.count()}')

# Sample first 5 lines
print('\nFirst 5 stocktake lines:')
for line in stocktake.lines.all()[:5]:
    print(f'\n  Item: {line.item.name} (ID={line.item.id})')
    print(f'    Category: {line.item.category_id}')
    print(f'    Counted: {line.counted_full_units} full + '
          f'{line.counted_partial_units} partial')
    print(f'    Counted value: {line.counted_value}')
    
    # Search for snapshots of this item in ANY period
    snapshots = StockSnapshot.objects.filter(
        hotel_id=2,
        item_id=line.item.id
    ).order_by('period__start_date')
    
    print(f'    Snapshots found: {snapshots.count()}')
    for snap in snapshots:
        print(f'      Period {snap.period.start_date} to '
              f'{snap.period.end_date}: '
              f'closing={snap.closing_full_units}/{snap.closing_partial_units}')

print('\n' + '='*100)
print('HYPOTHESIS')
print('='*100)
print('\nPossibility 1: Period 29 did not exist when stocktake was approved')
print('Possibility 2: approve_stocktake() failed silently')
print('Possibility 3: Snapshots were created then deleted')
print('Possibility 4: Wrong period_id used (check if period IDs changed)')
