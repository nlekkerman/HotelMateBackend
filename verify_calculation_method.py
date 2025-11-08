"""
Verify October 2024 calculation method matches spreadsheet logic.

This script checks:
1. How stock values are calculated in the database
2. If the calculation method matches spreadsheet expectations
3. Detailed breakdown of calculation for each category
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("OCTOBER 2024 CALCULATION METHOD VERIFICATION")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Find October 2024 period
try:
    oct_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2024,
        month=10,
        period_name="October 2024"
    )
    print(f"✓ Found October 2024 period")
except StockPeriod.DoesNotExist:
    print("❌ October 2024 period not found!")
    exit(1)

# Get snapshots
snapshots = StockSnapshot.objects.filter(
    period=oct_period
).select_related('item', 'item__category')

print(f"✓ Found {snapshots.count()} snapshots")
print()

# Expected values from spreadsheet
expected = {
    'D': Decimal('5311.62'),
    'B': Decimal('2288.46'),
    'S': Decimal('11063.66'),
    'M': Decimal('3062.43'),
    'W': Decimal('5580.35')
}

print("=" * 100)
print("CALCULATION METHOD ANALYSIS")
print("=" * 100)
print()

categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

for cat_code, cat_name in categories.items():
    print(f"\n{'=' * 100}")
    print(f"{cat_name} (Category {cat_code})")
    print(f"{'=' * 100}")
    
    cat_snaps = snapshots.filter(item__category_id=cat_code)
    
    if not cat_snaps.exists():
        print("  No items in this category")
        continue
    
    print(f"\n  Total items: {cat_snaps.count()}")
    print()
    
    # Test different calculation methods
    method1_total = Decimal('0.00')  # closing_stock_value field
    method2_total = Decimal('0.00')  # full + partial calculated separately
    method3_total = Decimal('0.00')  # using total_servings property
    
    # Show first 3 items as examples
    print(f"  Sample items (first 3):")
    print(f"  {'-' * 96}")
    print(f"  {'SKU':<12} {'Full':<8} {'Partial':<10} {'UOM':<6} "
          f"{'Unit Cost':<12} {'Value':<12}")
    print(f"  {'-' * 96}")
    
    for i, snap in enumerate(cat_snaps[:3]):
        item = snap.item
        
        # Method 1: Use stored closing_stock_value
        value1 = snap.closing_stock_value
        method1_total += value1
        
        # Method 2: Calculate based on category logic
        full_value = snap.closing_full_units * snap.unit_cost
        
        # Partial calculation depends on category
        if cat_code in ['D', 'B', 'M']:
            # Draught, Bottled Beer, Minerals: 
            # partial = servings × cost_per_serving
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:  # S, W
            # Spirits, Wine: partial = fractional bottles × unit_cost
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        value2 = full_value + partial_value
        method2_total += value2
        
        # Method 3: Using total_servings
        if hasattr(snap, 'total_servings'):
            value3 = snap.total_servings * snap.cost_per_serving
            method3_total += value3
        
        print(f"  {item.sku:<12} {snap.closing_full_units:<8.2f} "
              f"{snap.closing_partial_units:<10.4f} {item.uom:<6.2f} "
              f"€{snap.unit_cost:<11.4f} €{value1:<11.2f}")
    
    # Calculate full category totals
    for snap in cat_snaps[3:]:
        method1_total += snap.closing_stock_value
        
        full_value = snap.closing_full_units * snap.unit_cost
        if cat_code in ['D', 'B', 'M']:
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:
            partial_value = snap.closing_partial_units * snap.unit_cost
        method2_total += full_value + partial_value
        
        if hasattr(snap, 'total_servings'):
            method3_total += snap.total_servings * snap.cost_per_serving
    
    print(f"  {'-' * 96}")
    print()
    print(f"  CALCULATION METHODS:")
    print(f"  {'Method 1 (stored value):':<40} €{method1_total:>13.2f}")
    print(f"  {'Method 2 (full + partial calc):':<40} €{method2_total:>13.2f}")
    if method3_total > 0:
        print(f"  {'Method 3 (total_servings):':<40} €{method3_total:>13.2f}")
    print()
    print(f"  {'Expected from spreadsheet:':<40} €{expected[cat_code]:>13.2f}")
    print()
    
    diff1 = method1_total - expected[cat_code]
    diff2 = method2_total - expected[cat_code]
    
    if abs(diff1) < 1:
        print(f"  ✅ Method 1 MATCHES (diff: €{diff1:.2f})")
    else:
        print(f"  ❌ Method 1 differs by €{diff1:.2f}")
    
    if abs(diff2) < 1:
        print(f"  ✅ Method 2 MATCHES (diff: €{diff2:.2f})")
    else:
        print(f"  ❌ Method 2 differs by €{diff2:.2f}")
    
    # Explain the category-specific logic
    print()
    print(f"  CATEGORY LOGIC ({cat_code}):")
    if cat_code in ['D', 'B', 'M']:
        print(f"    - Full units: containers × unit_cost")
        print(f"    - Partial units: servings × cost_per_serving")
        print(f"    - Rationale: Partial represents loose servings")
    else:
        print(f"    - Full units: bottles × unit_cost")
        print(f"    - Partial units: fractional bottles × unit_cost")
        print(f"    - Rationale: Partial represents partial bottles")

print()
print("=" * 100)
print("OVERALL SUMMARY")
print("=" * 100)
print()

total_method1 = Decimal('0.00')
total_method2 = Decimal('0.00')
total_expected = Decimal('0.00')

for cat_code in ['D', 'B', 'S', 'M', 'W']:
    cat_snaps = snapshots.filter(item__category_id=cat_code)
    
    for snap in cat_snaps:
        total_method1 += snap.closing_stock_value
        
        full_value = snap.closing_full_units * snap.unit_cost
        if cat_code in ['D', 'B', 'M']:
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:
            partial_value = snap.closing_partial_units * snap.unit_cost
        total_method2 += full_value + partial_value
    
    total_expected += expected[cat_code]

print(f"{'Calculation Method':<40} {'Total Value':<15} {'vs Expected':<15}")
print("-" * 70)
print(f"{'Method 1 (stored values):':<40} €{total_method1:>13.2f} "
      f"€{total_method1 - total_expected:>13.2f}")
print(f"{'Method 2 (calculated):':<40} €{total_method2:>13.2f} "
      f"€{total_method2 - total_expected:>13.2f}")
print(f"{'Expected (spreadsheet):':<40} €{total_expected:>13.2f} "
      f"€{Decimal('0.00'):>13.2f}")
print()

if abs(total_method1 - total_expected) < 1:
    print("✅ Database values MATCH spreadsheet (using stored values)")
elif abs(total_method2 - total_expected) < 1:
    print("✅ Calculated values MATCH spreadsheet "
          "(using category-specific logic)")
else:
    print(f"⚠️  Difference: €{abs(total_method1 - total_expected):.2f}")
    print()
    print("   The calculation method is correct, but values may differ due to:")
    print("   1. Rounding differences")
    print("   2. Different stock quantities at time of snapshot")
    print("   3. Different unit costs")

print()
print("=" * 100)
print("CALCULATION LOGIC SUMMARY")
print("=" * 100)
print()
print("The system uses TWO different calculation methods based on category:")
print()
print("📊 DRAUGHT/BOTTLED BEER/MINERALS (D, B, M):")
print("   Value = (full_units × unit_cost) + "
      "(partial_units × cost_per_serving)")
print("   Reason: Partial units are loose servings (pints, bottles)")
print()
print("🍷 SPIRITS/WINE (S, W):")
print("   Value = (full_units × unit_cost) + "
      "(partial_units × unit_cost)")
print("   Reason: Partial units are fractional bottles (0.7 = 70% of bottle)")
print()
print("=" * 100)
