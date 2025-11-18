"""
Check all stocktakes and their approval status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print('='*100)
print('ALL STOCKTAKES AND THEIR STATUS')
print('='*100)

stocktakes = Stocktake.objects.filter(hotel_id=2).order_by('period_start')

for st in stocktakes:
    print(f'\n{st.period_start} to {st.period_end}')
    print(f'  Status: {st.status}')
    print(f'  Total lines: {st.lines.count()}')
    
    d = st.lines.filter(item__category_id='D').count()
    b = st.lines.filter(item__category_id='B').count()
    s = st.lines.filter(item__category_id='S').count()
    w = st.lines.filter(item__category_id='W').count()
    m = st.lines.filter(item__category_id='M').count()
    
    print(f'  By category: D={d}, B={b}, S={s}, W={w}, M={m}')
    print(f'  Approved: {st.approved_at}')
    print(f'  Approved by: {st.approved_by}')
    
    # Check if lines have counted values
    lines_with_counted = st.lines.exclude(
        counted_full_units=0,
        counted_partial_units=0
    ).count()
    print(f'  Lines with counted stock: {lines_with_counted}')

print('\n' + '='*100)
print('KEY INSIGHT')
print('='*100)
print('\nWhen a stocktake is APPROVED, the approve_stocktake() function:')
print('  1. Loops through ALL stocktake lines')
print('  2. For EACH line, creates/updates a StockSnapshot')
print('  3. Saves counted_full_units and counted_partial_units to snapshot')
print('\nSo if January stocktake only has beer lines, only beer snapshots are created!')
print('If September stocktake has all categories, all snapshots are created!')
