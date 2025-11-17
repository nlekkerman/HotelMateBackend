import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine
from decimal import Decimal


def restore_stock_items_from_october():
    """Restore StockItem measurements from October 2025 stocktake (ID 18)"""
    
    try:
        october_stocktake = Stocktake.objects.get(id=18)
    except Stocktake.DoesNotExist:
        print("ERROR: October stocktake (ID 18) not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"RESTORING STOCK ITEMS FROM OCTOBER STOCKTAKE")
    print(f"Stocktake ID: {october_stocktake.id}")
    print(f"Period: {october_stocktake.period_start} to {october_stocktake.period_end}")
    print(f"{'='*80}\n")
    
    lines = october_stocktake.lines.all().select_related('item', 'item__category')
    
    print(f"Total stocktake lines: {lines.count()}\n")
    
    restored_count = 0
    skipped_count = 0
    
    for line in lines:
        item = line.item
        
        # Calculate UOM from valuation_cost
        # valuation_cost = unit_cost / uom
        # So: uom = unit_cost / valuation_cost
        
        if line.valuation_cost and line.valuation_cost > 0:
            # We need to reverse engineer from the stocktake line
            # For now, we'll use item's current values if they exist in item data
            
            # Check if item has size info in SKU or can be inferred
            category = item.category.code
            
            # Set based on category patterns
            if category == 'D':  # Draught
                if '20' in item.name:
                    item.size = '20Lt'
                    item.size_value = Decimal('20')
                    item.size_unit = 'Lt'
                    item.uom = Decimal('35.21')
                elif '30' in item.name:
                    item.size = '30Lt'
                    item.size_value = Decimal('30')
                    item.size_unit = 'Lt'
                    item.uom = Decimal('52.82')
                elif '50' in item.name:
                    item.size = '50Lt'
                    item.size_value = Decimal('50')
                    item.size_unit = 'Lt'
                    item.uom = Decimal('88.03')
                
                # Calculate unit_cost from valuation_cost
                if item.uom > 0:
                    item.unit_cost = line.valuation_cost * item.uom
                    
            elif category == 'B':  # Bottled Beer
                item.size = 'Doz'
                item.size_value = Decimal('12')
                item.size_unit = 'Doz'
                item.uom = Decimal('12')
                item.unit_cost = line.valuation_cost * Decimal('12')
                
            elif category == 'S':  # Spirits
                # Check size from name/SKU
                if '1ltr' in item.name.lower() or '1 lt' in item.name.lower():
                    item.size = '1 Lt'
                    item.size_value = Decimal('1000')
                    item.size_unit = 'ml'
                    item.uom = Decimal('28.60')
                elif '70cl' in item.name.lower() or '70' in item.sku:
                    item.size = '70cl'
                    item.size_value = Decimal('700')
                    item.size_unit = 'ml'
                    item.uom = Decimal('20.00')
                elif '75cl' in item.name.lower():
                    item.size = '75cl'
                    item.size_value = Decimal('750')
                    item.size_unit = 'ml'
                    item.uom = Decimal('21.40')
                elif '50cl' in item.name.lower():
                    item.size = '50cl'
                    item.size_value = Decimal('500')
                    item.size_unit = 'ml'
                    item.uom = Decimal('14.30')
                else:
                    # Default to 70cl
                    item.size = '70cl'
                    item.size_value = Decimal('700')
                    item.size_unit = 'ml'
                    item.uom = Decimal('20.00')
                
                item.unit_cost = line.valuation_cost * item.uom
                
            elif category == 'W':  # Wine
                item.size = '75cl'
                item.size_value = Decimal('750')
                item.size_unit = 'ml'
                item.uom = Decimal('1.00')  # 1 glass per bottle for now
                item.unit_cost = line.valuation_cost
                
            elif category == 'M':  # Minerals
                # Keep subcategory, set basic measurements
                if item.subcategory == 'SOFT_DRINKS':
                    item.size = 'Doz'
                    item.size_value = Decimal('12')
                    item.size_unit = 'Doz'
                    item.uom = Decimal('12')
                    item.unit_cost = line.valuation_cost * Decimal('12')
                elif item.subcategory == 'SYRUPS':
                    item.size = 'Ind'
                    item.size_value = Decimal('700')
                    item.size_unit = 'ml'
                    item.uom = Decimal('700')
                    item.unit_cost = line.valuation_cost * Decimal('700')
                elif item.subcategory == 'JUICES':
                    item.size = 'Doz'
                    item.size_value = Decimal('12')
                    item.size_unit = 'Doz'
                    item.uom = Decimal('12')
                    item.unit_cost = line.valuation_cost * Decimal('12')
                elif item.subcategory == 'BIB':
                    item.size = '18LT'
                    item.size_value = Decimal('18')
                    item.size_unit = 'Lt'
                    item.uom = Decimal('18')
                    item.unit_cost = line.valuation_cost * Decimal('18')
                elif item.subcategory == 'BULK_JUICES':
                    item.size = 'Ind'
                    item.size_value = Decimal('1')
                    item.size_unit = 'Ind'
                    item.uom = Decimal('1')
                    item.unit_cost = line.valuation_cost
                elif item.subcategory == 'CORDIALS':
                    item.size = 'Doz'
                    item.size_value = Decimal('12')
                    item.size_unit = 'Doz'
                    item.uom = Decimal('12')
                    item.unit_cost = line.valuation_cost * Decimal('12')
            
            item.save()
            restored_count += 1
            
            if restored_count % 20 == 0:
                print(f"Restored {restored_count} items...")
        else:
            skipped_count += 1
            print(f"⚠ Skipped {item.sku} - {item.name} (no valuation_cost)")
    
    print(f"\n{'='*80}")
    print(f"COMPLETED")
    print(f"Restored: {restored_count} items")
    print(f"Skipped: {skipped_count} items")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    restore_stock_items_from_october()
