"""
Test the updated JUICES logic with 2-field input:
- counted_full_units = cases
- counted_partial_units = bottles (with decimals)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.juice_helpers import cases_bottles_ml_to_servings

print("=" * 80)
print("JUICES 2-FIELD INPUT TEST")
print("=" * 80)

# Test Case 1: User enters 3 cases + 3.5 bottles
print("\n--- Test 1: 3 cases + 3.5 bottles (1L bottles) ---")
cases = 3
bottles_with_fraction = Decimal('3.5')
bottle_size_ml = 1000

# Split decimal bottles into whole + ml
full_bottles = int(bottles_with_fraction)
ml = (bottles_with_fraction - full_bottles) * bottle_size_ml

print(f"Input: {cases} cases + {bottles_with_fraction} bottles")
print(f"Decoded: {cases} cases + {full_bottles} bottles + {ml}ml")

# Calculate servings
servings = cases_bottles_ml_to_servings(
    cases, full_bottles, ml,
    bottle_size_ml=bottle_size_ml,
    bottles_per_case=12,
    serving_size_ml=200
)
print(f"Total servings: {servings} (200ml each)")

# Verify math
total_ml = (cases * 12 * 1000) + (full_bottles * 1000) + ml
expected_servings = total_ml / 200
print(f"Verification: {total_ml}ml ÷ 200 = {expected_servings} servings")
print(f"✓ PASS" if servings == expected_servings else "✗ FAIL")

# Test Case 2: User enters 0 cases + 150.5 bottles
print("\n--- Test 2: 0 cases + 150.5 bottles (1L bottles) ---")
cases = 0
bottles_with_fraction = Decimal('150.5')

full_bottles = int(bottles_with_fraction)
ml = (bottles_with_fraction - full_bottles) * bottle_size_ml

print(f"Input: {cases} cases + {bottles_with_fraction} bottles")
print(f"Decoded: {cases} cases + {full_bottles} bottles + {ml}ml")

servings = cases_bottles_ml_to_servings(
    cases, full_bottles, ml,
    bottle_size_ml=bottle_size_ml,
    bottles_per_case=12,
    serving_size_ml=200
)
print(f"Total servings: {servings} (200ml each)")

total_ml = (cases * 12 * 1000) + (full_bottles * 1000) + ml
expected_servings = total_ml / 200
print(f"Verification: {total_ml}ml ÷ 200 = {expected_servings} servings")
print(f"✓ PASS" if servings == expected_servings else "✗ FAIL")

# Test Case 3: User enters 59 cases + 8.008 bottles (your real data)
print("\n--- Test 3: 59 cases + 8.008 bottles (RED NASHS) ---")
cases = 59
bottles_with_fraction = Decimal('8.008')

full_bottles = int(bottles_with_fraction)
ml = (bottles_with_fraction - full_bottles) * bottle_size_ml

print(f"Input: {cases} cases + {bottles_with_fraction} bottles")
print(f"Decoded: {cases} cases + {full_bottles} bottles + {ml:.0f}ml")

servings = cases_bottles_ml_to_servings(
    cases, full_bottles, ml,
    bottle_size_ml=bottle_size_ml,
    bottles_per_case=12,
    serving_size_ml=200
)
print(f"Total servings: {servings} (200ml each)")

total_ml = (cases * 12 * 1000) + (full_bottles * 1000) + ml
expected_servings = total_ml / 200
print(f"Verification: {total_ml}ml ÷ 200 = {expected_servings} servings")
print(f"✓ PASS" if abs(servings - expected_servings) < Decimal('0.01') else "✗ FAIL")

# Test Case 4: Edge cases
print("\n--- Test 4: Edge Cases ---")
test_cases = [
    (0, Decimal('0.25'), "Quarter bottle (250ml)"),
    (1, Decimal('11.999'), "Almost full case"),
    (0, Decimal('12.0'), "Exactly 1 case worth"),
    (5, Decimal('0'), "Exactly 5 cases"),
]

for cases, bottles_frac, description in test_cases:
    full_bottles = int(bottles_frac)
    ml = (bottles_frac - full_bottles) * bottle_size_ml
    servings = cases_bottles_ml_to_servings(
        cases, full_bottles, ml, 1000, 12, 200
    )
    print(f"{description}: {cases} cases + {bottles_frac} bottles = {servings:.2f} servings")

print("\n" + "=" * 80)
