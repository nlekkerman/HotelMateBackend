"""
Check BIB stocktake valuation logic.
Purpose: BIB items should use (full_units + partial_units) × unit_cost
NOT serving-based calculations.
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine

print("\n" + "="*80)
print("BIB (BAG-IN-BOX) STOCKTAKE VALUATION CHECK")
print("="*80)

# Get BIB items
bib_items = StockItem.objects.filter(
    hotel_id=2,
    category_id='M',
    subcategory='BIB',
    active=True
)

print(f"\nFound {bib_items.count()} BIB items:")
print("-"*80)

for item in bib_items:
    print(f"\n{item.sku} - {item.name}")
    print(f"  Unit Cost (18L box): €{item.unit_cost:.2f}")
    print(f"  UOM: {item.uom} (should be 18L)")
    print(f"  Cost per serving: €{item.cost_per_serving:.4f}")
    print(f"  Current stock: {item.current_full_units} boxes + {item.current_partial_units} partial")

# Get February stocktake lines
print("\n" + "="*80)
print("FEBRUARY STOCKTAKE - BIB ITEMS")
print("="*80)

stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if not stocktake:
    print("❌ February stocktake not found!")
else:
    print(f"\nStocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    
    lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__subcategory='BIB'
    ).select_related('item')
    
    print(f"\nFound {lines.count()} BIB stocktake lines:")
    print("-"*80)
    
    for line in lines:
        print(f"\n{line.item.sku} - {line.item.name}")
        print(f"  Counted: {line.counted_full_units} boxes + {line.counted_partial_units} partial")
        print(f"  Valuation cost: €{line.valuation_cost:.4f} (per serving)")
        print(f"  Counted qty: {line.counted_qty:.2f} servings")
        print(f"  Counted value: €{line.counted_value:.2f}")
        
        print(f"\n  ⚠️ CURRENT CALCULATION (SERVING-BASED):")
        print(f"     counted_qty = {line.counted_qty:.2f} servings")
        print(f"     counted_value = {line.counted_qty:.2f} × €{line.valuation_cost:.4f} = €{line.counted_value:.2f}")
        
        print(f"\n  ✅ CORRECT CALCULATION (UNIT-BASED):")
        total_units = line.counted_full_units + line.counted_partial_units
        correct_value = total_units * line.item.unit_cost
        print(f"     total_units = {line.counted_full_units} + {line.counted_partial_units} = {total_units}")
        print(f"     stock_value = {total_units} × €{line.item.unit_cost:.2f} = €{correct_value:.2f}")
        
        difference = correct_value - line.counted_value
        print(f"\n  📊 DIFFERENCE: €{difference:.2f}")
        
        if abs(difference) > Decimal('0.01'):
            print(f"  ❌ VALUATION MISMATCH!")
        else:
            print(f"  ✅ Values match")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nCURRENT ISSUE:")
print("  BIB items are using serving-based calculation:")
print("  stock_value = servings × cost_per_serving")
print("\nCORRECT LOGIC SHOULD BE:")
print("  stock_value = (full_units + partial_units) × unit_cost")
print("  Where:")
print("    - full_units = number of complete boxes")
print("    - partial_units = decimal fraction of a box (e.g., 0.5)")
print("    - unit_cost = cost of one full 18L box")
print("\nNo serving calculations needed for BIB stocktake.")
print("="*80 + "\n")
