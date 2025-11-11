"""
Populate September 2025 StockSnapshots from October 2025 data
with scaled values to match Excel targets.

Assumes September 2025 Period and Stocktake already exist.
"""
import os
import django
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, Stocktake, StocktakeLine
)
from hotel.models import Hotel

print("=" * 100)
print("POPULATING SEPTEMBER 2025 STOCK SNAPSHOTS")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Create or get September 2025 period
sept_period, created = StockPeriod.objects.get_or_create(
    hotel=hotel,
    period_name="September 2025",
    defaults={
        'start_date': date(2025, 9, 1),
        'end_date': date(2025, 9, 30),
        'period_type': 'MONTHLY',
        'is_closed': False,
        'notes': 'September 2025 period - Created by populate script'
    }
)

if created:
    print(f"✓ Created September 2025 period (ID: {sept_period.id})")
else:
    print(f"✓ September 2025 period found (ID: {sept_period.id})")

print(f"  Period: {sept_period.start_date} to {sept_period.end_date}")
print(f"  Status: {'CLOSED' if sept_period.is_closed else 'OPEN'}")
print()

# Get October 2025 period
try:
    oct_period = StockPeriod.objects.get(
        hotel=hotel,
        period_name="October 2025",
        is_closed=True
    )
    print(f"✓ October 2025 period found (ID: {oct_period.id})")
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found or not closed!")
    print("   Need October data to scale from")
    exit(1)

# Check existing snapshots
existing_count = StockSnapshot.objects.filter(period=sept_period).count()
if existing_count > 0:
    print(f"\n⚠️  Found {existing_count} existing September snapshots")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() == 'yes':
        StockSnapshot.objects.filter(period=sept_period).delete()
        print(f"✓ Deleted {existing_count} snapshots")
    else:
        print("❌ Cancelled")
        exit(0)

print()

# September 2025 target values from Excel (Date: 30-09-25)
sept_targets = {
    'D': Decimal('5303.15'),    # Draught Beer
    'B': Decimal('3079.04'),    # Bottled Beer
    'S': Decimal('10406.35'),   # Spirits
    'M': Decimal('4185.61'),    # Minerals/Syrups
    'W': Decimal('4466.13')     # Wine
}

print("September 2025 Target Values:")
print("-" * 50)
for cat_code, value in sept_targets.items():
    print(f"  {cat_code}: €{value:,.2f}")
print()

# Calculate October totals by category
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

print("Scale Factors (September / October):")
print("-" * 50)
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    print(f"  {cat_code}: {scale_factors[cat_code]:.6f}")
print()

# Create September snapshots
print("Creating September 2025 snapshots...")
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
    
    # Scale October units
    sept_full = (oct_snap.closing_full_units * scale).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    sept_partial = (oct_snap.closing_partial_units * scale).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    )
    
    # Calculate September value
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

print(f"✓ Created {created_count} snapshots total")
print()

# Update period with sales amount (keep OPEN, not closed)
sept_period.is_closed = False
sept_period.manual_sales_amount = Decimal('51207.00')
sept_period.notes = (
    "September 2025 snapshots created from scaled October data. "
    "Sales: €51,207.00. Period is OPEN for editing."
)
sept_period.save()
print("✓ September 2025 period kept OPEN (not closed)")
print(f"✓ Manual sales amount: €{sept_period.manual_sales_amount:,.2f}")
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

header = f"{'Category':<30} {'Target':<15} {'Calculated':<15}"
header += f" {'Difference':<15} {'% Match'}"
print(header)
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
    line = f"{status} {cat_name:<27} €{target:>13.2f} €{calculated:>13.2f}"
    line += f" €{diff:>13.2f} {match_pct:>13.2f}%"
    print(line)

print("-" * 100)
total_diff = total_calculated - total_target
if total_target > 0:
    total_match = (total_calculated / total_target * 100)
else:
    total_match = Decimal('0.00')

total_line = f"{'TOTAL':<30} €{total_target:>13.2f} €{total_calculated:>13.2f}"
total_line += f" €{total_diff:>13.2f} {total_match:>13.2f}%"
print(total_line)

print()
if abs(total_diff) < 10:
    print("✅ SUCCESS! September snapshots match targets (within €10)")
else:
    print(f"⚠️  Total difference: €{total_diff:.2f}")

print()
print("=" * 100)
print("CREATING STOCKTAKE")
print("=" * 100)

# Create or get September stocktake (DRAFT status)
stocktake, st_created = Stocktake.objects.get_or_create(
    hotel=hotel,
    period_start=sept_period.start_date,
    period_end=sept_period.end_date,
    defaults={
        'status': 'DRAFT',  # Keep as DRAFT for frontend approval
        'notes': 'September 2025 stocktake - Ready for approval from frontend'
    }
)

if st_created:
    print(f"✓ Created new stocktake: {stocktake.id}")
else:
    print(f"✓ Found existing stocktake: {stocktake.id}")
    # Ensure it's DRAFT status
    if stocktake.status != 'DRAFT':
        stocktake.status = 'DRAFT'
        stocktake.save()
        print("  ↳ Changed status to DRAFT")

# Create stocktake lines from snapshots (opening stock)
lines_created = 0
lines_updated = 0

for snapshot in StockSnapshot.objects.filter(period=sept_period):
    item = snapshot.item
    
    # Calculate opening stock from closing stock
    opening_qty = snapshot.closing_full_units + snapshot.closing_partial_units
    
    # Get valuation cost
    valuation_cost = item.unit_cost or Decimal('0.00')
    
    line, line_created = StocktakeLine.objects.update_or_create(
        stocktake=stocktake,
        item=item,
        defaults={
            'opening_qty': opening_qty,
            'counted_full_units': Decimal('0'),  # Empty for user to fill
            'counted_partial_units': Decimal('0'),  # Empty for user to fill
            'valuation_cost': valuation_cost,
        }
    )
    
    if line_created:
        lines_created += 1
    else:
        lines_updated += 1

print(f"✓ Stocktake lines created: {lines_created}")
if lines_updated > 0:
    print(f"✓ Stocktake lines updated: {lines_updated}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Period ID: {sept_period.id}")
print(f"Stock Snapshots: {created_count}")
print(f"Total Stock Value: €{total_calculated:,.2f}")
print(f"Manual Sales: €{sept_period.manual_sales_amount:,.2f}")
print(f"Stocktake ID: {stocktake.id}")
print(f"Stocktake Status: {stocktake.status}")
print(f"Stocktake Lines: {lines_created + lines_updated}")
print()
print("✅ September 2025 stock snapshots and stocktake created successfully!")
print("💡 Stocktake is in DRAFT status - ready to close from frontend UI")
print("=" * 100)
