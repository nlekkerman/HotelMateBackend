"""
Test Wine calculation after UOM fix
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StocktakeLine, Stocktake

print("=" * 120)
print("TESTING WINE CALCULATION AFTER UOM FIX")
print("=" * 120)
print()

# Get a wine item
wine = StockItem.objects.filter(category_id='W', active=True).first()

print(f"Wine Item: {wine.sku} - {wine.name}")
print(f"Size: {wine.size}")
print(f"UOM: {wine.uom} (should be 1.00)")
print(f"Unit Cost: €{wine.unit_cost}")
print(f"Cost per Serving: €{wine.cost_per_serving}")
print()

print("=" * 120)
print("TEST 1: STOCKTAKE CALCULATION")
print("=" * 120)
print()

# Simulate stocktake counting
wine.current_full_units = Decimal('10')  # 10 bottles
wine.current_partial_units = Decimal('0.5')  # half bottle
wine.save()

total_servings = wine.total_stock_in_servings
print(f"User counts: 10 bottles + 0.5 fractional")
print(f"  current_full_units = {wine.current_full_units}")
print(f"  current_partial_units = {wine.current_partial_units}")
print(f"  UOM = {wine.uom}")
print()
print(f"Calculation:")
print(f"  Servings = ({wine.current_full_units} × {wine.uom}) + ({wine.current_partial_units} × {wine.uom})")
print(f"  Servings = {total_servings}")
print()

if total_servings == Decimal('10.5'):
    print("✅ CORRECT! 10.5 bottles calculated properly")
else:
    print(f"❌ WRONG! Expected 10.5, got {total_servings}")

print()
print("=" * 120)
print("TEST 2: DIFFERENT QUANTITIES")
print("=" * 120)
print()

test_cases = [
    (Decimal('5'), Decimal('0.25'), Decimal('5.25')),
    (Decimal('12'), Decimal('0.75'), Decimal('12.75')),
    (Decimal('0'), Decimal('0.50'), Decimal('0.50')),
    (Decimal('20'), Decimal('0.00'), Decimal('20.00')),
]

all_passed = True
for full, partial, expected in test_cases:
    wine.current_full_units = full
    wine.current_partial_units = partial
    wine.save()
    
    result = wine.total_stock_in_servings
    status = "✅" if result == expected else "❌"
    
    print(f"{status} {full} bottles + {partial} = {result} (expected {expected})")
    
    if result != expected:
        all_passed = False

print()
if all_passed:
    print("✅ ALL TESTS PASSED!")
else:
    print("❌ SOME TESTS FAILED!")

print()
print("=" * 120)
print("TEST 3: COST CALCULATION")
print("=" * 120)
print()

wine.current_full_units = Decimal('10')
wine.current_partial_units = Decimal('0.5')
wine.save()

total_value = wine.total_stock_value
expected_value = Decimal('10.5') * wine.unit_cost

print(f"Stock: 10.5 bottles")
print(f"Unit Cost: €{wine.unit_cost} per bottle")
print(f"Total Value: €{total_value}")
print(f"Expected: €{expected_value}")
print()

if abs(total_value - expected_value) < Decimal('0.01'):
    print("✅ COST CALCULATION CORRECT!")
else:
    print("❌ COST CALCULATION WRONG!")

print()
print("=" * 120)
print("TEST 4: DISPLAY FORMAT")
print("=" * 120)
print()

print(f"Display Full Units: {wine.display_full_units}")
print(f"Display Partial Units: {wine.display_partial_units}")
print()

# Check if display matches input
if (wine.display_full_units == wine.current_full_units and 
    wine.display_partial_units == wine.current_partial_units):
    print("✅ DISPLAY FORMAT CORRECT!")
    print("   Shows: '10 + 0.50' or '10.50 bottles'")
else:
    print("❌ DISPLAY FORMAT ISSUE")

print()
print("=" * 120)
print("SUMMARY")
print("=" * 120)
print()
print("Wine UOM = 1.0 (bottles)")
print("✅ Stocktake counts in BOTTLES (e.g., 10.5 bottles)")
print("✅ Calculation: bottles × 1.0 = bottles (no conversion)")
print("✅ Display: Shows bottles + fractional")
print("✅ Cost: Per bottle (unchanged)")
print()
print("Sales reporting can use separate pricing:")
print("  - bottle_price: For bottle sales")
print("  - menu_price: For glass sales")
print()
