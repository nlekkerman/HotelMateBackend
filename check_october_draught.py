"""
Fetch and display all draught beers from October 2025 stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockPeriod
from datetime import date

# Find October 2025 period
try:
    oct_period = StockPeriod.objects.get(
        year=2025,
        month=10,
        period_type='MONTH'
    )
    print(f'October 2025 Period Found:')
    print(f'  ID: {oct_period.id}')
    print(f'  Period: {oct_period.period_name}')
    print(f'  Dates: {oct_period.start_date} to {oct_period.end_date}')
    print(f'  Status: {"CLOSED" if oct_period.is_closed else "OPEN"}')
    print()
    
    # Find stocktake for October
    stocktake = Stocktake.objects.filter(
        period_start=oct_period.start_date,
        period_end=oct_period.end_date
    ).first()
    
    if stocktake:
        print(f'October Stocktake Found:')
        print(f'  ID: {stocktake.id}')
        print(f'  Status: {stocktake.status}')
        print(f'  Total Lines: {stocktake.lines.count()}')
        print()
        
        # Get draught beers (category D)
        draught_lines = stocktake.lines.filter(
            item__category__code='D'
        ).select_related('item').order_by('item__name')
        
        print(f'DRAUGHT BEERS ({draught_lines.count()} items):')
        print('=' * 100)
        
        for line in draught_lines:
            print(f'\n{line.item.sku} - {line.item.name}')
            print(f'  Size: {line.item.size} | UOM: {line.item.uom} pints/keg')
            print(f'  Opening: {line.opening_qty:.2f} pints')
            print(f'  Counted: {line.counted_full_units} kegs + {line.counted_partial_units} pints')
            print(f'  Counted Qty: {line.counted_qty:.2f} pints')
            print(f'  Valuation Cost: €{line.valuation_cost:.4f} per pint')
            print(f'  Counted Value: €{line.counted_value:.2f}')
            print(f'  Expected: {line.expected_qty:.2f} pints')
            print(f'  Variance: {line.variance_qty:.2f} pints (€{line.variance_value:.2f})')
            print('-' * 100)
        
        print(f'\nTotal Draught Items: {draught_lines.count()}')
        
    else:
        print('No stocktake found for October 2025')
        
except StockPeriod.DoesNotExist:
    print('October 2025 period not found')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
