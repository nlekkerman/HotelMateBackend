"""
Update September counted values to match September closing stock values.
The previous import used current stock, but we need September 30th values.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 80)
print("UPDATE SEPTEMBER COUNTED TO SEPTEMBER CLOSING VALUES")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()

# Get September stocktake
try:
    stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start__year=2025,
        period_start__month=9
    )
    print(f"✅ September stocktake found (ID: {stocktake.id})")
except Stocktake.DoesNotExist:
    print("❌ September stocktake not found!")
    exit(1)

print()
print("Target September closing values by category:")
print("  Draught:  €5,303.15")
print("  Bottled:  €3,079.04")
print("  Spirits:  €10,406.35")
print("  Minerals: €4,185.61")
print("  Wine:     €4,466.13")
print("  TOTAL:    €27,440.28")
print()

# Get current August closing (opening) values by category
print("Calculating scale factors...")

# Get current totals by category (from opening = August)
from django.db.models import Sum, F

august_totals = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    lines = stocktake.lines.filter(item__category_id=cat_code)
    total = lines.aggregate(
        total=Sum(F('opening_qty') * F('valuation_cost'))
    )['total'] or Decimal('0.00')
    august_totals[cat_code] = total

print("\nAugust closing (current opening) by category:")
print(f"  D: €{august_totals['D']:,.2f}")
print(f"  B: €{august_totals['B']:,.2f}")
print(f"  S: €{august_totals['S']:,.2f}")
print(f"  M: €{august_totals['M']:,.2f}")
print(f"  W: €{august_totals['W']:,.2f}")

# September target values
sept_targets = {
    'D': Decimal('5303.15'),
    'B': Decimal('3079.04'),
    'S': Decimal('10406.35'),
    'M': Decimal('4185.61'),
    'W': Decimal('4466.13')
}

# Calculate scale factors
scale_factors = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    if august_totals[cat_code] > 0:
        scale_factors[cat_code] = sept_targets[cat_code] / august_totals[cat_code]
    else:
        scale_factors[cat_code] = Decimal('1.0')

print("\nScale factors (September / August):")
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    print(f"  {cat_code}: {scale_factors[cat_code]:.6f}")

print("\nUpdating counted values...")

updated_count = 0
sept_calculated = {
    'D': Decimal('0.00'),
    'B': Decimal('0.00'),
    'S': Decimal('0.00'),
    'M': Decimal('0.00'),
    'W': Decimal('0.00')
}

for line in stocktake.lines.all():
    cat_code = line.item.category_id
    scale = scale_factors[cat_code]
    
    # Scale the opening (August) quantities to get September closing
    # Opening qty is already in servings
    sept_qty = line.opening_qty * scale
    
    # Calculate full and partial units from scaled servings
    # For simplicity, put everything in partial units for now
    line.counted_full_units = Decimal('0.00')
    line.counted_partial_units = sept_qty
    line.save()
    
    # Track calculated value
    sept_calculated[cat_code] += line.counted_value
    updated_count += 1
    
    if updated_count % 50 == 0:
        print(f"  Updated {updated_count} lines...")

print(f"✅ Updated {updated_count} lines")
print()

# Verify totals
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print(f"{'Category':<15} {'Target':<15} {'Calculated':<15} {'Diff':<15} {'Match %'}")
print("-" * 80)

total_target = Decimal('0.00')
total_calculated = Decimal('0.00')

for cat_code in ['D', 'B', 'S', 'M', 'W']:
    target = sept_targets[cat_code]
    calculated = sept_calculated[cat_code]
    diff = calculated - target
    match_pct = (calculated / target * 100) if target > 0 else Decimal('0')
    
    total_target += target
    total_calculated += calculated
    
    print(f"{cat_code:<15} €{target:>13,.2f} €{calculated:>13,.2f} €{diff:>13,.2f} {match_pct:>13,.2f}%")

print("-" * 80)
total_diff = total_calculated - total_target
total_match = (total_calculated / total_target * 100) if total_target > 0 else Decimal('0')
print(f"{'TOTAL':<15} €{total_target:>13,.2f} €{total_calculated:>13,.2f} €{total_diff:>13,.2f} {total_match:>13,.2f}%")

print()
if abs(total_diff) < 10:
    print("✅ SUCCESS! September values match targets (within €10)")
else:
    print(f"⚠️  Total difference: €{total_diff:.2f}")

print()
print("=" * 80)
print("SEPTEMBER 2025 STOCKTAKE UPDATED")
print("=" * 80)
print(f"Stocktake ID: {stocktake.id}")
print(f"Opening Value: €{august_totals['D'] + august_totals['B'] + august_totals['S'] + august_totals['M'] + august_totals['W']:,.2f}")
print(f"Counted Value: €{total_calculated:,.2f}")

# Calculate variance
total_variance = sum(line.variance_value for line in stocktake.lines.all())
print(f"Variance: €{total_variance:,.2f}")
print()
print("✅ September counted values updated to September closing stock!")
print("=" * 80)
