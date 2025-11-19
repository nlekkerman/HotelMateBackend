import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

def update_bulk_juices_uom():
    """Update UOM to 1 for all bulk juices"""
    
    # Update bulk juices (Minerals category with BULK_JUICES subcategory)
    bulk_juices = StockItem.objects.filter(subcategory='BULK_JUICES')
    
    print(f"\nFound {bulk_juices.count()} bulk juices to update")
    print("=" * 80)
    
    count = 0
    for juice in bulk_juices:
        old_uom = juice.uom
        juice.uom = Decimal('1.00')
        juice.save()
        count += 1
        print(f"Updated: {juice.name:45s} | {old_uom} -> 1.00")
    
    print(f"\n✓ Updated {count} bulk juices")
    print("=" * 80)

if __name__ == '__main__':
    update_bulk_juices_uom()
