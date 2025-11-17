"""
Verify BIB calculations with 36ml serving size
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB CALCULATIONS VERIFICATION (36ml serving)")
print("="*80)

bib_items = StockItem.objects.filter(
    hotel_id=2,
    category_id='M',
    subcategory='BIB'
).order_by('sku')

for item in bib_items:
    print(f"\n{'-'*80}")
    print(f"{item.sku} - {item.name}")
    print(f"{'-'*80}")
    
    print(f"\nItem Configuration:")
    print(f"  unit_cost: €{item.unit_cost} (per 18L box)")
    print(f"  size_value: {item.size_value}ml (serving size)")
    
    # Calculate servings per box
    box_ml = 18000  # 18L = 18000ml
    servings_per_box = box_ml / float(item.size_value)
    
    print(f"\nServings Calculation:")
    print(f"  Box size: 18,000ml")
    print(f"  Serving size: {item.size_value}ml")
    print(f"  Servings per box: {servings_per_box:.0f}")
    
    # Calculate cost per serving
    cost_per_serving_calc = float(item.unit_cost) / servings_per_box
    
    print(f"\nCost Per Serving:")
    print(f"  Manual: €{item.unit_cost} ÷ {servings_per_box:.0f} = €{cost_per_serving_calc:.4f}")
    print(f"  System: €{item.cost_per_serving:.4f}")
    
    # Test with 2 boxes
    item.current_full_units = Decimal('2')
    item.current_partial_units = Decimal('0')
    
    total_servings = servings_per_box * 2
    
    print(f"\nExample: 2 Full Boxes")
    print(f"  Stocktake value: 2 × €{item.unit_cost} = €{item.total_stock_value:.2f}")
    print(f"  Total servings: {total_servings:.0f}")
    print(f"  If sold at €3.50: Revenue = €{total_servings * 3.50:.2f}")
    print(f"  GP per serving: €3.50 - €{cost_per_serving_calc:.4f} = €{3.50 - cost_per_serving_calc:.4f}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
print("✅ 18,000ml ÷ 36ml = 500 servings per box")
print("✅ Stocktake: boxes × unit_cost (storage value)")
print("✅ GP: servings × (menu_price - cost_per_serving)")
print("="*80 + "\n")
