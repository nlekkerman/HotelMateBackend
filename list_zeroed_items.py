"""
List all zeroed stock items
Run with: python manage.py shell < list_zeroed_items.py
"""
from stock_tracker.models import StockItem
from decimal import Decimal

zeroed = StockItem.objects.filter(
    current_full_units=Decimal('0'),
    current_partial_units=Decimal('0'),
    active=True
).select_related('category').order_by('category__code', 'sku')

print(f"\n{'='*80}")
print(f"ZEROED STOCK ITEMS")
print(f"{'='*80}\n")

if zeroed.count() == 0:
    print("✓ No zeroed items found - all items have stock values!\n")
else:
    print(f"Found {zeroed.count()} items with zero stock:\n")
    
    by_category = {}
    for item in zeroed:
        cat = item.category.code
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)
    
    for cat_code in sorted(by_category.keys()):
        items = by_category[cat_code]
        cat_name = items[0].category.name
        print(f"\n{cat_code} - {cat_name} ({len(items)} items)")
        print("-" * 80)
        for item in items:
            print(f"  {item.sku:<10} {item.name}")
    
    print(f"\n{'='*80}")
    print(f"Total: {zeroed.count()} items need restoration")
    print(f"{'='*80}\n")
