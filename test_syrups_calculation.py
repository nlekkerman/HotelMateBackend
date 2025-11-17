"""
Test syrups calculation logic with different fractional values
"""
from decimal import Decimal

SYRUP_SERVING_SIZE = Decimal('35')  # ml per serving

print("=" * 80)
print("SYRUPS CALCULATION TEST - Individual Bottles with Decimals")
print("=" * 80)

# Test cases: (full_bottles, partial_bottles, bottle_size_ml)
test_cases = [
    (4, 0.7, 700, "4.7 bottles of 700ml syrup"),
    (10, 0.5, 700, "10.5 bottles of 700ml syrup"),
    (5, 0.25, 700, "5.25 bottles of 700ml syrup"),
    (3, 0.0, 700, "3 bottles of 700ml syrup (no partial)"),
    (4, 0.7, 1000, "4.7 bottles of 1L syrup"),
    (2, 0.8, 1000, "2.8 bottles of 1L syrup"),
]

print("\nFormula: (full + partial) × bottle_size_ml ÷ 35ml = servings")
print("-" * 80)

for full, partial, bottle_size, description in test_cases:
    full_dec = Decimal(str(full))
    partial_dec = Decimal(str(partial))
    bottle_size_dec = Decimal(str(bottle_size))
    
    total_bottles = full_dec + partial_dec
    total_ml = total_bottles * bottle_size_dec
    servings = total_ml / SYRUP_SERVING_SIZE
    
    print(f"\n{description}")
    print(f"  Input: full={full}, partial={partial}")
    print(f"  Total: {total_bottles} bottles")
    print(f"  Total ml: {total_ml}ml")
    print(f"  Servings: {servings:.2f}")

print("\n" + "=" * 80)
print("COST VALUATION EXAMPLE")
print("=" * 80)

cost_per_bottle = Decimal('10.25')
full = Decimal('4')
partial = Decimal('0.7')

total_bottles = full + partial
total_cost = total_bottles * cost_per_bottle

print(f"\nCost per bottle: €{cost_per_bottle}")
print(f"Stock: {total_bottles} bottles")
print(f"Total value: €{total_cost:.2f}")

print("\n" + "=" * 80)
print("✅ This approach matches SPIRITS and WINE logic!")
print("=" * 80)
