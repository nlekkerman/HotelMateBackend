"""
Fix missing size, size_unit, and uom for all stock items
Run with: python manage.py shell < fix_missing_measurements.py
"""
from stock_tracker.models import StockItem
from decimal import Decimal

items = StockItem.objects.filter(active=True).select_related('category')

print(f"\n{'='*80}")
print(f"FIXING MISSING MEASUREMENTS")
print(f"{'='*80}\n")

fixed_count = 0
skipped_count = 0

for item in items:
    needs_fix = (
        not item.size or 
        not item.size_unit or 
        not item.uom or 
        item.uom == Decimal('0')
    )
    
    if not needs_fix:
        skipped_count += 1
        continue
    
    category = item.category.code
    
    # Set based on category
    if category == 'D':  # Draught
        # Check keg size from name
        if '20' in item.name or '20Lt' in item.name.upper():
            item.size = '20Lt'
            item.size_value = Decimal('20')
            item.size_unit = 'Lt'
            item.uom = Decimal('35.21')  # pints per 20L keg
        elif '30' in item.name or '30Lt' in item.name.upper():
            item.size = '30Lt'
            item.size_value = Decimal('30')
            item.size_unit = 'Lt'
            item.uom = Decimal('52.82')  # pints per 30L keg
        elif '50' in item.name or '50Lt' in item.name.upper():
            item.size = '50Lt'
            item.size_value = Decimal('50')
            item.size_unit = 'Lt'
            item.uom = Decimal('88.03')  # pints per 50L keg
        else:
            # Default to 30L
            item.size = '30Lt'
            item.size_value = Decimal('30')
            item.size_unit = 'Lt'
            item.uom = Decimal('52.82')
    
    elif category == 'B':  # Bottled Beer
        item.size = 'Doz'
        item.size_value = Decimal('12')
        item.size_unit = 'Doz'
        item.uom = Decimal('12')  # bottles per case
    
    elif category == 'S':  # Spirits
        # Check bottle size from name
        if '1LTR' in item.name.upper() or '1 LT' in item.name.upper():
            item.size = '1Lt'
            item.size_value = Decimal('1000')
            item.size_unit = 'ml'
            item.uom = Decimal('28.60')  # 35ml shots
        elif '75CL' in item.name.upper() or '750ML' in item.name.upper():
            item.size = '75cl'
            item.size_value = Decimal('750')
            item.size_unit = 'ml'
            item.uom = Decimal('21.40')  # 35ml shots
        elif '50CL' in item.name.upper() or '500ML' in item.name.upper():
            item.size = '50cl'
            item.size_value = Decimal('500')
            item.size_unit = 'ml'
            item.uom = Decimal('14.30')  # 35ml shots
        else:
            # Default to 70cl (standard spirit bottle)
            item.size = '70cl'
            item.size_value = Decimal('700')
            item.size_unit = 'ml'
            item.uom = Decimal('20.00')  # 35ml shots
    
    elif category == 'W':  # Wine
        # Check bottle size
        if '187' in item.name or '18.7' in item.name:
            item.size = '187ml'
            item.size_value = Decimal('187')
            item.size_unit = 'ml'
            item.uom = Decimal('1.25')  # glasses per small bottle
        else:
            # Standard wine bottle
            item.size = '75cl'
            item.size_value = Decimal('750')
            item.size_unit = 'ml'
            item.uom = Decimal('5.00')  # 150ml glasses per bottle
    
    elif category == 'M':  # Minerals/Soft Drinks
        # Check subcategory
        if item.subcategory == 'SOFT_DRINKS':
            item.size = 'Doz'
            item.size_value = Decimal('12')
            item.size_unit = 'Doz'
            item.uom = Decimal('12')
        elif item.subcategory == 'SYRUPS':
            item.size = 'Ind'
            item.size_value = Decimal('700')
            item.size_unit = 'ml'
            item.uom = Decimal('700')  # servings per bottle
        elif item.subcategory == 'JUICES':
            item.size = 'Doz'
            item.size_value = Decimal('12')
            item.size_unit = 'Doz'
            item.uom = Decimal('12')
        elif item.subcategory == 'BIB':
            item.size = '18Lt'
            item.size_value = Decimal('18')
            item.size_unit = 'Lt'
            item.uom = Decimal('72')  # 250ml servings
        elif item.subcategory == 'BULK_JUICES':
            item.size = 'Ind'
            item.size_value = Decimal('1')
            item.size_unit = 'Ind'
            item.uom = Decimal('60')  # servings per carton
        elif item.subcategory == 'CORDIALS':
            item.size = 'Doz'
            item.size_value = Decimal('12')
            item.size_unit = 'Doz'
            item.uom = Decimal('12')
        else:
            # Default for uncategorized minerals
            item.size = 'Doz'
            item.size_value = Decimal('12')
            item.size_unit = 'Doz'
            item.uom = Decimal('12')
    
    item.save()
    fixed_count += 1
    
    if fixed_count % 20 == 0:
        print(f"Fixed {fixed_count} items...")

print(f"\n{'='*80}")
print(f"COMPLETE")
print(f"{'='*80}")
print(f"✓ Fixed: {fixed_count} items")
print(f"⚬ Skipped (already has values): {skipped_count} items")
print(f"{'='*80}\n")
