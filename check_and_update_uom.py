import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

def check_categories_and_update():
    """Check categories and update UOM"""
    
    # Get sample items from each category
    all_items = StockItem.objects.all()
    categories = set()
    
    for item in all_items:
        categories.add(str(item.category))
    
    print("Categories found:")
    for cat in sorted(categories):
        print(f"  - {cat}")
    
    print("\n" + "=" * 80)
    
    # Update all syrups (Minerals category with SYRUPS subcategory)
    syrups = StockItem.objects.filter(subcategory='SYRUPS')
    
    print(f"\nFound {syrups.count()} syrups to update")
    print("=" * 80)
    
    syrup_count = 0
    for syrup in syrups:
        old_uom = syrup.uom
        syrup.uom = Decimal('1.00')
        syrup.save()
        syrup_count += 1
        print(f"Updated: {syrup.name:45s} | {old_uom} -> 1.00")
    
    print(f"\n✓ Updated {syrup_count} syrups")
    
    # Update all spirits - filter by category containing "Spirits"
    spirits = StockItem.objects.filter(category__name__icontains='Spirit')
    
    print(f"\nFound {spirits.count()} spirits to update")
    print("=" * 80)
    
    spirit_count = 0
    for spirit in spirits:
        old_uom = spirit.uom
        spirit.uom = Decimal('1.00')
        spirit.save()
        spirit_count += 1
        print(f"Updated: {spirit.name:45s} | {old_uom} -> 1.00")
    
    print(f"\n✓ Updated {spirit_count} spirits")
    print("\n" + "=" * 80)
    print(f"TOTAL: Updated {syrup_count + spirit_count} items")
    print("=" * 80)

if __name__ == '__main__':
    check_categories_and_update()
