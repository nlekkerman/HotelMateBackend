import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

def update_syrups_spirits_uom():
    """Update UOM to 1 for all syrups and spirits"""
    
    # Update all syrups (Minerals category with SYRUPS subcategory)
    syrups = StockItem.objects.filter(
        category__name='M - Minerals & Syrups',
        subcategory='SYRUPS'
    )
    
    print(f"\nFound {syrups.count()} syrups to update")
    print("=" * 80)
    
    syrup_count = 0
    for syrup in syrups:
        old_uom = syrup.uom
        syrup.uom = Decimal('1.00')
        syrup.save()
        syrup_count += 1
        print(f"Updated: {syrup.name:50s} | Old UOM: {old_uom} -> New UOM: 1.00")
    
    print(f"\n✓ Updated {syrup_count} syrups")
    
    # Update all spirits (S - Spirits category)
    spirits = StockItem.objects.filter(category__name='S - Spirits')
    
    print(f"\nFound {spirits.count()} spirits to update")
    print("=" * 80)
    
    spirit_count = 0
    for spirit in spirits:
        old_uom = spirit.uom
        spirit.uom = Decimal('1.00')
        spirit.save()
        spirit_count += 1
        print(f"Updated: {spirit.name:50s} | Old UOM: {old_uom} -> New UOM: 1.00")
    
    print(f"\n✓ Updated {spirit_count} spirits")
    print("\n" + "=" * 80)
    print(f"TOTAL: Updated {syrup_count + spirit_count} items")
    print("=" * 80)

if __name__ == '__main__':
    update_syrups_spirits_uom()
