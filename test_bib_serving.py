"""
Test BIB serving_size and GP calculations
Check if BIB items can calculate GP and serving values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB SERVING_SIZE & GP TEST")
print("="*80)

bib_items = StockItem.objects.filter(
    hotel_id=2,
    category_id='M',
    subcategory='BIB'
)

for item in bib_items:
    print(f"\n{'-'*80}")
    print(f"{item.sku} - {item.name}")
    print(f"{'-'*80}")
    
    print(f"\nCurrent Values:")
    print(f"  unit_cost: €{item.unit_cost}")
    print(f"  uom: {item.uom}")
    print(f"  menu_price: {item.menu_price}")
    print(f"  size: {item.size}")
    
    print(f"\nCurrent Stock:")
    print(f"  Full: {item.current_full_units}")
    print(f"  Partial: {item.current_partial_units}")
    print(f"  Total: {item.current_full_units + item.current_partial_units} boxes")
    
    print(f"\nCalculated Values:")
    print(f"  cost_per_serving: €{item.cost_per_serving}")
    print(f"  total_stock_in_servings: {item.total_stock_in_servings}")
    print(f"  total_stock_value: €{item.total_stock_value}")
    
    if item.menu_price:
        print(f"\nGP Calculations:")
        print(f"  menu_price: €{item.menu_price}")
        print(f"  cost_per_serving: €{item.cost_per_serving}")
        gp_per = item.gross_profit_per_serving
        gp_pct = item.gross_profit_percentage
        if gp_per:
            print(f"  gross_profit_per_serving: €{gp_per}")
        if gp_pct:
            print(f"  gross_profit_percentage: {gp_pct}%")
    else:
        print(f"\n⚠️ No menu_price set - cannot calculate GP")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("="*80)
print("If BIB items are sold on dash (200ml servings):")
print("  1. Set serving_size = 200ml for each BIB item")
print("  2. Set menu_price for each item")
print("  3. System will calculate GP automatically")
print("\nStocktake valuation stays the same (boxes × unit_cost)")
print("GP calculations are separate for sales analysis")
print("="*80 + "\n")
