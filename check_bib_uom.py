"""
Check BIB UOM values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 120)
print("CHECKING BIB UOM VALUES")
print("=" * 120)
print()

# Get all BIB items
bib_items = StockItem.objects.filter(
    category_id='M',
    subcategory='BIB',
    active=True
).order_by('sku')

print(f"Total BIB Items: {bib_items.count()}")
print()

if bib_items.count() == 0:
    print("No BIB items found!")
else:
    print("CURRENT BIB ITEMS:")
    print("-" * 120)
    print(f"{'SKU':<15} {'Name':<50} {'Size':<15} {'UOM':<10} {'Unit Cost':<12}")
    print("-" * 120)
    
    uom_groups = {}
    for item in bib_items:
        print(f"{item.sku:<15} {item.name[:50]:<50} {item.size:<15} {item.uom:<10} €{item.unit_cost:<11.4f}")
        
        uom_key = float(item.uom)
        if uom_key not in uom_groups:
            uom_groups[uom_key] = []
        uom_groups[uom_key].append(item)
    
    print()
    print("=" * 120)
    print("UOM DISTRIBUTION:")
    print("=" * 120)
    for uom, items in sorted(uom_groups.items()):
        print(f"\nUOM = {uom}: {len(items)} items")
        if uom == 1.0:
            print("  ✅ CORRECT: 1 box = 1 storage unit")
        elif uom == 18.0:
            print("  ❌ WRONG: Should be 1.0 (this is liters per box, not UOM)")
        else:
            print(f"  ❌ WRONG: Should be 1.0 (not {uom})")
    
    print()
    print("=" * 120)
    print("BIB LOGIC:")
    print("=" * 120)
    print("""
BIB (Bag-in-Box) Counting:
--------------------------
Storage: BOXES + FRACTIONAL (e.g., 2.5 boxes)
UOM: Should be 1.0 (individual boxes)

Example:
  User counts: 2 boxes + 0.5 fractional
  Calculation: (2 × 1.0) + (0.5 × 1.0) = 2.5 boxes ✓
  
The box size (18L) is stored in size_value, NOT in UOM!
UOM only defines the counting unit (boxes), not the conversion to drinks.
""")

print()
