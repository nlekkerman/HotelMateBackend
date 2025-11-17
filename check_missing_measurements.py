"""
Check for stock items missing size, size_unit, and uom
Run with: python manage.py shell < check_missing_measurements.py
"""
from stock_tracker.models import StockItem
from decimal import Decimal

items = StockItem.objects.filter(active=True).select_related('category').order_by('category__code', 'sku')

missing_size = []
missing_size_unit = []
missing_uom = []
missing_all = []

for item in items:
    has_issues = False
    issues = []
    
    if not item.size or item.size == '':
        missing_size.append(item)
        issues.append('size')
        has_issues = True
    
    if not item.size_unit or item.size_unit == '':
        missing_size_unit.append(item)
        issues.append('size_unit')
        has_issues = True
    
    if not item.uom or item.uom == Decimal('0'):
        missing_uom.append(item)
        issues.append('uom')
        has_issues = True
    
    if len(issues) == 3:
        missing_all.append(item)

print(f"\n{'='*80}")
print(f"STOCK ITEMS MISSING MEASUREMENTS")
print(f"{'='*80}\n")

print(f"Missing size:      {len(missing_size)} items")
print(f"Missing size_unit: {len(missing_size_unit)} items")
print(f"Missing uom:       {len(missing_uom)} items")
print(f"Missing ALL THREE: {len(missing_all)} items")

if missing_all:
    print(f"\n{'='*80}")
    print(f"ITEMS MISSING ALL THREE FIELDS ({len(missing_all)} items)")
    print(f"{'='*80}\n")
    
    by_category = {}
    for item in missing_all:
        cat = item.category.code
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat_code in sorted(by_category.keys()):
        items_list = by_category[cat_code]
        cat_name = items_list[0].category.name
        print(f"\n{cat_code} - {cat_name} ({len(items_list)} items)")
        print("-" * 80)
        for item in items_list:
            stock_info = f"{item.current_full_units} full, {item.current_partial_units} partial"
            print(f"  {item.sku:<15} {item.name:<50} {stock_info}")

print(f"\n{'='*80}\n")
