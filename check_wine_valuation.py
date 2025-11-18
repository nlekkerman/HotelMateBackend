"""
Check Wine Valuation Cost Issue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake, StockItem
from decimal import Decimal

print("=" * 80)
print("FIND RECENT STOCKTAKES")
print("=" * 80)

stocktakes = Stocktake.objects.filter(hotel_id=2).order_by('-period_start')[:5]
for st in stocktakes:
    print(f"{st.id}: {st.period_start} to {st.period_end} ({st.status})")

# Use the most recent one
stocktake = stocktakes.first()
print(f"\nUsing stocktake: {stocktake.id} ({stocktake.period_start})")

print("\n" + "=" * 80)
print("CHECK WINE W0023 VALUATION")
print("=" * 80)

# Get the wine item
wine = StockItem.objects.get(sku='W0023', hotel_id=2)
print(f"\nItem: {wine.sku} - {wine.name}")
print(f"UOM: {wine.uom}")
print(f"Unit Cost: €{wine.unit_cost}")
print(f"Cost per Serving: €{wine.cost_per_serving}")

# Get the stocktake line
try:
    line = stocktake.lines.get(item=wine)
    
    print(f"\n--- STOCKTAKE LINE ---")
    print(f"Valuation Cost (frozen): €{line.valuation_cost}")
    print(f"Counted Full Units: {line.counted_full_units}")
    print(f"Counted Partial Units: {line.counted_partial_units}")
    print(f"Counted Qty (servings): {line.counted_qty}")
    print(f"Counted Value: €{line.counted_value}")
    
    print(f"\n--- CALCULATION BREAKDOWN ---")
    print(f"Formula: counted_qty × valuation_cost")
    print(f"Calculation: {line.counted_qty} × €{line.valuation_cost} = €{float(line.counted_qty) * float(line.valuation_cost):.2f}")
    
    print(f"\n--- EXPECTED vs ACTUAL ---")
    expected_with_unit_cost = float(line.counted_qty) * float(wine.unit_cost)
    expected_with_cost_per_serving = float(line.counted_qty) * float(wine.cost_per_serving)
    
    print(f"If using unit_cost: {line.counted_qty} × €{wine.unit_cost} = €{expected_with_unit_cost:.2f}")
    print(f"If using cost_per_serving: {line.counted_qty} × €{wine.cost_per_serving} = €{expected_with_cost_per_serving:.2f}")
    print(f"Actual counted_value: €{line.counted_value}")
    
    if abs(float(line.counted_value) - expected_with_unit_cost) < 0.01:
        print("\n✓ Matches unit_cost calculation")
    elif abs(float(line.counted_value) - expected_with_cost_per_serving) < 0.01:
        print("\n✓ Matches cost_per_serving calculation")
    else:
        print(f"\n❌ Doesn't match either calculation!")
    
    print(f"\n--- THE PROBLEM ---")
    if float(line.valuation_cost) == float(wine.cost_per_serving):
        print(f"✓ valuation_cost ({line.valuation_cost}) = cost_per_serving ({wine.cost_per_serving})")
        print(f"This is CORRECT for wine with UOM=1")
    else:
        print(f"❌ valuation_cost ({line.valuation_cost}) ≠ cost_per_serving ({wine.cost_per_serving})")
        print(f"This will cause incorrect value calculations!")

except StocktakeLine.DoesNotExist:
    print(f"\n❌ No stocktake line found for {wine.sku} in this stocktake")
    
print("\n" + "=" * 80)
print("CHECK ALL WINES IN STOCKTAKE")
print("=" * 80)

wine_lines = stocktake.lines.filter(item__category_id='W')[:5]
print(f"\nShowing first 5 wine items:")

for line in wine_lines:
    expected = float(line.counted_qty) * float(line.item.unit_cost)
    actual = float(line.counted_value)
    match = "✓" if abs(expected - actual) < 0.01 else "❌"
    
    print(f"\n{line.item.sku}: {line.counted_qty} servings")
    print(f"  valuation_cost: €{line.valuation_cost}")
    print(f"  Expected: €{expected:.2f}")
    print(f"  Actual: €{actual:.2f} {match}")
