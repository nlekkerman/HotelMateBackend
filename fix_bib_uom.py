"""
Fix BIB UOM from 72 to 18 (liters per box)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("FIX BIB UOM: 72 → 18")
print("="*80)

bib_items = StockItem.objects.filter(
    hotel_id=2,
    category_id='M',
    subcategory='BIB'
)

print(f"\nFound {bib_items.count()} BIB items")
print("-"*80)

for item in bib_items:
    print(f"\n{item.sku} - {item.name}")
    print(f"  Current UOM: {item.uom}")
    
    if item.uom != Decimal('18'):
        item.uom = Decimal('18')
        item.save()
        print(f"  ✅ Updated to 18")
    else:
        print(f"  ✅ Already correct")

print("\n" + "="*80)
print("BIB UOM FIX COMPLETE")
print("="*80 + "\n")
