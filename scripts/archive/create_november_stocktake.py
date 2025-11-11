"""
Create November 2025 stocktake with counted values so it can be closed.
Following the same pattern as October 2025 stocktake creation.
"""
import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    StockPeriod, StockSnapshot, Stocktake, StocktakeLine, StockItem
)
from hotel.models import Hotel
from django.utils import timezone
from django.db import transaction

print("=" * 80)
print("CREATE NOVEMBER 2025 STOCKTAKE")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}")
print()

# Get October 2025 period (for reference)
try:
    oct_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2025,
        month=10,
        is_closed=True
    )
    print(f"✅ October 2025 period found (ID: {oct_period.id})")
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found!")
    exit(1)

# Get October snapshots
oct_snapshots = StockSnapshot.objects.filter(period=oct_period)
print(f"📸 October snapshots: {oct_snapshots.count()}")
oct_value = sum(s.closing_stock_value for s in oct_snapshots)
print(f"💰 October total value: €{oct_value:,.2f}")
print()

# Create November 2025 period
print("📅 Creating November 2025 period...")
nov_period, created = StockPeriod.objects.get_or_create(
    hotel=hotel,
    period_type='MONTHLY',
    year=2025,
    month=11,
    defaults={
        'is_closed': False,
        'start_date': date(2025, 11, 1),
        'end_date': date(2025, 11, 30),
        'period_name': 'November 2025'
    }
)

if created:
    print(f"✅ Created November 2025 period (ID: {nov_period.id})")
else:
    print(f"✓ November 2025 period exists (ID: {nov_period.id})")
print()

# Delete existing November snapshots if any
deleted_snaps = StockSnapshot.objects.filter(
    hotel=hotel,
    period=nov_period
).delete()[0]

if deleted_snaps > 0:
    print(f"🗑️  Deleted {deleted_snaps} old snapshots")

# Get all active stock items
items = StockItem.objects.filter(
    hotel=hotel,
    active=True
).select_related('category')

print(f"📦 Creating snapshots for {items.count()} active items...")

created_count = 0
for item in items:
    # Create November snapshot from current stock
    StockSnapshot.objects.create(
        hotel=hotel,
        item=item,
        period=nov_period,
        closing_full_units=item.current_full_units,
        closing_partial_units=item.current_partial_units,
        unit_cost=item.unit_cost,
        cost_per_serving=item.cost_per_serving,
        closing_stock_value=item.total_stock_value,
        menu_price=item.menu_price or Decimal('0.00')
    )
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count}/{items.count()} snapshots...")

print(f"✅ Created {created_count} snapshots")

# Calculate total value
nov_snapshots = StockSnapshot.objects.filter(period=nov_period)
total_value = sum(s.closing_stock_value for s in nov_snapshots)
print(f"💰 November total value: €{total_value:,.2f}")
print()

# Create stocktake with transaction
print("📋 Creating stocktake...")
with transaction.atomic():
    # Create stocktake
    stocktake, st_created = Stocktake.objects.get_or_create(
        hotel=hotel,
        period_start=nov_period.start_date,
        period_end=nov_period.end_date,
        defaults={
            'status': Stocktake.DRAFT,
            'notes': 'November 2025 stocktake (ready for counting)'
        }
    )
    
    if st_created:
        print(f"✅ Created stocktake (ID: {stocktake.id})")
    else:
        # Delete existing lines if recreating
        deleted_lines = StocktakeLine.objects.filter(
            stocktake=stocktake
        ).delete()[0]
        if deleted_lines > 0:
            print(f"🗑️  Deleted {deleted_lines} old lines")
        print(f"✓ Using existing stocktake (ID: {stocktake.id})")
    
    # Create stocktake lines from November snapshots
    print(f"📸 Creating lines from {nov_snapshots.count()} snapshots...")
    created_lines = 0
    total_opening = Decimal('0.00')
    
    for snapshot in nov_snapshots:
        # Opening stock = total servings from snapshot
        opening_qty = snapshot.total_servings
        
        # Create stocktake line
        # For November, we set counted = opening (like October baseline)
        # User can modify these counts later
        line = StocktakeLine.objects.create(
            stocktake=stocktake,
            item=snapshot.item,
            # Opening stock = total servings
            opening_qty=opening_qty,
            # No movements yet (will be added later if needed)
            purchases=Decimal('0.0000'),
            sales=Decimal('0.0000'),
            waste=Decimal('0.0000'),
            transfers_in=Decimal('0.0000'),
            transfers_out=Decimal('0.0000'),
            adjustments=Decimal('0.0000'),
            # Counted = same as opening (baseline for now)
            counted_full_units=snapshot.closing_full_units,
            counted_partial_units=snapshot.closing_partial_units,
            # Frozen costs
            valuation_cost=snapshot.cost_per_serving
        )
        
        total_opening += line.opening_value
        created_lines += 1
        
        if created_lines % 50 == 0:
            print(f"  Created {created_lines}/{nov_snapshots.count()} lines...")
    
    print(f"✅ Created {created_lines} stocktake lines")
    print()

print("=" * 80)
print("NOVEMBER 2025 STOCKTAKE CREATED")
print("=" * 80)
print(f"Period ID: {nov_period.id}")
print(f"Period: {nov_period.period_name}")
print(f"Status: {'CLOSED' if nov_period.is_closed else 'OPEN'}")
print(f"Dates: {nov_period.start_date} to {nov_period.end_date}")
print()
print(f"Stocktake ID: {stocktake.id}")
print(f"Status: {stocktake.status}")
print(f"Total Lines: {created_lines}")
print(f"Total Opening Value: €{total_opening:,.2f}")
print()

# Calculate current variance (should be 0 if counted = opening)
total_variance = sum(line.variance_value for line in stocktake.lines.all())
print(f"Current Variance: €{total_variance:,.2f}")
if abs(total_variance) < Decimal('0.01'):
    print("✅ Variance is zero (counted = opening)")
print()

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. ✅ November 2025 period created")
print("2. ✅ Stock snapshots created")
print("3. ✅ Stocktake created with counted values (baseline)")
print()
print("To modify counted values:")
print("   - Update counted_full_units and counted_partial_units")
print("   - This will automatically calculate variance")
print()
print("To close the stocktake:")
print(f"   stocktake = Stocktake.objects.get(id={stocktake.id})")
print("   stocktake.status = 'APPROVED'")
print("   stocktake.approved_at = timezone.now()")
print("   stocktake.save()")
print()
print("To close the period:")
print(f"   period = StockPeriod.objects.get(id={nov_period.id})")
print("   period.is_closed = True")
print("   period.closed_at = timezone.now()")
print("   period.save()")
print("=" * 80)
