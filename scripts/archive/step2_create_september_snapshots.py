"""
Step 2: Create September 2025 StockSnapshots
Scale from October 2025 data to match September targets
"""
import os
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 80)
print("STEP 2: CREATE SEPTEMBER 2025 STOCK SNAPSHOTS")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel,
    period_name="September 2025"
)
print(f"✓ September Period found (ID: {sept_period.id})")

# Get October period for scaling
oct_period = StockPeriod.objects.get(
    hotel=hotel,
    period_name="October 2025"
)
print(f"✓ October Period found (ID: {oct_period.id})")
print()

# September target values from Excel
sept_targets = {
    'D': Decimal('5303.15'),
    'B': Decimal('3079.04'),
    'S': Decimal('10406.35'),
    'M': Decimal('4185.61'),
    'W': Decimal('4466.13')
}

print("September Targets:")
for cat, value in sept_targets.items():
    print(f"  {cat}: €{value:,.2f}")
print()

# Calculate October totals
oct_snapshots = StockSnapshot.objects.filter(period=oct_period)
print(f"October snapshots: {oct_snapshots.count()}")

oct_totals = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    cat_snaps = oct_snapshots.filter(item__category_id=cat_code)
    total = Decimal('0.00')
    
    for snap in cat_snaps:
        full_value = snap.closing_full_units * snap.unit_cost
        
        if cat_code in ['D', 'B', 'M']:
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        total += full_value + partial_value
    
    oct_totals[cat_code] = total

print()
print("October Totals:")
for cat, value in oct_totals.items():
    print(f"  {cat}: €{value:,.2f}")
print()

# Calculate scale factors
scale_factors = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    if oct_totals[cat_code] > 0:
        scale_factors[cat_code] = sept_targets[cat_code] / oct_totals[cat_code]
    else:
        scale_factors[cat_code] = Decimal('1.0')

print("Scale Factors (Sept/Oct):")
for cat, factor in scale_factors.items():
    print(f"  {cat}: {factor:.6f}")
print()

# Check for existing snapshots
existing = StockSnapshot.objects.filter(period=sept_period).count()
if existing > 0:
    print(f"⚠️  Found {existing} existing snapshots")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    StockSnapshot.objects.filter(period=sept_period).delete()
    print("✓ Deleted existing snapshots")
    print()

# Create September snapshots
print("Creating September snapshots...")
print("-" * 80)

created_count = 0
sept_totals = {
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
    else:
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
    
    sept_totals[cat_code] += sept_value
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count} snapshots...")

print(f"✓ Created {created_count} total snapshots")
print()

# Validation
print("=" * 80)
print("VALIDATION")
print("=" * 80)
print()
print(f"{'Category':<15} {'Target':<15} {'Created':<15} {'Diff':<15} {'Match %'}")
print("-" * 80)

total_target = Decimal('0.00')
total_created = Decimal('0.00')

for cat_code in ['D', 'B', 'S', 'M', 'W']:
    target = sept_targets[cat_code]
    created = sept_totals[cat_code]
    diff = created - target
    match_pct = (created / target * 100) if target > 0 else Decimal('0.00')
    
    total_target += target
    total_created += created
    
    status = "✓" if abs(diff) < 5 else "⚠️"
    print(f"{status} {cat_code:<13} €{target:>13.2f} €{created:>13.2f} "
          f"€{diff:>13.2f} {match_pct:>13.2f}%")

print("-" * 80)
total_diff = total_created - total_target
total_match = (total_created / total_target * 100) if total_target > 0 else Decimal('0.00')
print(f"{'TOTAL':<15} €{total_target:>13.2f} €{total_created:>13.2f} "
      f"€{total_diff:>13.2f} {total_match:>13.2f}%")
print()

if abs(total_diff) < 10:
    print("✅ SUCCESS! Snapshots match targets")
else:
    print(f"⚠️  Difference: €{total_diff:.2f}")

print()
print("=" * 80)
print("✅ STEP 2 COMPLETE - Snapshots created")
print("=" * 80)
print()
print("NEXT: Run script to create Stocktake")
