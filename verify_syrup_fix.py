"""
Verify Syrup Valuation Fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, Stocktake

print("=" * 80)
print("VERIFY SYRUP VALUATION FIX")
print("=" * 80)

# Get February stocktake
stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start__year=2025,
    period_start__month=2
).first()

# Get syrup lines
syrup_lines = stocktake.lines.filter(item__subcategory='SYRUPS')

print(f"\nChecking {syrup_lines.count()} syrup items...")

print("\n" + "=" * 80)
print("BEFORE vs AFTER")
print("=" * 80)

for line in syrup_lines[:5]:
    syrup = line.item
    total_bottles = float(line.counted_full_units) + float(line.counted_partial_units)
    
    # Refresh from DB to get new calculated value
    line.refresh_from_db()
    
    expected = total_bottles * float(syrup.unit_cost)
    actual = float(line.counted_value)
    
    match = "✓" if abs(expected - actual) < 0.01 else "❌"
    
    print(f"\n{syrup.sku} - {syrup.name}")
    print(f"  Bottles: {total_bottles:.2f}")
    print(f"  Unit Cost: €{syrup.unit_cost}")
    print(f"  Expected Value: €{expected:.2f}")
    print(f"  Actual Value: €{actual:.2f} {match}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

all_correct = True
for line in syrup_lines:
    total_bottles = float(line.counted_full_units) + float(line.counted_partial_units)
    expected = total_bottles * float(line.item.unit_cost)
    actual = float(line.counted_value)
    
    if abs(expected - actual) > 0.01:
        print(f"❌ {line.item.sku}: Expected €{expected:.2f}, got €{actual:.2f}")
        all_correct = False

if all_correct:
    print("\n✓✓✓ ALL SYRUPS NOW CORRECTLY VALUED PER BOTTLE! ✓✓✓")
else:
    print("\n❌ Some syrups still have incorrect values")

# Check total impact
print("\n" + "=" * 80)
print("TOTAL VALUE IMPACT")
print("=" * 80)

total_old = sum(
    float(line.counted_qty) * float(line.valuation_cost)
    for line in syrup_lines
)

total_new = sum(float(line.counted_value) for line in syrup_lines)

print(f"Old total (per serving): €{total_old:.2f}")
print(f"New total (per bottle): €{total_new:.2f}")
print(f"Difference: €{total_new - total_old:.2f}")
