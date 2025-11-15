"""
List all periods and stocktakes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake

print("=" * 100)
print("ALL PERIODS AND STOCKTAKES")
print("=" * 100)

periods = StockPeriod.objects.all().order_by('-year', '-month')

for period in periods:
    print(f'\nPeriod ID: {period.id}')
    print(f'  Period: {period.period_name}')
    print(f'  Dates: {period.start_date} to {period.end_date}')
    print(f'  Status: {"CLOSED" if period.is_closed else "OPEN"}')
    
    # Find matching stocktake
    stocktake = Stocktake.objects.filter(
        hotel=period.hotel,
        period_start=period.start_date,
        period_end=period.end_date
    ).first()
    
    if stocktake:
        print(f'  Stocktake ID: {stocktake.id}')
        print(f'  Stocktake Status: {stocktake.status}')
        print(f'  Total Lines: {stocktake.lines.count()}')
    else:
        print(f'  Stocktake: NO STOCKTAKE')
    
    print('-' * 100)

print(f'\nTotal Periods: {periods.count()}')
print(f'Total Stocktakes: {Stocktake.objects.count()}')
