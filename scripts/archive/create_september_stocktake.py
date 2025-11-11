"""
Create September 2025 stocktake by scaling October 2025 data
to match target values exactly.

This script:
1. Gets October 2025 closing stock values
2. Calculates scale factors per category to match September targets
3. Creates September 2025 StockPeriod and StockSnapshots
4. Scales October values to create accurate September closing stock

PASTE YOUR EXCEL TARGET VALUES BELOW IN THE sept_targets DICTIONARY
"""
import os
import django
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
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

# Get October 2025 period
try:
    oct_period = StockPeriod.objects.get(
        period_name="October 2025",
        is_closed=True
    )
    print("✓ October 2025 period found")
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found!")
    print("   Make sure October 2025 is closed first")
    exit(1)

# =============================================================================
# SEPTEMBER 2025 TARGET VALUES FROM EXCEL (Date: 30-09-25)
# Total Stock Value: €27,440.28
# Sales Amount: €51,207.00
# =============================================================================
sept_targets = {
    'D': Decimal('5303.15'),    # Draught Beer total value
    'B': Decimal('3079.04'),    # Bottled Beer total value
    'S': Decimal('10406.35'),   # Spirits total value
    'M': Decimal('4185.61'),    # Minerals/Syrups total value
    'W': Decimal('4466.13')     # Wine total value
}
# =============================================================================

print("\nSeptember 2025 Target Values:")
print("-" * 50)
for cat_code, value in sept_targets.items():
    print(f"  {cat_code}: €{value:,.2f}")
print()

# Calculate October 2025 totals by category
oct_snapshots = StockSnapshot.objects.filter(period=oct_period)

oct_totals = {}
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    cat_snaps = oct_snapshots.filter(item__category_id=cat_code)
    
    total = Decimal('0.00')
    for snap in cat_snaps:
        # Full units value
        full_value = snap.closing_full_units * snap.unit_cost
        
        # Partial units value (different calculation for different categories)
        if cat_code in ['D', 'B', 'M']:
            # Draught, Bottled, Minerals: partial = servings
            partial_value = snap.closing_partial_units * snap.cost_per_serving
        else:  # S, W
            # Spirits, Wine: partial = fractional units
            partial_value = snap.closing_partial_units * snap.unit_cost
        
        total += full_value + partial_value
    
    oct_totals[cat_code] = total

print("October 2025 Closing Stock Values:")
print("-" * 50)
for cat_code in ['D', 'B', 'S', 'M', 'W']:
    print(f"  {cat_code}: €{oct_totals[cat_code]:,.2f}")
print()

# Calculate scale factors (how much to multiply October values)
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

# Create September 2025 period
print("Creating September 2025 period...")
sept_period, created = StockPeriod.create_monthly_period(hotel, 2025, 9)

if not created:
    print("⚠️  September 2025 period already exists!")
    response = input("Delete existing snapshots and recreate? (yes/no): ")
    if response.lower() == 'yes':
        deleted_count = StockSnapshot.objects.filter(period=sept_period).count()
        StockSnapshot.objects.filter(period=sept_period).delete()
        print(f"✓ Deleted {deleted_count} existing snapshots")
    else:
        print("❌ Cancelled")
        exit(0)
else:
    print("✓ September 2025 period created")

# Create scaled snapshots for September
print()
print("Creating September 2025 snapshots from scaled October data...")
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
    
    # Scale the October units by the category scale factor
    sept_full = (oct_snap.closing_full_units * scale).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    sept_partial = (oct_snap.closing_partial_units * scale).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    )
    
    # Calculate September value with same unit costs as October
    full_value = sept_full * oct_snap.unit_cost
    
    if cat_code in ['D', 'B', 'M']:
        partial_value = sept_partial * oct_snap.cost_per_serving
    else:  # S, W
        partial_value = sept_partial * oct_snap.unit_cost
    
    sept_value = (full_value + partial_value).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    
    # Create September snapshot
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

# Close the period and add sales amount
sept_period.is_closed = True
sept_period.closed_at = datetime.now()
sept_period.manual_sales_amount = Decimal('51207.00')
sept_period.notes = (
    "Created from October 2025 data using category scale factors. "
    "Sales: €51,207.00"
)
sept_period.save()
print("✓ September 2025 period marked as closed")
print(f"✓ Manual sales amount set: €{sept_period.manual_sales_amount:,.2f}")
print()

# Validation report
print("=" * 100)
print("VALIDATION REPORT - SEPTEMBER 2025")
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
    print("✅ SUCCESS! September 2025 stocktake matches targets (within €10)")
else:
    print(f"⚠️  Total difference: €{total_diff:.2f}")

print()
print("=" * 100)
print("SEPTEMBER 2025 SUMMARY")
print("=" * 100)
print(f"Period ID: {sept_period.id}")
print(f"Total Stock Value: €{total_calculated:,.2f}")
print(f"Manual Sales Amount: €{sept_period.manual_sales_amount:,.2f}")
print(f"Status: {'CLOSED' if sept_period.is_closed else 'OPEN'}")
print()
print("NOTE: S45 should be W45 (Wine item miscategorized as Spirits)")
print("      This will be corrected in the data import")
print()
print("=" * 100)
print("NEXT STEPS:")
print("=" * 100)
print("1. ✓ September 2025 period created and closed")
print("2. ✓ Stock snapshots created from scaled October data")
print("3. ✓ Manual sales amount set: €51,207.00")
print("4. Run comparison report: Sept → Oct to verify consumption")
print("5. If needed, add manual purchases:")
print(f"   sept_period = StockPeriod.objects.get(id={sept_period.id})")
print("   sept_period.manual_purchases_amount = Decimal('AMOUNT')")
print("   sept_period.save()")
print("=" * 100)
