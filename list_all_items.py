"""
List all items in the database grouped by category
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Get all items ordered by category and SKU
all_items = StockItem.objects.all().order_by('category', 'sku')

current_category = None
category_counts = {}

print("=" * 80)
print("ALL STOCK ITEMS IN DATABASE")
print("=" * 80)

for item in all_items:
    # Print category header when it changes
    if item.category != current_category:
        if current_category:
            print(f"\n{'─' * 80}")
        current_category = item.category
        print(f"\n{'═' * 80}")
        print(f"CATEGORY: {current_category or 'UNCATEGORIZED'}")
        print(f"{'═' * 80}")
        category_counts[current_category] = 0
    
    # Print item details
    category_counts[current_category] += 1
    uom = f"{item.uom}" if item.uom else 'N/A'
    print(f"{item.sku:15} | {item.name:50} | UOM: {uom}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY BY CATEGORY")
print("=" * 80)
for category, count in sorted(category_counts.items()):
    print(f"{category or 'UNCATEGORIZED':30} : {count:4} items")

print(f"\n{'TOTAL':30} : {sum(category_counts.values()):4} items")
print("=" * 80)
