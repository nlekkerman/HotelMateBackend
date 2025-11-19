import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockItem
from decimal import Decimal

def populate_march_stocktake_counted():
    """
    Populate March stocktake with realistic counted values per category
    """
    
    # Get March stocktake
    march_stocktake = Stocktake.objects.filter(
        period_start='2025-03-01',
        period_end='2025-03-31'
    ).first()
    
    if not march_stocktake:
        print("March stocktake not found!")
        return
    
    print(f"\nPopulating March Stocktake (ID: {march_stocktake.id})")
    print(f"Period: {march_stocktake.period_start} to {march_stocktake.period_end}")
    print("="*80)
    
    # FIXED VALUES FOR EACH CATEGORY/SUBCATEGORY
    # Same numbers for all items in each group for easy tracking/testing
    
    COUNTED_VALUES = {
        'D': {'full': Decimal('3'), 'partial': Decimal('20.00')},  # 3 kegs + 20 pints
        'B': {'full': Decimal('2'), 'partial': Decimal('8')},      # 2 cases + 8 bottles
        'S': {'full': Decimal('5.50'), 'partial': Decimal('0')},   # 5.50 bottles
        'W': {'full': Decimal('7.25'), 'partial': Decimal('0')},   # 7.25 bottles
        'M_SOFT_DRINKS': {'full': Decimal('4'), 'partial': Decimal('6')},      # 4 cases + 6 bottles
        'M_SYRUPS': {'full': Decimal('3.50'), 'partial': Decimal('0')},        # 3.50 bottles
        'M_JUICES': {'full': Decimal('2'), 'partial': Decimal('5.75')},        # 2 cases + 5.75 bottles (5 bottles + 750ml)
        'M_CORDIALS': {'full': Decimal('1'), 'partial': Decimal('9')},         # 1 case + 9 bottles
        'M_BIB': {'full': Decimal('2.50'), 'partial': Decimal('0')},           # 2.50 boxes
        'M_BULK_JUICES': {'full': Decimal('45.50'), 'partial': Decimal('0')},  # 45.50 bottles
    }
    
    lines = march_stocktake.lines.all()
    updated_count = 0
    
    for line in lines:
        category = line.item.category.code
        subcategory = line.item.subcategory
        
        # Get the appropriate fixed values
        if category == 'M' and subcategory:
            key = f'M_{subcategory}'
            values = COUNTED_VALUES.get(key, {'full': Decimal('0'), 'partial': Decimal('0')})
        else:
            values = COUNTED_VALUES.get(category, {'full': Decimal('0'), 'partial': Decimal('0')})
        
        full = values['full']
        partial = values['partial']
        
        # Update the line
        line.counted_full_units = full
        line.counted_partial_units = partial
        line.save()
        updated_count += 1
        
        # Print progress every 50 items
        if updated_count % 50 == 0:
            print(f"Updated {updated_count} lines...")
    
    print(f"\n✓ Updated {updated_count} stocktake lines")
    print("="*80)
    
    # Show some examples
    print("\nSample counted values by category:")
    print("="*80)
    
    examples = {
        'D': 'Draught Beer',
        'B': 'Bottled Beer',
        'S': 'Spirits',
        'W': 'Wine',
    }
    
    for code, name in examples.items():
        line = lines.filter(item__category__code=code).first()
        if line:
            print(f"\n{name} - {line.item.name}")
            print(f"  UOM: {line.item.uom}")
            print(f"  Counted Full: {line.counted_full_units}")
            print(f"  Counted Partial: {line.counted_partial_units}")
            print(f"  Counted Qty: {line.counted_qty}")
    
    # Minerals subcategories
    mineral_examples = [
        ('SOFT_DRINKS', 'Soft Drinks'),
        ('SYRUPS', 'Syrups'),
        ('JUICES', 'Juices'),
        ('BIB', 'BIB'),
        ('BULK_JUICES', 'Bulk Juices'),
    ]
    
    for subcat, name in mineral_examples:
        line = lines.filter(
            item__category__code='M',
            item__subcategory=subcat
        ).first()
        if line:
            print(f"\n{name} - {line.item.name}")
            print(f"  UOM: {line.item.uom}")
            print(f"  Subcategory: {line.item.subcategory}")
            print(f"  Counted Full: {line.counted_full_units}")
            print(f"  Counted Partial: {line.counted_partial_units}")
            print(f"  Counted Qty: {line.counted_qty}")

if __name__ == '__main__':
    populate_march_stocktake_counted()
