import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem


# Draught Beer UOM mapping (pints per keg size)
DRAUGHT_UOM_MAP = {
    '20Lt': Decimal('35.21'),
    '30Lt': Decimal('52.82'),
    '50Lt': Decimal('88.03'),
}


def set_draught_measurements():
    """Set size and UOM for all Draught Beer items"""
    
    draught_items = StockItem.objects.filter(category__code='D')
    
    print(f"\n{'='*80}")
    print(f"SETTING MEASUREMENTS FOR DRAUGHT BEER (Category D)")
    print(f"Total items: {draught_items.count()}")
    print(f"{'='*80}\n")
    
    updated_count = 0
    
    for item in draught_items:
        # Extract size from SKU or name
        # Examples: "20 Heineken 00%", "30 Beamish", "50 Guinness"
        size_lt = None
        
        # Try to find size in name
        if '20' in item.name or '20Lt' in item.size:
            size_lt = '20Lt'
        elif '30' in item.name or '30Lt' in item.size:
            size_lt = '30Lt'
        elif '50' in item.name or '50Lt' in item.size:
            size_lt = '50Lt'
        
        if size_lt:
            item.size = size_lt
            item.size_value = Decimal(size_lt.replace('Lt', ''))
            item.size_unit = 'Lt'
            item.uom = DRAUGHT_UOM_MAP[size_lt]
            item.save()
            
            print(f"✓ {item.sku} - {item.name}")
            print(f"  Size: {item.size} | UoM: {item.uom} pints/keg")
            updated_count += 1
        else:
            print(f"⚠ {item.sku} - {item.name} - Could not determine size")
    
    print(f"\n{'='*80}")
    print(f"COMPLETED: Updated {updated_count} draught beer items")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    set_draught_measurements()
