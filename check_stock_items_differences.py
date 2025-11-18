"""
Check differences between beer stock items and other category stock items
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

print('='*100)
print('CHECKING STOCK ITEMS - BEERS vs OTHER CATEGORIES')
print('='*100)

# Get counts
draught_count = StockItem.objects.filter(category_id='D', active=True).count()
bottled_count = StockItem.objects.filter(category_id='B', active=True).count()
spirits_count = StockItem.objects.filter(category_id='S', active=True).count()
wine_count = StockItem.objects.filter(category_id='W', active=True).count()
minerals_count = StockItem.objects.filter(category_id='M', active=True).count()

print(f'\nTOTAL ITEMS:')
print(f'  Draught Beer (D): {draught_count}')
print(f'  Bottled Beer (B): {bottled_count}')
print(f'  Spirits (S): {spirits_count}')
print(f'  Wine (W): {wine_count}')
print(f'  Minerals (M): {minerals_count}')

print('\n' + '='*100)
print('FIELD COMPARISON - Sample from each category')
print('='*100)

# Check a sample from each
categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals'
}

for cat_id, cat_name in categories.items():
    item = StockItem.objects.filter(category_id=cat_id, active=True).first()
    
    if item:
        print(f'\n{cat_name} ({cat_id}) - {item.sku} - {item.name}')
        print(f'  current_full_units: {item.current_full_units}')
        print(f'  current_partial_units: {item.current_partial_units}')
        print(f'  unit_cost: {item.unit_cost}')
        print(f'  cost_per_serving: {item.cost_per_serving}')
        print(f'  uom: {item.uom}')
        print(f'  size: {item.size}')
        
        # Check if property exists
        try:
            servings = item.total_stock_in_servings
            print(f'  total_stock_in_servings: {servings}')
        except Exception as e:
            print(f'  total_stock_in_servings: ERROR - {e}')

print('\n' + '='*100)
print('CHECKING: Do all items have current_full_units and current_partial_units?')
print('='*100)

for cat_id, cat_name in categories.items():
    items = StockItem.objects.filter(category_id=cat_id, active=True)
    
    missing_full = items.filter(current_full_units__isnull=True).count()
    missing_partial = items.filter(current_partial_units__isnull=True).count()
    zero_both = items.filter(current_full_units=0, current_partial_units=0).count()
    has_stock = items.exclude(current_full_units=0, current_partial_units=0).count()
    
    print(f'\n{cat_name} ({cat_id}): {items.count()} items')
    print(f'  Missing current_full_units: {missing_full}')
    print(f'  Missing current_partial_units: {missing_partial}')
    print(f'  Both zero: {zero_both}')
    print(f'  Has stock (non-zero): {has_stock}')

print('\n' + '='*100)
print('CHECKING: Field types')
print('='*100)

for cat_id, cat_name in categories.items():
    item = StockItem.objects.filter(category_id=cat_id, active=True).first()
    if item:
        print(f'\n{cat_name} - {item.sku}')
        print(f'  current_full_units: {type(item.current_full_units).__name__} = {item.current_full_units}')
        print(f'  current_partial_units: {type(item.current_partial_units).__name__} = {item.current_partial_units}')
        print(f'  unit_cost: {type(item.unit_cost).__name__} = {item.unit_cost}')
        print(f'  cost_per_serving: {type(item.cost_per_serving).__name__} = {item.cost_per_serving}')
        print(f'  uom: {type(item.uom).__name__} = {item.uom}')

print('\n' + '='*100)
print('COMPARING: All fields between beers and others')
print('='*100)

beer_item = StockItem.objects.filter(category_id='B', active=True).first()
spirit_item = StockItem.objects.filter(category_id='S', active=True).first()
wine_item = StockItem.objects.filter(category_id='W', active=True).first()
mineral_item = StockItem.objects.filter(category_id='M', active=True).first()

if beer_item and spirit_item:
    print('\nBEER vs SPIRITS - Field comparison:')
    print(f'  Beer has: {dir(beer_item)[:10]}...')
    print(f'  Spirit has: {dir(spirit_item)[:10]}...')
    
    # Check model fields
    beer_fields = [f.name for f in beer_item._meta.get_fields()]
    spirit_fields = [f.name for f in spirit_item._meta.get_fields()]
    
    print(f'\n  Same model fields? {beer_fields == spirit_fields}')
    print(f'  Total fields: {len(beer_fields)}')

print('\n' + '='*100)
print('KEY QUESTION: Is there ANY difference in StockItem structure?')
print('='*100)

# They should all be the same - it's the same model!
print('\nANSWER: NO! All categories use the SAME StockItem model.')
print('All items have the same fields:')
print('  - current_full_units')
print('  - current_partial_units')
print('  - unit_cost')
print('  - cost_per_serving')
print('  - uom')
print('  - etc.')

print('\nThe ONLY differences are:')
print('  1. category_id field value (D, B, S, W, M)')
print('  2. How the total_stock_in_servings property CALCULATES')
print('  3. How counted_qty in StocktakeLine CALCULATES')

print('\n' + '='*100)
print('So why are beers populating but not others?')
print('='*100)
print('\nIt must be in:')
print('  1. The calculation logic (total_servings property)')
print('  2. The data (closing_full_units, closing_partial_units in snapshots)')
print('  3. The snapshot creation/update process')
print('\nLet me check the actual data...')
