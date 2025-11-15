"""
Create stocktake for October 2025 period
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod, StocktakeLine, StockItem
from hotel.models import Hotel

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
    
    # Check if stocktake already exists
    existing_stocktake = Stocktake.objects.filter(
        period_start=oct_period.start_date,
        period_end=oct_period.end_date
    ).first()
    
    if existing_stocktake:
        print(f'Stocktake already exists for October 2025:')
        print(f'  ID: {existing_stocktake.id}')
        print(f'  Status: {existing_stocktake.status}')
        print(f'  Total Lines: {existing_stocktake.lines.count()}')
        
        # Show draught beers
        draught_lines = existing_stocktake.lines.filter(
            item__category__code='D'
        ).select_related('item').order_by('item__name')
        
        print(f'\nDRAUGHT BEERS ({draught_lines.count()} items):')
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
    else:
        print('Creating new stocktake for October 2025...')
        
        # Get hotel
        hotel = oct_period.hotel
        
        # Create stocktake
        stocktake = Stocktake.objects.create(
            hotel=hotel,
            period_start=oct_period.start_date,
            period_end=oct_period.end_date,
            status='DRAFT'
        )
        print(f'Created stocktake ID: {stocktake.id}')
        
        # Get all active stock items
        items = StockItem.objects.filter(hotel=hotel, active=True)
        print(f'Found {items.count()} active stock items')
        
        # Create stocktake lines
        lines_created = 0
        for item in items:
            # Get opening stock from item's current stock
            opening_qty = item.total_stock_in_servings
            
            StocktakeLine.objects.create(
                stocktake=stocktake,
                item=item,
                opening_qty=opening_qty,
                purchases=0,
                waste=0,
                transfers_in=0,
                transfers_out=0,
                adjustments=0,
                counted_full_units=0,
                counted_partial_units=0,
                valuation_cost=item.cost_per_serving
            )
            lines_created += 1
        
        print(f'Created {lines_created} stocktake lines')
        
        # Show draught beers
        draught_lines = stocktake.lines.filter(
            item__category__code='D'
        ).select_related('item').order_by('item__name')
        
        print(f'\nDRAUGHT BEERS ({draught_lines.count()} items):')
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
        
        print(f'\nStocktake created successfully!')
        
except StockPeriod.DoesNotExist:
    print('October 2025 period not found')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
