"""
Set BIB serving size to 35ml for GP calculations
Note: This does NOT affect stocktake valuation (still boxes × unit_cost)
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("SET BIB SERVING SIZE TO 36ML")
print("="*80)

bib_items = StockItem.objects.filter(
    hotel_id=2,
    category_id='M',
    subcategory='BIB'
)

print(f"\nFound {bib_items.count()} BIB items")
print("\nUpdating size_value to 36ml (500 servings per 18L box)...")
print("-"*80)

for item in bib_items:
    print(f"\n{item.sku} - {item.name}")
    print(f"  Current size_value: {item.size_value}")
    print(f"  Current size_unit: {item.size_unit}")
    
    # Set serving size to 36ml (18L = 18000ml ÷ 36ml = 500 servings)
    item.size_value = Decimal('36')
    item.size_unit = 'ml'
    item.save()
    
    print(f"  ✅ Updated to: 36ml (500 servings per box)")
    
    # Recalculate cost_per_serving
    print(f"\n  unit_cost: €{item.unit_cost} (per 18L box)")
    print(f"  cost_per_serving: €{item.cost_per_serving} (per 35ml)")

print("\n" + "="*80)
print("IMPORTANT:")
print("="*80)
print("✅ Serving size set to 36ml (500 servings per 18L box)")
print("✅ Stocktake valuation still uses: boxes × unit_cost")
print("✅ These are separate calculations!")
print("\nStocktake = storage value (boxes)")
print("GP = sales profitability (36ml servings)")
print("\nMath: 18,000ml ÷ 36ml = 500 servings per box")
print("="*80 + "\n")
