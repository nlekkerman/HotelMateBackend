"""
Check Syrup Valuation Cost Issue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake, StockItem
from decimal import Decimal

print("=" * 80)
print("CHECK SYRUP VALUATION")
print("=" * 80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2, 
    period_start__year=2025, 
    period_start__month=2
).first()

print(f"\nStocktake: {stocktake.id} ({stocktake.period_start})")

# Get all syrup lines
syrup_lines = stocktake.lines.filter(item__subcategory='SYRUPS')
print(f"\nFound {syrup_lines.count()} syrup items")

print("\n" + "=" * 80)
print("ANALYSIS: Check a few syrups")
print("=" * 80)

for line in syrup_lines[:5]:
    syrup = line.item
    print(f"\n{syrup.sku} - {syrup.name}")
    print(f"  Size: {syrup.size} ({syrup.size_value}{syrup.size_unit})")
    print(f"  UOM: {syrup.uom} (bottle size in ml)")
    print(f"  Unit Cost: €{syrup.unit_cost} (per bottle)")
    print(f"  Cost per Serving: €{syrup.cost_per_serving} (per 35ml shot)")
    print(f"  Valuation Cost: €{line.valuation_cost}")
    
    print(f"\n  Counted:")
    print(f"    Full: {line.counted_full_units} bottles")
    print(f"    Partial: {line.counted_partial_units} (fractional)")
    print(f"    Total bottles: {float(line.counted_full_units) + float(line.counted_partial_units):.2f}")
    print(f"    Counted Qty (servings): {line.counted_qty}")
    print(f"    Counted Value: €{line.counted_value}")
    
    # What should the value be?
    total_bottles = float(line.counted_full_units) + float(line.counted_partial_units)
    expected_value_per_bottle = total_bottles * float(syrup.unit_cost)
    expected_value_per_serving = float(line.counted_qty) * float(line.valuation_cost)
    
    print(f"\n  Expected Values:")
    print(f"    If valued per bottle: {total_bottles:.2f} × €{syrup.unit_cost} = €{expected_value_per_bottle:.2f}")
    print(f"    If valued per serving: {line.counted_qty} × €{line.valuation_cost} = €{expected_value_per_serving:.2f}")
    print(f"    Actual: €{line.counted_value}")
    
    if abs(float(line.counted_value) - expected_value_per_bottle) < 0.01:
        print(f"    ✓ Matches bottle valuation")
    elif abs(float(line.counted_value) - expected_value_per_serving) < 0.01:
        print(f"    ✓ Matches serving valuation")
    else:
        print(f"    ❌ Doesn't match either!")

print("\n" + "=" * 80)
print("THE ISSUE")
print("=" * 80)
print("""
Syrups are stored as BOTTLES (e.g., 4.7 bottles = 4 full + 0.7 partial).
They should be VALUED per bottle, not per 35ml serving.

Backend converts to servings for tracking consumption:
  - 4.7 bottles × 700ml = 3,290ml ÷ 35ml = 94 servings

But for VALUATION (cost calculation):
  - Should use: 4.7 bottles × unit_cost (cost per bottle)
  - NOT: 94 servings × cost_per_serving

This is the same issue as BIB!
""")

print("\n" + "=" * 80)
print("CHECK CURRENT LOGIC")
print("=" * 80)

# Check if syrups use bottle valuation or serving valuation
line = syrup_lines.first()
total_bottles = float(line.counted_full_units) + float(line.counted_partial_units)
value_per_bottle = total_bottles * float(line.item.unit_cost)
value_per_serving = float(line.counted_qty) * float(line.valuation_cost)

print(f"\nTest item: {line.item.sku}")
print(f"Actual counted_value: €{line.counted_value}")
print(f"Bottle method: €{value_per_bottle:.2f}")
print(f"Serving method: €{value_per_serving:.2f}")

if abs(float(line.counted_value) - value_per_bottle) < 0.01:
    print("\n✓ Currently using BOTTLE valuation (CORRECT)")
elif abs(float(line.counted_value) - value_per_serving) < 0.01:
    print("\n❌ Currently using SERVING valuation (WRONG)")
    print("\nThis needs to be fixed in the model!")
