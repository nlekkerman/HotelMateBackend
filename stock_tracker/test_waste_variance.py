"""
Test: How Waste Affects Variance

This demonstrates the relationship between waste, expected qty, and variance.
"""

from decimal import Decimal

print("="*80)
print("DEMONSTRATION: How Waste Affects Variance")
print("="*80)

# Scenario: Broken Keg
print("\n📦 SCENARIO: Broken Keg During Delivery")
print("-" * 80)

opening = Decimal('88')  # 1 full keg
purchases = Decimal('88')  # Delivered 1 keg
sales = Decimal('100')  # Sold some pints
counted = Decimal('0')  # Nothing left (keg broke)

print(f"\nStock Movements:")
print(f"  Opening:  {opening} pints (1 keg)")
print(f"  Purchases: +{purchases} pints (1 keg delivered)")
print(f"  Sales:    -{sales} pints (sold to customers)")
print(f"  Counted:  {counted} pints (nothing on shelf)")

# WITHOUT waste recorded
print("\n" + "="*80)
print("BEFORE Recording Waste (Forgot to log broken keg)")
print("="*80)

waste_before = Decimal('0')
expected_before = opening + purchases - sales - waste_before
variance_before = counted - expected_before

print(f"\nCalculation:")
print(f"  Expected = Opening + Purchases - Sales - Waste")
print(f"           = {opening} + {purchases} - {sales} - {waste_before}")
print(f"           = {expected_before} pints")
print(f"\n  Variance = Counted - Expected")
print(f"           = {counted} - {expected_before}")
print(f"           = {variance_before} pints")

print(f"\n📊 Result:")
print(f"  Expected: {expected_before} pints")
print(f"  Counted:  {counted} pints")
print(f"  Variance: {variance_before} pints ⚠️ HUGE SHORTAGE!")
print(f"\n  ❌ This looks like {abs(variance_before)} pints were stolen or lost!")

# WITH waste recorded
print("\n" + "="*80)
print("AFTER Recording Waste (Logged the broken keg)")
print("="*80)

waste_after = Decimal('76')  # The amount that was in the broken keg
expected_after = opening + purchases - sales - waste_after
variance_after = counted - expected_after

print(f"\nAdded Movement:")
print(f"  Type: WASTE")
print(f"  Quantity: {waste_after} pints")
print(f"  Notes: 'Keg damaged during delivery'")

print(f"\nCalculation:")
print(f"  Expected = Opening + Purchases - Sales - Waste")
print(f"           = {opening} + {purchases} - {sales} - {waste_after}")
print(f"           = {expected_after} pints")
print(f"\n  Variance = Counted - Expected")
print(f"           = {counted} - {expected_after}")
print(f"           = {variance_after} pints")

print(f"\n📊 Result:")
print(f"  Expected: {expected_after} pints")
print(f"  Counted:  {counted} pints")
print(f"  Variance: {variance_after} pints ✅ PERFECT MATCH!")
print(f"\n  ✓ The waste explains the missing stock completely!")

# Show the impact
print("\n" + "="*80)
print("IMPACT ANALYSIS")
print("="*80)

print(f"\n{'Field':<15} {'Without Waste':<20} {'With Waste':<20} {'Change':<15}")
print("-" * 70)
print(f"{'Waste':<15} {waste_before:<20} {waste_after:<20} +{waste_after - waste_before}")
print(f"{'Expected':<15} {expected_before:<20} {expected_after:<20} {expected_after - expected_before}")
print(f"{'Counted':<15} {counted:<20} {counted:<20} {counted - counted}")
print(f"{'Variance':<15} {variance_before:<20} {variance_after:<20} {variance_after - variance_before}")

print("\n✅ KEY INSIGHTS:")
print("   1. Waste REDUCED expected qty (76 → 0)")
print("   2. Counted stayed the same (it's physical count)")
print("   3. Variance IMPROVED from -76 to 0")
print("   4. Recording waste EXPLAINED the shortage")

# Another example: Partial waste
print("\n\n" + "="*80)
print("EXAMPLE 2: Spoiled Wine Bottles")
print("="*80)

opening2 = Decimal('24')  # 2 cases
purchases2 = Decimal('12')  # 1 case
sales2 = Decimal('20')
waste2_before = Decimal('0')
waste2_after = Decimal('3')  # 3 corked bottles
counted2 = Decimal('13')

print(f"\nBEFORE Recording Waste:")
expected2_before = opening2 + purchases2 - sales2 - waste2_before
variance2_before = counted2 - expected2_before
print(f"  Expected: {opening2} + {purchases2} - {sales2} - {waste2_before} = {expected2_before}")
print(f"  Counted:  {counted2}")
print(f"  Variance: {variance2_before} bottles ⚠️ Shortage!")

print(f"\nAFTER Recording Waste (3 corked bottles):")
expected2_after = opening2 + purchases2 - sales2 - waste2_after
variance2_after = counted2 - expected2_after
print(f"  Expected: {opening2} + {purchases2} - {sales2} - {waste2_after} = {expected2_after}")
print(f"  Counted:  {counted2}")
print(f"  Variance: {variance2_after} bottles ✅ Perfect!")

# Formula demonstration
print("\n\n" + "="*80)
print("FORMULA BREAKDOWN")
print("="*80)

print("""
The relationship:

    EXPECTED QTY = Opening + Purchases - Sales - WASTE - Transfers + Adjustments
                                                    ↑
                                              Waste reduces expected!

    COUNTED QTY = (Full Units × Servings) + Partial Units
                  ↑
                  Independent of waste!

    VARIANCE = Counted - Expected
               ↑             ↑
               No change   Reduced by waste
               
    Result: Variance increases (less negative or more positive)
""")

print("\n💡 REMEMBER:")
print("   - Waste affects EXPECTED (reduces it)")
print("   - Waste does NOT affect COUNTED (that's physical count)")
print("   - Therefore, waste DOES affect VARIANCE (indirectly)")
print("   - Recording waste makes variance more accurate!")

print("\n" + "="*80)
