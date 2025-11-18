"""
Check the relationship between Stocktakes and StockPeriods
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod, StockSnapshot

print('='*100)
print('STOCKTAKES VS PERIODS VS SNAPSHOTS')
print('='*100)

stocktakes = Stocktake.objects.filter(hotel_id=2).order_by('period_start')
periods = StockPeriod.objects.filter(hotel_id=2).order_by('start_date')

print('\n' + '='*100)
print('STOCKTAKES')
print('='*100)
for st in stocktakes:
    print(f'\nStocktake ID: {st.id}')
    print(f'  Dates: {st.period_start} to {st.period_end}')
    print(f'  Status: {st.status}')
    print(f'  Lines: {st.lines.count()}')
    
    # Check if there's a matching period
    try:
        period = StockPeriod.objects.get(
            hotel_id=2,
            start_date=st.period_start,
            end_date=st.period_end
        )
        print(f'  ✅ Period ID: {period.id} (closed={period.is_closed})')
        
        # Check snapshots for this period
        snapshots = StockSnapshot.objects.filter(
            hotel_id=2,
            period_id=period.id
        )
        print(f'  Snapshots: {snapshots.count()}')
        
    except StockPeriod.DoesNotExist:
        print(f'  ❌ NO matching period found')

print('\n' + '='*100)
print('PERIODS')
print('='*100)
for period in periods:
    print(f'\nPeriod ID: {period.id}')
    print(f'  Dates: {period.start_date} to {period.end_date}')
    print(f'  Closed: {period.is_closed}')
    
    # Check snapshots
    snapshots = StockSnapshot.objects.filter(
        hotel_id=2,
        period_id=period.id
    )
    print(f'  Snapshots: {snapshots.count()}')
    
    # Check for matching stocktake
    try:
        stocktake = Stocktake.objects.get(
            hotel_id=2,
            period_start=period.start_date,
            period_end=period.end_date
        )
        print(f'  ✅ Stocktake ID: {stocktake.id} ({stocktake.status})')
    except Stocktake.DoesNotExist:
        print('  ❌ NO matching stocktake found')

print('\n' + '='*100)
print('KEY QUESTION')
print('='*100)
print('\nWhen approve_stocktake() creates snapshots, which period_id does it use?')
print('Does it use stocktake dates or look up the matching StockPeriod?')
