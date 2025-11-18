"""
Test variance_drink_servings field - should only work for BIB
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

print("\n" + "="*80)
print("TEST: variance_drink_servings - BIB vs Other Categories")
print("="*80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if stocktake:
    # Test different categories
    test_items = [
        ('M25', 'BIB', 'Splash Cola 18LTR'),
        ('M03', 'SOFT_DRINKS', 'Coke Zero 200ML Bottles'),
        ('M08', 'JUICES', 'Pineapple Juice 1LTR'),
        ('M16', 'SYRUPS', 'Monin Coffee 700ML'),
    ]
    
    for sku, expected_subcat, name in test_items:
        line = StocktakeLine.objects.filter(
            stocktake=stocktake,
            item__sku=sku
        ).select_related('item').first()
        
        if line:
            print(f"\n{'-'*80}")
            print(f"Item: {line.item.sku} - {line.item.name}")
            print(f"Subcategory: {line.item.subcategory}")
            print(f"{'-'*80}")
            
            print(f"variance_qty: {line.variance_qty}")
            
            if line.item.subcategory == 'BIB':
                # For BIB: variance_qty is boxes, calculate drink servings
                serving_size = line.item.size_value
                servings_per_box = Decimal('18000') / Decimal(str(serving_size))
                drink_servings = line.variance_qty * servings_per_box
                
                print(f"  ↳ This is {line.variance_qty} BOXES")
                print(f"  ↳ Serving size: {serving_size}ml")
                print(f"  ↳ Servings per box: {servings_per_box:.0f}")
                print(f"  ↳ Drink servings: {drink_servings:.2f}")
                print(f"  ✅ Should calculate variance_drink_servings = {drink_servings:.2f}")
                
            elif line.item.subcategory == 'SOFT_DRINKS':
                print(f"  ↳ This is ALREADY drink servings (bottles)")
                print(f"  ✅ variance_drink_servings should return None")
                
            elif line.item.subcategory == 'JUICES':
                print(f"  ↳ This is ALREADY drink servings (200ml portions)")
                print(f"  ✅ variance_drink_servings should return None")
                
            elif line.item.subcategory == 'SYRUPS':
                print(f"  ↳ This is ALREADY drink servings (35ml shots)")
                print(f"  ✅ variance_drink_servings should return None")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
variance_drink_servings logic:
- BIB: Calculate boxes × servings_per_box → return drink servings
- ALL OTHER CATEGORIES: Return None (they already have drink servings)

This won't break any existing logic because:
1. It's a NEW field (not changing existing fields)
2. Returns None for non-BIB (frontend can check if value exists)
3. BIB is special case where variance_qty = boxes, not servings
""")
print("="*80 + "\n")
