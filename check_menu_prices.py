"""
Check menu_price values for stock items
Run with: Get-Content check_menu_prices.py | python manage.py shell
"""
from stock_tracker.models import StockItem
from decimal import Decimal

items = StockItem.objects.filter(active=True).select_related('category').order_by('category__code', 'sku')

has_price = []
no_price = []
zero_price = []

for item in items:
    if item.menu_price and item.menu_price > Decimal('0'):
        has_price.append(item)
    elif item.menu_price == Decimal('0'):
        zero_price.append(item)
    else:
        no_price.append(item)

print(f"\n{'='*80}")
print(f"MENU PRICE STATUS")
print(f"{'='*80}\n")

print(f"Has menu price (> 0):  {len(has_price)} items")
print(f"Zero menu price:       {len(zero_price)} items")
print(f"NULL/missing price:    {len(no_price)} items")
print(f"Total items:           {items.count()}")

if no_price or zero_price:
    print(f"\n{'='*80}")
    print(f"ITEMS WITHOUT VALID MENU PRICE ({len(no_price) + len(zero_price)} items)")
    print(f"{'='*80}\n")
    
    items_without_price = no_price + zero_price
    by_category = {}
    for item in items_without_price:
        cat = item.category.code
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat_code in sorted(by_category.keys()):
        items_list = by_category[cat_code]
        cat_name = items_list[0].category.name
        print(f"\n{cat_code} - {cat_name} ({len(items_list)} items)")
        print("-" * 80)
        for item in items_list[:15]:
            price_str = str(item.menu_price) if item.menu_price else "NULL"
            print(f"  {item.sku:<15} {item.name:<45} €{price_str}")
        if len(items_list) > 15:
            print(f"  ... and {len(items_list) - 15} more")

if has_price:
    print(f"\n{'='*80}")
    print(f"SAMPLE ITEMS WITH MENU PRICES")
    print(f"{'='*80}\n")
    
    by_category = {}
    for item in has_price[:30]:
        cat = item.category.code
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat_code in sorted(by_category.keys()):
        items_list = by_category[cat_code]
        cat_name = items_list[0].category.name
        print(f"\n{cat_code} - {cat_name}")
        print("-" * 80)
        for item in items_list[:5]:
            print(f"  {item.sku:<15} {item.name:<45} €{item.menu_price}")

print(f"\n{'='*80}\n")
