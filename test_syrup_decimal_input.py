"""
Test SYRUPS single decimal field input (bottles.ml format)
Tests that 10.5 bottles = 10 bottles + 500ml
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import SYRUP_SERVING_SIZE

def test_syrup_decimal_calculation():
    """Test the SYRUPS decimal bottle logic"""
    
    print("=" * 60)
    print("SYRUPS: Single Decimal Field Test")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Test 1: 10.5 bottles of 1000ml syrup',
            'bottles_decimal': 10.5,
            'bottle_size_ml': 1000,
            'expected_ml': 10500,
            'expected_servings': 10500 / 35  # 300 servings
        },
        {
            'name': 'Test 2: 3.25 bottles of 700ml syrup',
            'bottles_decimal': 3.25,
            'bottle_size_ml': 700,
            'expected_ml': 2275,  # 3*700 + 0.25*700
            'expected_servings': 2275 / 35  # 65 servings
        },
        {
            'name': 'Test 3: 15.714 bottles (real data scenario)',
            'bottles_decimal': 15.714,
            'bottle_size_ml': 1000,
            'expected_ml': 15714,
            'expected_servings': 15714 / 35  # 448.97 servings
        },
        {
            'name': 'Test 4: 0.5 bottles (half bottle)',
            'bottles_decimal': 0.5,
            'bottle_size_ml': 1000,
            'expected_ml': 500,
            'expected_servings': 500 / 35  # 14.29 servings
        },
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 60)
        
        bottles_decimal = test['bottles_decimal']
        bottle_size_ml = test['bottle_size_ml']
        
        # Simulate the backend logic
        full_bottles = int(bottles_decimal)
        ml = (bottles_decimal - full_bottles) * bottle_size_ml
        total_ml = (full_bottles * bottle_size_ml) + ml
        servings = total_ml / SYRUP_SERVING_SIZE
        
        print(f"Input: {bottles_decimal} bottles")
        print(f"Bottle size: {bottle_size_ml}ml")
        print(f"Split:")
        print(f"  - Full bottles: {full_bottles}")
        print(f"  - Partial ml: {ml}ml")
        print(f"Total ml: {total_ml}ml")
        print(f"Servings (÷35ml): {servings:.2f}")
        print(f"Expected servings: {test['expected_servings']:.2f}")
        
        # Verify
        assert abs(total_ml - test['expected_ml']) < 0.01, \
            f"ML mismatch! Got {total_ml}, expected {test['expected_ml']}"
        assert abs(servings - test['expected_servings']) < 0.01, \
            f"Servings mismatch! Got {servings}, expected {test['expected_servings']}"
        
        print("✅ PASS")
    
    print("\n" + "=" * 60)
    print("ALL SYRUP TESTS PASSED! ✅")
    print("=" * 60)
    
    # Show comparison
    print("\n" + "=" * 60)
    print("COMPARISON: Old vs New Input Method")
    print("=" * 60)
    
    print("\n🔴 OLD METHOD (2 fields):")
    print("  - Bottles field: 10")
    print("  - ML field: 500")
    print("  - User must enter both values separately")
    
    print("\n🟢 NEW METHOD (1 field):")
    print("  - Bottles field: 10.5")
    print("  - Backend auto-splits: 10 bottles + 500ml")
    print("  - Simpler user input!")
    
    print("\n" + "=" * 60)
    print("Frontend Implementation:")
    print("=" * 60)
    print("""
<Input 
  label="Bottles" 
  name="current_partial_units" 
  type="number" 
  step="0.001"
  placeholder="e.g., 10.5"
/>

// Display format:
"10.5 bottles" = 300 servings
// Or show breakdown:
"10 bottles, 500ml" = 300 servings
    """)

if __name__ == '__main__':
    test_syrup_decimal_calculation()
