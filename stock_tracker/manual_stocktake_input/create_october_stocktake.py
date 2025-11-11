"""
Create October 2025 stocktake using September's closing stock as opening.

This script:
1. Creates October 2025 StockPeriod
2. Creates October 2025 Stocktake
3. Creates StocktakeLines with opening_qty from September snapshots
4. Creates closing StockSnapshots for October (to become November opening)
"""
import os
import django
from datetime import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, Stocktake,
    StocktakeLine, StockItem
)
from hotel.models import Hotel

print("=" * 100)
print("CREATING OCTOBER 2025 STOCKTAKE")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name} (ID: {hotel.id})")
print()

# ============================================================================
# STEP 1: Get September period and snapshots
# ============================================================================
print("STEP 1: Loading September 2025 data...")
print("-" * 100)

try:
    sept_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2025,
        month=9,
        period_type='MONTHLY'
    )
    print(f"✓ September 2025 period found (ID: {sept_period.id})")
    print(f"  Dates: {sept_period.start_date} to {sept_period.end_date}")
    print(f"  Closed: {sept_period.is_closed}")
except StockPeriod.DoesNotExist:
    print("❌ September 2025 period not found!")
    print("   Please create September period first.")
    exit(1)

# Get September snapshots (these become October opening)
sept_snapshots = StockSnapshot.objects.filter(
    period=sept_period
).select_related('item', 'item__category')

print(f"✓ Found {sept_snapshots.count()} September snapshots")
print()

# Calculate September totals by category
categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals/Syrups'
}

sept_totals = {}
for cat_code in categories.keys():
    cat_snaps = sept_snapshots.filter(item__category_id=cat_code)
    total = sum(snap.closing_stock_value for snap in cat_snaps)
    sept_totals[cat_code] = total
    print(f"  {cat_code} - {categories[cat_code]:<25} "
          f"€{total:>12.2f}")

sept_grand_total = sum(sept_totals.values())
print(f"  {'TOTAL':<30} €{sept_grand_total:>12.2f}")
print()

# ============================================================================
# STEP 2: Create October 2025 StockPeriod
# ============================================================================
print("STEP 2: Creating October 2025 period...")
print("-" * 100)

oct_period, created = StockPeriod.create_monthly_period(hotel, 2025, 10)

if not created:
    print("⚠️  October 2025 period already exists!")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    
    # Delete existing data
    StockSnapshot.objects.filter(period=oct_period).delete()
    Stocktake.objects.filter(
        hotel=hotel,
        period_start=oct_period.start_date,
        period_end=oct_period.end_date
    ).delete()
    print("✓ Deleted existing October data")

print(f"✓ October 2025 period ready (ID: {oct_period.id})")
print(f"  Dates: {oct_period.start_date} to {oct_period.end_date}")
print()

# ============================================================================
# STEP 3: Create October 2025 Stocktake
# ============================================================================
print("STEP 3: Creating October 2025 stocktake...")
print("-" * 100)

oct_stocktake = Stocktake.objects.create(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date,
    status='DRAFT',
    notes='Created from September closing stock'
)

print(f"✓ Stocktake created (ID: {oct_stocktake.id})")
print(f"  Status: {oct_stocktake.status}")
print()

# ============================================================================
# STEP 4: Create StocktakeLines with September closing as opening
# ============================================================================
print("STEP 4: Creating stocktake lines...")
print("-" * 100)

lines_created = 0
opening_totals = {}

for cat_code in categories.keys():
    opening_totals[cat_code] = Decimal('0.00')

for sept_snap in sept_snapshots:
    # September's closing stock becomes October's opening stock
    # Use total_servings property which handles all size types correctly
    opening_servings = sept_snap.total_servings
    
    # Create stocktake line
    StocktakeLine.objects.create(
        stocktake=oct_stocktake,
        item=sept_snap.item,
        # Opening = September closing (in servings)
        opening_qty=opening_servings,
        # No movements yet (will be added manually or imported later)
        purchases=Decimal('0.0000'),
        waste=Decimal('0.0000'),
        transfers_in=Decimal('0.0000'),
        transfers_out=Decimal('0.0000'),
        adjustments=Decimal('0.0000'),
        # No counted stock yet (DRAFT state)
        counted_full_units=Decimal('0.00'),
        counted_partial_units=Decimal('0.00'),
        # Use current costs from item
        valuation_cost=sept_snap.cost_per_serving
    )
    
    # Track opening values
    opening_value = opening_servings * sept_snap.cost_per_serving
    cat_code = sept_snap.item.category_id
    opening_totals[cat_code] += opening_value
    
    lines_created += 1
    
    if lines_created % 50 == 0:
        print(f"  Created {lines_created} lines...")

print(f"✓ Created {lines_created} stocktake lines")
print()

# Show opening stock by category
print("  Opening Stock (from September closing):")
print("  " + "-" * 80)
for cat_code, cat_name in categories.items():
    value = opening_totals[cat_code]
    print(f"  {cat_code} - {cat_name:<25} €{value:>12.2f}")
print("  " + "-" * 80)
grand_opening = sum(opening_totals.values())
print(f"  {'TOTAL':<30} €{grand_opening:>12.2f}")
print()

# ============================================================================
# STEP 5: Create October closing snapshots (same as opening for now)
# ============================================================================
print("STEP 5: Creating October closing snapshots...")
print("-" * 100)

snapshots_created = 0
closing_totals = {}

for cat_code in categories.keys():
    closing_totals[cat_code] = Decimal('0.00')

for sept_snap in sept_snapshots:
    # For now, October closing = October opening (no changes)
    # These will be updated when stocktake is counted
    
    StockSnapshot.objects.create(
        hotel=hotel,
        item=sept_snap.item,
        period=oct_period,
        # Copy September closing as October closing (placeholder)
        closing_full_units=sept_snap.closing_full_units,
        closing_partial_units=sept_snap.closing_partial_units,
        unit_cost=sept_snap.unit_cost,
        cost_per_serving=sept_snap.cost_per_serving,
        closing_stock_value=sept_snap.closing_stock_value,
        menu_price=sept_snap.menu_price
    )
    
    cat_code = sept_snap.item.category_id
    closing_totals[cat_code] += sept_snap.closing_stock_value
    
    snapshots_created += 1
    
    if snapshots_created % 50 == 0:
        print(f"  Created {snapshots_created} snapshots...")

print(f"✓ Created {snapshots_created} snapshots")
print()

# Show closing stock by category
print("  Closing Stock (placeholder - same as opening):")
print("  " + "-" * 80)
for cat_code, cat_name in categories.items():
    value = closing_totals[cat_code]
    print(f"  {cat_code} - {cat_name:<25} €{value:>12.2f}")
print("  " + "-" * 80)
grand_closing = sum(closing_totals.values())
print(f"  {'TOTAL':<30} €{grand_closing:>12.2f}")
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 100)
print("CREATION COMPLETE")
print("=" * 100)
print()
print("Summary:")
print(f"  ✓ October 2025 Period created (ID: {oct_period.id})")
print(f"  ✓ October 2025 Stocktake created (ID: {oct_stocktake.id})")
print(f"  ✓ {lines_created} StocktakeLines created")
print(f"  ✓ {snapshots_created} StockSnapshots created")
print()
print(f"  Opening Stock Value:  €{grand_opening:.2f}")
print(f"  Closing Stock Value:  €{grand_closing:.2f}")
print()
print("Next Steps:")
print("  1. Add purchases/waste to October stocktake lines")
print("  2. Count October closing stock")
print("  3. Approve stocktake when ready")
print("  4. Test endpoint: GET /api/stock_tracker/2/stocktakes/"
      f"{oct_stocktake.id}/")
print()
print("=" * 100)
