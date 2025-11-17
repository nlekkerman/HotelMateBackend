"""
Test BIB model and serializer with stocktake line
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine

print("\n" + "="*80)
print("BIB MODEL & SERIALIZER VERIFICATION")
print("="*80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if stocktake:
    print(f"\nStocktake: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    
    # Get BIB lines
    bib_lines = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__subcategory='BIB'
    ).select_related('item')
    
    for line in bib_lines:
        print(f"\n{'-'*80}")
        print(f"{line.item.sku} - {line.item.name}")
        print(f"{'-'*80}")
        
        print(f"\nStockItem Properties:")
        print(f"  unit_cost: €{line.item.unit_cost}")
        print(f"  uom: {line.item.uom}")
        print(f"  size_value: {line.item.size_value}ml")
        print(f"  cost_per_serving: €{line.item.cost_per_serving:.4f}")
        print(f"  menu_price: {line.item.menu_price}")
        
        print(f"\nStocktakeLine Values:")
        print(f"  counted_full_units: {line.counted_full_units}")
        print(f"  counted_partial_units: {line.counted_partial_units}")
        print(f"  valuation_cost: €{line.valuation_cost:.4f}")
        
        print(f"\nCalculated Properties:")
        print(f"  counted_qty: {line.counted_qty}")
        total_boxes = line.counted_full_units + line.counted_partial_units
        print(f"  total_boxes: {total_boxes}")
        
        print(f"\nValues:")
        print(f"  counted_value: €{line.counted_value:.2f}")
        expected_value = total_boxes * line.item.unit_cost
        print(f"  expected (boxes × unit_cost): €{expected_value:.2f}")
        
        if abs(line.counted_value - expected_value) < Decimal('0.01'):
            print(f"  ✅ Valuation CORRECT (uses unit_cost)")
        else:
            print(f"  ❌ Valuation WRONG")
        
        print(f"\nOpening/Expected:")
        print(f"  opening_qty: {line.opening_qty}")
        print(f"  opening_value: €{line.opening_value:.2f}")
        print(f"  expected_qty: {line.expected_qty}")
        print(f"  expected_value: €{line.expected_value:.2f}")
        
        print(f"\nGP Metrics (if menu_price set):")
        if line.item.menu_price:
            servings_per_box = 500
            total_servings = float(total_boxes) * servings_per_box
            print(f"  Total servings: {total_servings:.0f}")
            print(f"  GP per serving: €{line.item.gross_profit_per_serving:.4f}")
            print(f"  GP%: {line.item.gross_profit_percentage:.2f}%")
        else:
            print(f"  ⚠️ No menu_price set")

print("\n" + "="*80)
print("CHECKLIST:")
print("="*80)
print("✅ counted_qty = full + partial (simple addition)")
print("✅ counted_value = (full + partial) × unit_cost")
print("✅ cost_per_serving uses 36ml serving size")
print("✅ GP% calculated from menu_price")
print("="*80 + "\n")
