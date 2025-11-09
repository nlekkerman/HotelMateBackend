"""
REAL SCENARIO: 5 Cases + 9 Bottles, Break 5 Bottles

This shows exactly how breaking 5 bottles affects variance.
"""

from decimal import Decimal

print("="*80)
print("YOUR SCENARIO: Cronin's 0.0% - Breaking Bottles")
print("="*80)

# Setup
bottles_per_case = 12
opening_cases = 5
opening_loose = 9
total_opening = (opening_cases * bottles_per_case) + opening_loose

print(f"\n📦 INITIAL STOCK:")
print(f"   {opening_cases} cases × {bottles_per_case} bottles = {opening_cases * bottles_per_case} bottles")
print(f"   + {opening_loose} loose bottles")
print(f"   ────────────────────────")
print(f"   Total Opening: {total_opening} bottles")

# Movements
purchases = Decimal('0')
sales = Decimal('0')
broken_bottles = Decimal('5')

print(f"\n💥 INCIDENT: 5 bottles broken!")

# Physical count after breaking bottles
# Originally had 69 bottles, broke 5, should have 64
actual_physical_stock = total_opening - int(broken_bottles)
counted_full = 5  # Still have 5 full cases
counted_partial = 4  # Had 9 loose, broke 5, left with 4

print(f"\n🔍 PHYSICAL COUNT (What you actually see on shelf):")
print(f"   {counted_full} cases × {bottles_per_case} = {counted_full * bottles_per_case} bottles")
print(f"   + {counted_partial} loose bottles")
print(f"   ────────────────────────")
print(f"   Total Counted: {(counted_full * bottles_per_case) + counted_partial} bottles")

# SCENARIO 1: WITHOUT recording waste
print("\n" + "="*80)
print("SCENARIO 1: Forget to Record the Waste")
print("="*80)

waste_not_recorded = Decimal('0')
expected_without_waste = total_opening + purchases - sales - waste_not_recorded
counted = (counted_full * bottles_per_case) + counted_partial
variance_without_waste = counted - expected_without_waste

print(f"\n📊 Calculations:")
print(f"   Expected = Opening + Purchases - Sales - Waste")
print(f"            = {total_opening} + {purchases} - {sales} - {waste_not_recorded}")
print(f"            = {expected_without_waste} bottles")
print(f"\n   Counted = Physical count on shelf")
print(f"           = {counted} bottles")
print(f"\n   Variance = Counted - Expected")
print(f"            = {counted} - {expected_without_waste}")
print(f"            = {variance_without_waste} bottles")

print(f"\n❌ RESULT:")
print(f"   Expected: {expected_without_waste} bottles")
print(f"   Counted:  {counted} bottles")
print(f"   Variance: {variance_without_waste} bottles ⚠️ SHORTAGE!")
print(f"\n   Problem: System thinks you're missing {abs(variance_without_waste)} bottles!")
print(f"   Reality: You broke them, they're not missing/stolen!")

# SCENARIO 2: WITH recording waste
print("\n" + "="*80)
print("SCENARIO 2: Properly Record the Waste")
print("="*80)

waste_recorded = broken_bottles  # 5 bottles
expected_with_waste = total_opening + purchases - sales - waste_recorded
variance_with_waste = counted - expected_with_waste

print(f"\n📝 Added Movement:")
print(f"   Type: WASTE")
print(f"   Quantity: {waste_recorded} bottles")
print(f"   Notes: 'Dropped tray, 5 bottles broke'")

print(f"\n📊 Calculations:")
print(f"   Expected = Opening + Purchases - Sales - Waste")
print(f"            = {total_opening} + {purchases} - {sales} - {waste_recorded}")
print(f"            = {expected_with_waste} bottles")
print(f"\n   Counted = Physical count on shelf")
print(f"           = {counted} bottles")
print(f"\n   Variance = Counted - Expected")
print(f"            = {counted} - {expected_with_waste}")
print(f"            = {variance_with_waste} bottles")

print(f"\n✅ RESULT:")
print(f"   Expected: {expected_with_waste} bottles")
print(f"   Counted:  {counted} bottles")
print(f"   Variance: {variance_with_waste} bottles ✓ PERFECT!")
print(f"\n   Success: Waste explains the difference completely!")

# Comparison
print("\n" + "="*80)
print("COMPARISON TABLE")
print("="*80)

print(f"\n{'Field':<20} {'Without Waste':<20} {'With Waste':<20}")
print("-" * 60)
print(f"{'Opening':<20} {total_opening:<20} {total_opening:<20}")
print(f"{'Purchases':<20} {purchases:<20} {purchases:<20}")
print(f"{'Sales':<20} {sales:<20} {sales:<20}")
print(f"{'Waste':<20} {waste_not_recorded:<20} {waste_recorded:<20} ← CHANGED!")
print(f"{'':<20} {'':<20} {'':<20}")
print(f"{'Expected':<20} {expected_without_waste:<20} {expected_with_waste:<20} ← REDUCED!")
print(f"{'Counted':<20} {counted:<20} {counted:<20} (same)")
print(f"{'Variance':<20} {variance_without_waste:<20} {variance_with_waste:<20} ← FIXED!")

# Visual representation
print("\n" + "="*80)
print("VISUAL BREAKDOWN")
print("="*80)

print("""
WHAT YOU HAD:
┌──────────────────────────────────────┐
│ 5 full cases (60 bottles)            │
│ + 9 loose bottles                    │
│ = 69 total bottles                   │
└──────────────────────────────────────┘

WHAT HAPPENED:
┌──────────────────────────────────────┐
│ 💥 5 bottles broke!                  │
└──────────────────────────────────────┘

WHAT YOU HAVE NOW:
┌──────────────────────────────────────┐
│ 5 full cases (60 bottles) ✓          │
│ + 4 loose bottles ✓                  │
│ = 64 total bottles                   │
└──────────────────────────────────────┘
""")

print("\nWITHOUT Recording Waste:")
print("   Expected: 69 bottles (system doesn't know about breakage)")
print("   Counted:  64 bottles (physical reality)")
print("   ❌ Variance: -5 bottles (looks like theft!)")

print("\nWITH Recording Waste:")
print("   Expected: 64 bottles (system accounts for breakage)")
print("   Counted:  64 bottles (physical reality)")
print("   ✅ Variance: 0 bottles (perfect match!)")

# Summary
print("\n" + "="*80)
print("YES - WASTE ABSOLUTELY AFFECTS VARIANCE!")
print("="*80)

print("""
HOW IT WORKS:

1. EXPECTED qty = Opening + Purchases - Sales - WASTE
   └─ Waste REDUCES expected
   └─ 69 bottles expected becomes 64 bottles expected

2. COUNTED qty = Physical count (what's on shelf)
   └─ You count 64 bottles
   └─ Waste does NOT change this (it's reality)

3. VARIANCE = Counted - Expected
   └─ Without waste: 64 - 69 = -5 (shortage!)
   └─ With waste: 64 - 64 = 0 (perfect!)

BOTTOM LINE:
Recording waste adjusts the EXPECTED quantity to match reality,
which fixes the VARIANCE to reflect truth instead of showing
false shortages.
""")

print("\n💡 FOR YOUR FRONTEND:")
print("""
When staff breaks bottles, they should:
1. Click "Add Waste" button
2. Enter quantity: 5
3. Add note: "Dropped tray, 5 bottles broke"
4. Submit

Result:
- Waste movement created in database
- Expected qty automatically reduces by 5
- Variance updates to show correct stock level
- Audit trail created (who, when, why)
""")

print("="*80)
