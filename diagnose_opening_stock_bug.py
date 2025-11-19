"""
Diagnose Opening Stock Calculation Bug
Shows how February closing becomes March opening
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_porter.settings')
django.setup()

from inventory.models import StocktakeLine, Stocktake, Period

# Get February closing (Stocktake #37)
feb_stocktake = Stocktake.objects.get(id=37)
print(f"\n{'='*80}")
print(f"FEBRUARY CLOSING STOCKTAKE #{feb_stocktake.id}")
print(f"Period: {feb_stocktake.period}")
print(f"{'='*80}\n")

# Get March opening (Stocktake #44)
march_stocktake = Stocktake.objects.get(id=44)
print(f"MARCH OPENING STOCKTAKE #{march_stocktake.id}")
print(f"Period: {march_stocktake.period}")
print(f"{'='*80}\n")

# Check syrups
syrup_skus = ['M3', 'M0006', 'M13', 'M04', 'M0014']

for sku in syrup_skus:
    # February closing
    feb_line = StocktakeLine.objects.filter(
        stocktake=feb_stocktake,
        stock_item__sku=sku
    ).first()
    
    # March opening
    march_line = StocktakeLine.objects.filter(
        stocktake=march_stocktake,
        stock_item__sku=sku
    ).first()
    
    if feb_line and march_line:
        item = feb_line.stock_item
        print(f"\n{item.sku} - {item.name}")
        print(f"  Category: {item.category.name}, Subcategory: {item.subcategory.name}")
        print(f"  Size: {item.size_ml}ml, Serving: {item.serving_size_ml}ml")
        print(f"  Servings per bottle: {item.servings_per_unit}")
        
        print(f"\n  FEBRUARY CLOSING:")
        print(f"    Counted: {feb_line.full_units}.{feb_line.partial_units} bottles")
        print(f"    Total bottles: {feb_line.total_units_as_decimal}")
        print(f"    Servings: {feb_line.servings}")
        print(f"    Value: €{feb_line.total_value}")
        
        print(f"\n  MARCH OPENING (SHOULD MATCH FEB CLOSING):")
        print(f"    Opening: {march_line.opening_full_units}.{march_line.opening_partial_units} bottles")
        print(f"    Total bottles: {march_line.opening_total_units}")
        print(f"    Servings: {march_line.opening_servings}")
        print(f"    Value: €{march_line.opening_value}")
        
        # Calculate what it SHOULD be
        expected_servings = feb_line.servings
        expected_value = feb_line.total_value
        
        print(f"\n  ❌ BUG DETECTED:")
        print(f"    Expected opening servings: {expected_servings}")
        print(f"    Actual opening servings: {march_line.opening_servings}")
        print(f"    WRONG by factor of: {march_line.opening_servings / expected_servings if expected_servings > 0 else 0:.1f}x")
        print(f"    (This is the serving_size_ml: {item.serving_size_ml}ml)")
        
        print(f"\n  {'─'*70}")

print(f"\n{'='*80}")
print("DIAGNOSIS: Opening stock is being multiplied by serving_size_ml!")
print("This creates massive phantom stock values.")
print(f"{'='*80}\n")
