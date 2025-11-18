"""
Fix BIB UOM from 72.0 to 1.0 (individual boxes)

ISSUE: BIB items have UOM = 72.0 which is incorrect for stocktake counting.
SOLUTION: UOM = 1.0 (count boxes), size_value = 18 (liters per box)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("FIX BIB UOM: 72.0 → 1.0 (INDIVIDUAL BOXES)")
print("="*80)

bib_items = StockItem.objects.filter(
    category_id='M',
    subcategory='BIB',
    active=True
)

print(f"\nFound {bib_items.count()} BIB items")
print()
print("BIB counting logic:")
print("  - User counts: 2 boxes + 0.5 fractional")
print("  - UOM = 1.0 means count in BOXES")
print("  - Calculation: (2 × 1) + (0.5 × 1) = 2.5 boxes ✓")
print("  - Box size (18L) stored in size_value, not UOM")
print("-"*80)

for item in bib_items:
    print(f"\n{item.sku} - {item.name}")
    print(f"  Current UOM: {item.uom}")
    print(f"  Size: {item.size} | Size Value: {item.size_value}L")
    print(f"  Unit Cost: €{item.unit_cost} per box")
    
    if item.uom != Decimal('1.00'):
        old_uom = item.uom
        item.uom = Decimal('1.00')
        item.save()
        print(f"  ✅ Updated UOM: {old_uom} → 1.00")
    else:
        print(f"  ✅ Already correct (UOM = 1.00)")

print("\n" + "="*80)
print("BIB UOM FIX COMPLETE")
print("All BIB items now use UOM = 1.0 (individual boxes)")
print("="*80 + "\n")
