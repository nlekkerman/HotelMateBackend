"""
Test BIB variance display - show exactly what frontend receives
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine
from stock_tracker.stock_serializers import StocktakeLineSerializer

print("\n" + "="*80)
print("BIB VARIANCE DISPLAY - WHAT FRONTEND RECEIVES")
print("="*80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

if stocktake:
    # Get one BIB line
    line = StocktakeLine.objects.filter(
        stocktake=stocktake,
        item__sku='M25'
    ).select_related('item').first()
    
    if line:
        print(f"\nItem: {line.item.sku} - {line.item.name}")
        print(f"Subcategory: {line.item.subcategory}")
        print(f"Unit cost: €{line.item.unit_cost}")
        
        print(f"\n{'-'*80}")
        print("STOCK VALUES (in boxes)")
        print(f"{'-'*80}")
        print(f"Opening: {line.opening_qty} boxes")
        print(f"Purchases: {line.purchases} boxes")
        print(f"Expected: {line.expected_qty} boxes")
        print(f"Counted: {line.counted_qty} boxes")
        print(f"Variance: {line.variance_qty} boxes")
        
        print(f"\n{'-'*80}")
        print("API RESPONSE FROM SERIALIZER")
        print(f"{'-'*80}")
        
        # Serialize to see what frontend gets
        serializer = StocktakeLineSerializer(line)
        data = serializer.data
        
        print(f"\nOpening Display:")
        print(f"  opening_display_full_units: '{data['opening_display_full_units']}'")
        print(f"  opening_display_partial_units: '{data['opening_display_partial_units']}'")
        
        print(f"\nCounted Display:")
        print(f"  counted_display_full_units: '{data['counted_display_full_units']}'")
        print(f"  counted_display_partial_units: '{data['counted_display_partial_units']}'")
        
        print(f"\nExpected Display:")
        print(f"  expected_display_full_units: '{data['expected_display_full_units']}'")
        print(f"  expected_display_partial_units: '{data['expected_display_partial_units']}'")
        
        print(f"\nVariance Display:")
        print(f"  variance_display_full_units: '{data['variance_display_full_units']}'")
        print(f"  variance_display_partial_units: '{data['variance_display_partial_units']}'")
        print(f"  variance_qty: {data['variance_qty']}")
        print(f"  variance_value: {data['variance_value']}")
        
        print(f"\n{'-'*80}")
        print("FRONTEND SHOULD DISPLAY")
        print(f"{'-'*80}")
        
        full = data['variance_display_full_units']
        partial = data['variance_display_partial_units']
        total = float(line.variance_qty)
        value = data['variance_value']
        
        print(f"\nOption 1: Separate fields")
        print(f"  {full} containers")
        print(f"  {partial} serves")
        print(f"  €{value} ⚠️")
        print(f"  ({total:.2f} boxes)")
        
        print(f"\nOption 2: Combined with 'boxes' label")
        print(f"  {full} containers")
        print(f"  {partial} serves")
        print(f"  €{value} ⚠️")
        print(f"  ({total:.2f} boxes)")
        
        print(f"\nOption 3: Change label dynamically")
        print(f"  {full} containers")
        print(f"  {partial} serves")
        print(f"  €{value} ⚠️")
        print(f"  ({total:.2f} {'boxes' if line.item.subcategory == 'BIB' else 'servings'})")
        
        print(f"\n{'-'*80}")
        print("SERVING SIZE INFO (for reference only - don't display)")
        print(f"{'-'*80}")
        print(f"Serving size: {line.item.size_value}ml")
        servings_per_box = float(18000 / line.item.size_value)
        print(f"Servings per box: {servings_per_box:.0f}")
        drink_servings = total * servings_per_box
        print(f"If converted to drink servings: {drink_servings:.0f} servings")
        print(f"  ⚠️ DON'T show this! Show boxes only!")

print("\n" + "="*80 + "\n")
