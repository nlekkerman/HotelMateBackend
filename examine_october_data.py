"""
Examine October 2024 stocktake data to understand:
1. How units are stored (full vs partial)
2. Value calculations
3. Unit types per category
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from decimal import Decimal

print("=" * 100)
print("EXAMINING OCTOBER 2024 STOCKTAKE DATA")
print("=" * 100)
print()

# Get October period
try:
    oct_period = StockPeriod.objects.get(
        period_name="October 2024",
        is_closed=True
    )
    print(f"✓ Found October 2024 period")
    print(f"  Period: {oct_period.start_date} to {oct_period.end_date}")
    print(f"  Closed: {oct_period.is_closed}")
    print()
except StockPeriod.DoesNotExist:
    print("✗ October 2024 period not found!")
    exit(1)

# Get all snapshots
snapshots = StockSnapshot.objects.filter(period=oct_period).select_related('item', 'item__category')
print(f"Total snapshots: {snapshots.count()}")
print()

# Analyze by category
print("=" * 100)
print("CATEGORY ANALYSIS")
print("=" * 100)
print()

categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

category_totals = {}

for cat_code, cat_name in categories.items():
    print(f"\n{'=' * 100}")
    print(f"{cat_code} - {cat_name}")
    print('=' * 100)
    
    cat_snapshots = snapshots.filter(item__category_id=cat_code).order_by('item__sku')
    
    if cat_snapshots.count() == 0:
        print("No items in this category")
        continue
    
    total_value = Decimal('0.00')
    
    print(f"\n{'SKU':<15} {'Name':<40} {'Full':<10} {'Partial':<12} {'Value':<12}")
    print("-" * 100)
    
    for snap in cat_snapshots[:10]:  # Show first 10 items
        item = snap.item
        
        # Calculate value using snapshot's stored cost
        full_value = snap.closing_full_units * snap.unit_cost
        
        # Partial value depends on category
        if cat_code in ['D', 'B', 'M']:
            # Partial units are servings (pints, bottles)
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        elif cat_code in ['S', 'W']:
            # Partial units are percentage of bottle
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        item_value = full_value + partial_value
        total_value += item_value
        
        print(f"{item.sku:<15} {item.name[:38]:<40} {snap.closing_full_units:<10.2f} {snap.closing_partial_units:<12.4f} €{item_value:<11.2f}")
    
    if cat_snapshots.count() > 10:
        print(f"... and {cat_snapshots.count() - 10} more items")
    
    # Calculate total for category
    for snap in cat_snapshots:
        if snap.item.sku in [s.item.sku for s in cat_snapshots[:10]]:
            continue  # Already counted
        
        full_value = snap.closing_full_units * snap.unit_cost
        
        if cat_code in ['D', 'B', 'M']:
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        elif cat_code in ['S', 'W']:
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        total_value += full_value + partial_value
    
    category_totals[cat_code] = total_value
    
    print("-" * 100)
    print(f"{'TOTAL':<55} {'':>10} {'':>12} €{total_value:>11.2f}")
    print()

# Summary
print("\n" + "=" * 100)
print("OCTOBER 2024 CLOSING STOCK SUMMARY")
print("=" * 100)
print()

for cat_code, cat_name in categories.items():
    if cat_code in category_totals:
        print(f"{cat_name:<30} €{category_totals[cat_code]:>12.2f}")

grand_total = sum(category_totals.values())
print("-" * 45)
print(f"{'TOTAL':<30} €{grand_total:>12.2f}")

print("\n" + "=" * 100)
print("SEPTEMBER TARGET VALUES")
print("=" * 100)
print()

sept_targets = {
    'D': Decimal('5303.15'),
    'B': Decimal('3079.04'),
    'S': Decimal('10406.35'),
    'M': Decimal('4185.61'),
    'W': Decimal('4466.13')
}

print(f"{'Category':<30} {'October':<15} {'September':<15} {'Difference':<15} {'Scale Factor':<15}")
print("-" * 100)

for cat_code, cat_name in categories.items():
    oct_val = category_totals.get(cat_code, Decimal('0.00'))
    sept_val = sept_targets.get(cat_code, Decimal('0.00'))
    diff = oct_val - sept_val
    
    if oct_val > 0:
        scale = sept_val / oct_val
    else:
        scale = Decimal('0.00')
    
    print(f"{cat_name:<30} €{oct_val:>13.2f} €{sept_val:>13.2f} €{diff:>13.2f} {scale:>14.6f}")

sept_total = sum(sept_targets.values())
print("-" * 100)
print(f"{'TOTAL':<30} €{grand_total:>13.2f} €{sept_total:>13.2f}")

print("\n" + "=" * 100)
print("KEY FINDINGS FOR SEPTEMBER CALCULATION")
print("=" * 100)
print()
print("1. UNIT STORAGE:")
print("   • Draught (D): full_units = KEGS, partial_units = PINTS")
print("   • Bottled (B): full_units = CASES, partial_units = LOOSE BOTTLES")
print("   • Spirits (S): full_units = BOTTLES, partial_units = DECIMAL (0.50 = 50%)")
print("   • Wine (W): full_units = BOTTLES, partial_units = DECIMAL (0.25 = 25%)")
print("   • Minerals (M): full_units = varies, partial_units = varies")
print()
print("2. VALUE CALCULATION:")
print("   • Full units value = full_units × unit_cost")
print("   • Partial value (D/B/M) = partial_units × cost_per_serving")
print("   • Partial value (S/W) = partial_units × unit_cost")
print()
print("3. SEPTEMBER CREATION STRATEGY:")
print("   • Scale each item's full AND partial units by category scale factor")
print("   • Preserve the SAME ratio of full:partial for each item")
print("   • This ensures realistic stock distributions")
print()
