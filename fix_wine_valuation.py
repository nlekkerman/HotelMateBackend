"""
Fix Wine Valuation Cost in Stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake, StockItem
from decimal import Decimal

print("=" * 80)
print("FIX WINE VALUATION COSTS")
print("=" * 80)

# Get February stocktake
stocktake = Stocktake.objects.filter(hotel_id=2, period_start__year=2025, period_start__month=2).first()
print(f"\nStocktake: {stocktake.id} ({stocktake.period_start})")
print(f"Status: {stocktake.status}")

# Get all wine lines
wine_lines = stocktake.lines.filter(item__category_id='W')
print(f"\nFound {wine_lines.count()} wine items")

print("\n" + "=" * 80)
print("ANALYSIS: Why is valuation_cost wrong?")
print("=" * 80)

# Check a few wines
for line in wine_lines[:3]:
    wine = line.item
    print(f"\n{wine.sku} - {wine.name}")
    print(f"  Current UOM: {wine.uom}")
    print(f"  Unit Cost: €{wine.unit_cost}")
    print(f"  Cost per Serving: €{wine.cost_per_serving}")
    print(f"  Valuation Cost (frozen): €{line.valuation_cost}")
    
    # What UOM would give this valuation_cost?
    if line.valuation_cost > 0:
        implied_uom = wine.unit_cost / line.valuation_cost
        print(f"  → Implied UOM (unit_cost / valuation_cost): {implied_uom:.2f}")
        print(f"  → This suggests valuation_cost was set when UOM was ~{implied_uom:.0f}")

print("\n" + "=" * 80)
print("SOLUTION")
print("=" * 80)
print("""
The problem: valuation_cost was frozen when wines had UOM=5 (glasses per bottle).
Now wines have UOM=1 (bottle = 1 unit), but valuation_cost wasn't updated.

Fix: Update all wine stocktake lines to use correct valuation_cost.

For wines with UOM=1:
  valuation_cost = unit_cost / 1 = unit_cost
""")

response = input("\nUpdate all wine valuation costs? (yes/no): ")

if response.lower() == 'yes':
    print("\nUpdating...")
    updated_count = 0
    
    for line in wine_lines:
        old_val = line.valuation_cost
        # Set valuation_cost = cost_per_serving (which equals unit_cost when UOM=1)
        line.valuation_cost = line.item.cost_per_serving
        line.save()
        
        new_val = line.valuation_cost
        print(f"  {line.item.sku}: €{old_val} → €{new_val}")
        updated_count += 1
    
    print(f"\n✓ Updated {updated_count} wine items")
    
    # Verify one item
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    line = wine_lines.get(item__sku='W0023')
    line.refresh_from_db()
    
    print(f"\nW0023 - {line.item.name}")
    print(f"  Counted: {line.counted_qty} servings")
    print(f"  Valuation Cost: €{line.valuation_cost}")
    print(f"  Counted Value: €{line.counted_value}")
    print(f"  Expected: {line.counted_qty} × €{line.item.unit_cost} = €{float(line.counted_qty) * float(line.item.unit_cost):.2f}")
    
    if abs(float(line.counted_value) - (float(line.counted_qty) * float(line.item.unit_cost))) < 0.01:
        print("\n  ✓ CORRECT!")
    else:
        print("\n  ❌ Still wrong")
else:
    print("\nSkipped update")
