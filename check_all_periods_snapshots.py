"""
Check all periods and their snapshots
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot

print('='*100)
print('ALL PERIODS AND THEIR SNAPSHOTS')
print('='*100)

periods = StockPeriod.objects.filter(hotel_id=2).order_by('start_date')

for p in periods:
    print(f'\n{p.period_name} ({p.start_date} to {p.end_date})')
    print(f'  Closed: {p.is_closed}')
    
    total = StockSnapshot.objects.filter(period=p).count()
    d_count = StockSnapshot.objects.filter(period=p, item__category_id='D').count()
    b_count = StockSnapshot.objects.filter(period=p, item__category_id='B').count()
    s_count = StockSnapshot.objects.filter(period=p, item__category_id='S').count()
    w_count = StockSnapshot.objects.filter(period=p, item__category_id='W').count()
    m_count = StockSnapshot.objects.filter(period=p, item__category_id='M').count()
    
    print(f'  Total snapshots: {total}')
    print(f'  By category: D={d_count}, B={b_count}, S={s_count}, W={w_count}, M={m_count}')
    
    # Check which have closing stock
    if total > 0:
        with_stock_d = StockSnapshot.objects.filter(
            period=p, item__category_id='D'
        ).exclude(closing_full_units=0, closing_partial_units=0).count()
        
        with_stock_b = StockSnapshot.objects.filter(
            period=p, item__category_id='B'
        ).exclude(closing_full_units=0, closing_partial_units=0).count()
        
        with_stock_s = StockSnapshot.objects.filter(
            period=p, item__category_id='S'
        ).exclude(closing_full_units=0, closing_partial_units=0).count()
        
        with_stock_w = StockSnapshot.objects.filter(
            period=p, item__category_id='W'
        ).exclude(closing_full_units=0, closing_partial_units=0).count()
        
        with_stock_m = StockSnapshot.objects.filter(
            period=p, item__category_id='M'
        ).exclude(closing_full_units=0, closing_partial_units=0).count()
        
        print(f'  With closing stock: D={with_stock_d}, B={with_stock_b}, S={with_stock_s}, W={with_stock_w}, M={with_stock_m}')

print('\n' + '='*100)
print('SUMMARY')
print('='*100)
print('\nThis shows which periods have snapshots and which categories have closing stock data.')
