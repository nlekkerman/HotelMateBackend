"""
Helper functions for JUICES 3-level tracking (Cases + Bottles + ml)

These functions convert between:
1. Total bottles (e.g., 35.5 bottles)
2. Cases + Bottles + ml (e.g., 2 cases, 11 bottles, 500ml)
"""
from decimal import Decimal, ROUND_DOWN


def bottles_to_cases_bottles_ml(total_bottles, bottle_size_ml=1000, bottles_per_case=12):
    """
    Convert total bottles to Cases + Bottles + ml.
    
    Args:
        total_bottles (Decimal or float): Total bottles (can be fractional, e.g., 35.5)
        bottle_size_ml (int): Size of one bottle in ml (default 1000 for 1L)
        bottles_per_case (int): Bottles per case (default 12)
    
    Returns:
        tuple: (cases, bottles, ml)
    
    Example:
        >>> bottles_to_cases_bottles_ml(35.5, 1000, 12)
        (2, 11, 500)
        
        Calculation:
        - 35.5 bottles ÷ 12 = 2.958... → 2 full cases (24 bottles)
        - Remainder: 35.5 - 24 = 11.5 bottles
        - 11.5 bottles = 11 full bottles + 0.5 bottle
        - 0.5 bottle × 1000ml = 500ml
        
        Result: 2 cases, 11 bottles, 500ml
    """
    total_bottles = Decimal(str(total_bottles))
    bottle_size_ml = Decimal(str(bottle_size_ml))
    bottles_per_case = Decimal(str(bottles_per_case))
    
    # Step 1: Calculate full cases
    cases = int(total_bottles / bottles_per_case)
    
    # Step 2: Calculate remaining bottles after removing full cases
    bottles_after_cases = total_bottles - (cases * bottles_per_case)
    
    # Step 3: Split remaining bottles into full bottles + fractional
    full_bottles = int(bottles_after_cases)
    fractional_bottle = bottles_after_cases - full_bottles
    
    # Step 4: Convert fractional bottle to ml
    ml = int(fractional_bottle * bottle_size_ml)
    
    return cases, full_bottles, ml


def cases_bottles_ml_to_bottles(cases, bottles, ml, bottle_size_ml=1000, bottles_per_case=12):
    """
    Convert Cases + Bottles + ml back to total bottles.
    
    Args:
        cases (int or Decimal): Number of full cases
        bottles (int or Decimal): Number of loose bottles
        ml (int or Decimal): Ml from partial bottle
        bottle_size_ml (int): Size of one bottle in ml (default 1000)
        bottles_per_case (int): Bottles per case (default 12)
    
    Returns:
        Decimal: Total bottles (fractional)
    
    Example:
        >>> cases_bottles_ml_to_bottles(2, 11, 500, 1000, 12)
        Decimal('35.5')
        
        Calculation:
        - 2 cases × 12 = 24 bottles
        - + 11 loose bottles = 35 bottles
        - + 500ml ÷ 1000ml = 0.5 bottle
        - Total: 35.5 bottles
    """
    cases = Decimal(str(cases))
    bottles = Decimal(str(bottles))
    ml = Decimal(str(ml))
    bottle_size_ml = Decimal(str(bottle_size_ml))
    bottles_per_case = Decimal(str(bottles_per_case))
    
    # Calculate bottles from cases
    bottles_from_cases = cases * bottles_per_case
    
    # Convert ml to fractional bottle
    fractional_bottle = ml / bottle_size_ml
    
    # Total bottles
    total_bottles = bottles_from_cases + bottles + fractional_bottle
    
    return total_bottles


def cases_bottles_ml_to_servings(cases, bottles, ml, bottle_size_ml=1000, 
                                  bottles_per_case=12, serving_size_ml=200):
    """
    Convert Cases + Bottles + ml directly to servings.
    
    Args:
        cases (int or Decimal): Number of full cases
        bottles (int or Decimal): Number of loose bottles
        ml (int or Decimal): Ml from partial bottle
        bottle_size_ml (int): Size of one bottle in ml (default 1000)
        bottles_per_case (int): Bottles per case (default 12)
        serving_size_ml (int): Serving size in ml (default 200 for juices)
    
    Returns:
        Decimal: Total servings
    
    Example:
        >>> cases_bottles_ml_to_servings(2, 11, 500, 1000, 12, 200)
        Decimal('177.5')
        
        Calculation:
        - 2 cases = 24 bottles = 24,000ml
        - 11 bottles = 11,000ml
        - 500ml = 500ml
        - Total: 35,500ml ÷ 200ml = 177.5 servings
    """
    cases = Decimal(str(cases))
    bottles = Decimal(str(bottles))
    ml = Decimal(str(ml))
    bottle_size_ml = Decimal(str(bottle_size_ml))
    bottles_per_case = Decimal(str(bottles_per_case))
    serving_size_ml = Decimal(str(serving_size_ml))
    
    # Calculate total ml
    bottles_from_cases = cases * bottles_per_case
    total_bottles = bottles_from_cases + bottles
    total_ml_from_bottles = total_bottles * bottle_size_ml
    total_ml = total_ml_from_bottles + ml
    
    # Convert to servings
    servings = total_ml / serving_size_ml
    
    return servings


def servings_to_cases_bottles_ml(servings, bottle_size_ml=1000, 
                                  bottles_per_case=12, serving_size_ml=200):
    """
    Convert servings to Cases + Bottles + ml (reverse calculation).
    
    Args:
        servings (Decimal or float): Total servings
        bottle_size_ml (int): Size of one bottle in ml (default 1000)
        bottles_per_case (int): Bottles per case (default 12)
        serving_size_ml (int): Serving size in ml (default 200)
    
    Returns:
        tuple: (cases, bottles, ml)
    
    Example:
        >>> servings_to_cases_bottles_ml(177.5, 1000, 12, 200)
        (2, 11, 500)
        
        Calculation:
        - 177.5 servings × 200ml = 35,500ml
        - 35,500ml ÷ 1000ml = 35.5 bottles
        - Then use bottles_to_cases_bottles_ml()
    """
    servings = Decimal(str(servings))
    serving_size_ml = Decimal(str(serving_size_ml))
    
    # Convert servings to total ml
    total_ml = servings * serving_size_ml
    
    # Convert ml to total bottles
    bottle_size_ml_dec = Decimal(str(bottle_size_ml))
    total_bottles = total_ml / bottle_size_ml_dec
    
    # Use the bottles_to_cases_bottles_ml function
    return bottles_to_cases_bottles_ml(total_bottles, bottle_size_ml, bottles_per_case)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("JUICE HELPERS - Example Usage")
    print("=" * 80)
    
    # Example 1: User enters 35.5 bottles
    print("\n--- Example 1: Convert 35.5 bottles ---")
    bottles = 35.5
    cases, bottles_count, ml = bottles_to_cases_bottles_ml(bottles, 1000, 12)
    print(f"Input: {bottles} bottles")
    print(f"Output: {cases} cases + {bottles_count} bottles + {ml}ml")
    
    # Example 2: User counts 2 cases, 11 bottles, 500ml
    print("\n--- Example 2: Convert 2 cases, 11 bottles, 500ml to bottles ---")
    total = cases_bottles_ml_to_bottles(2, 11, 500, 1000, 12)
    print(f"Input: 2 cases + 11 bottles + 500ml")
    print(f"Output: {total} bottles")
    
    # Example 3: Calculate servings
    print("\n--- Example 3: Convert to servings ---")
    servings = cases_bottles_ml_to_servings(2, 11, 500, 1000, 12, 200)
    print(f"Input: 2 cases + 11 bottles + 500ml")
    print(f"Output: {servings} servings (200ml each)")
    
    # Example 4: Reverse - servings to cases/bottles/ml
    print("\n--- Example 4: Convert servings back ---")
    cases, bottles_count, ml = servings_to_cases_bottles_ml(177.5, 1000, 12, 200)
    print(f"Input: 177.5 servings")
    print(f"Output: {cases} cases + {bottles_count} bottles + {ml}ml")
    
    # Example 5: Edge cases
    print("\n--- Example 5: Edge Cases ---")
    
    # Exactly 1 case
    cases, bottles_count, ml = bottles_to_cases_bottles_ml(12, 1000, 12)
    print(f"12 bottles → {cases} cases + {bottles_count} bottles + {ml}ml")
    
    # Less than 1 case
    cases, bottles_count, ml = bottles_to_cases_bottles_ml(5.75, 1000, 12)
    print(f"5.75 bottles → {cases} cases + {bottles_count} bottles + {ml}ml")
    
    # Only ml (fractional bottle)
    cases, bottles_count, ml = bottles_to_cases_bottles_ml(0.25, 1000, 12)
    print(f"0.25 bottles → {cases} cases + {bottles_count} bottles + {ml}ml")
    
    # Large number
    cases, bottles_count, ml = bottles_to_cases_bottles_ml(150.333, 1000, 12)
    print(f"150.333 bottles → {cases} cases + {bottles_count} bottles + {ml}ml")
    
    print("\n" + "=" * 80)
