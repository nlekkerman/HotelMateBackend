"""
Log all items without menu prices
Shows which items are missing selling prices
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 80)
print("ITEMS WITHOUT MENU PRICES")
print("=" * 80)
print()

# Get all items
all_items = StockItem.objects.all()

# Items without any selling price
no_menu_price = []
no_bottle_price = []
no_any_price = []

# Group by category
by_category = {
    'D': {'no_price': [], 'total': 0},
    'B': {'no_price': [], 'total': 0},
    'S': {'no_price': [], 'total': 0},
    'W': {'no_price': [], 'total': 0},
    'M': {'no_price': [], 'total': 0},
}

for item in all_items:
    category = item.category_id
    if category not in by_category:
        by_category[category] = {'no_price': [], 'total': 0}
    
    by_category[category]['total'] += 1
    
    # For wines, check bottle_price
    if category == 'W':
        if not item.bottle_price or item.bottle_price == 0:
            by_category[category]['no_price'].append(item)
            no_any_price.append(item)
    else:
        # For others, check menu_price
        if not item.menu_price or item.menu_price == 0:
            by_category[category]['no_price'].append(item)
            no_any_price.append(item)

# Print report
print("SUMMARY BY CATEGORY")
print("-" * 80)
for cat_code, data in sorted(by_category.items()):
    cat_name = {
        'D': 'Draught Beer',
        'B': 'Bottled Beer',
        'S': 'Spirits',
        'W': 'Wines',
        'M': 'Minerals/Mixers'
    }.get(cat_code, cat_code)
    
    missing = len(data['no_price'])
    total = data['total']
    percentage = (missing / total * 100) if total > 0 else 0
    
    print(f"{cat_name} ({cat_code}):")
    print(f"  Total items: {total}")
    print(f"  Missing prices: {missing} ({percentage:.1f}%)")
    print()

print("=" * 80)
print("DETAILED LIST - ITEMS WITHOUT PRICES")
print("=" * 80)

for cat_code in ['D', 'B', 'S', 'W', 'M']:
    items = by_category.get(cat_code, {}).get('no_price', [])
    if items:
        cat_name = {
            'D': 'DRAUGHT BEER',
            'B': 'BOTTLED BEER',
            'S': 'SPIRITS',
            'W': 'WINES',
            'M': 'MINERALS/MIXERS'
        }.get(cat_code, cat_code)
        
        print(f"\n{cat_name} ({cat_code}) - {len(items)} items:")
        print("-" * 80)
        for item in items:
            price_field = "bottle_price" if cat_code == 'W' else "menu_price"
            print(f"  {item.sku} - {item.name}")
            print(f"    Missing: {price_field}")
            if item.unit_cost:
                print(f"    Unit cost: €{item.unit_cost}")
            print()

print("=" * 80)
print("TOTAL SUMMARY")
print("=" * 80)
print(f"Total items in database: {all_items.count()}")
print(f"Items without selling price: {len(no_any_price)}")
print(f"Items with selling price: {all_items.count() - len(no_any_price)}")
print()

# Check saleable items without prices
saleable_no_price = [
    item for item in no_any_price if item.available_on_menu
]

if saleable_no_price:
    print("⚠️ SALEABLE ITEMS WITHOUT PRICES:")
    print(f"   {len(saleable_no_price)} items marked as available_on_menu")
    print("   but have no selling price!")
    print()
    for item in saleable_no_price[:10]:
        print(f"   - {item.sku} - {item.name}")
    if len(saleable_no_price) > 10:
        print(f"   ... and {len(saleable_no_price) - 10} more")
    print()

print("=" * 80)
