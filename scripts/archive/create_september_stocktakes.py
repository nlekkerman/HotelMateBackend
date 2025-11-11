"""
Create September 2025 stocktake by scaling October data
to match target values exactly.
"""
import os
import django
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel

print("=" * 100)
print("CREATING SEPTEMBER 2025 STOCKTAKE")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Get October period
try:
    oct_period = StockPeriod.objects.get(
        period_name="October 2025",
        is_closed=True
    )
    print(f"✓ October 2025 period found")
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found!")
    exit(1)

# September target values
sept_targets = {
    'D': Decimal('5303.15'),
    'B': Decimal('3079.04'),
    'S': Decimal('10406.35'),
    'M': Decimal('4185.61'),
    'W': Decimal('4466.13')
}

# Calculate October totals and scale factors
oct_snapshots = StockSnapshot.objects.filter(period=oct_period)

oct_totals = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    cat_snaps = oct_snapshots.filter(item__category_id=cat_code)
    
    total = Decimal('0.00')
    for snap in cat_snaps:
        full_value = snap.closing_full_units * snap.unit_cost
        
        if cat_code in ['D', 'B', 'M']:
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:  # S, W
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        total += full_value + partial_value
    
    oct_totals[cat_code] = total

# Calculate scale factors
scale_factors = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    if oct_totals[cat_code] > 0:
        scale_factors[cat_code] = sept_targets[cat_code] / oct_totals[cat_code]
    else:
        scale_factors[cat_code] = Decimal('1.0')

print("Scale factors:")
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    print(f"  {cat_code}: {scale_factors[cat_code]:.6f}")
print()

# Create September period
print("Creating September 2025 period...")
sept_period, created = StockPeriod.create_monthly_period(hotel, 2025, 9)

if not created:
    print("⚠️  September 2025 period already exists!")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() == 'yes':
        StockSnapshot.objects.filter(period=sept_period).delete()
        print("✓ Deleted existing snapshots")
    else:
        print("❌ Cancelled")
        exit(0)
else:
    print("✓ September 2025 period created")

# Create snapshots
print()
print("Creating September snapshots...")
print("-" * 100)

created_count = 0
sept_calculated_totals = {
    'D': Decimal('0.00'),
    'B': Decimal('0.00'),
    'S': Decimal('0.00'),
    'M': Decimal('0.00'),
    'W': Decimal('0.00')
}

for oct_snap in oct_snapshots:
    cat_code = oct_snap.item.category_id
    scale = scale_factors[cat_code]
    
    # Scale units
    sept_full = (oct_snap.closing_full_units * scale).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    sept_partial = (oct_snap.closing_partial_units * scale).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    )
    
    # Calculate value
    full_value = sept_full * oct_snap.unit_cost
    if cat_code in ['D', 'B', 'M']:
        partial_value = sept_partial * oct_snap.cost_per_serving
    else:  # S, W
        partial_value = sept_partial * oct_snap.unit_cost
    
    sept_value = (full_value + partial_value).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    # Create snapshot
    StockSnapshot.objects.create(
        hotel=hotel,
        item=oct_snap.item,
        period=sept_period,
        closing_full_units=sept_full,
        closing_partial_units=sept_partial,
        unit_cost=oct_snap.unit_cost,
        cost_per_serving=oct_snap.cost_per_serving,
        closing_stock_value=sept_value,
        menu_price=oct_snap.menu_price
    )
    
    sept_calculated_totals[cat_code] += sept_value
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count} snapshots...")

print(f"✓ Created {created_count} snapshots")
print()

# Close the period
sept_period.is_closed = True
sept_period.closed_at = datetime.now()
sept_period.notes = "Created from October 2025 data using category scale factors"
sept_period.save()
print("✓ September period marked as closed")
print()

# Validation report
print("=" * 100)
print("VALIDATION REPORT")
print("=" * 100)
print()

categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

print(f"{'Category':<30} {'Target':<15} {'Calculated':<15} {'Difference':<15} {'% Match'}")
print("-" * 100)

total_target = Decimal('0.00')
total_calculated = Decimal('0.00')

for cat_code, cat_name in categories.items():
    target = sept_targets[cat_code]
    calculated = sept_calculated_totals[cat_code]
    diff = calculated - target
    
    if target > 0:
        match_pct = (calculated / target * 100)
    else:
        match_pct = Decimal('0.00')
    
    total_target += target
    total_calculated += calculated
    
    status = "✓" if abs(diff) < 5 else "⚠️"
    print(f"{status} {cat_name:<27} €{target:>13.2f} €{calculated:>13.2f} €{diff:>13.2f} {match_pct:>13.2f}%")

print("-" * 100)
total_diff = total_calculated - total_target
total_match = (total_calculated / total_target * 100) if total_target > 0 else Decimal('0.00')
print(f"{'TOTAL':<30} €{total_target:>13.2f} €{total_calculated:>13.2f} €{total_diff:>13.2f} {total_match:>13.2f}%")

print()
if abs(total_diff) < 10:
    print("✅ SUCCESS! September stocktake matches targets (within €10)")
else:
    print(f"⚠️  Total difference: €{total_diff:.2f}")

print()
print("=" * 100)
print("NEXT STEPS:")
print("=" * 100)
print("1. Verify September totals match expected values")
print("2. Run sales calculation script to compare Sept → Oct")
print("3. Calculate expected revenue based on consumption")
print("=" * 100)
