"""
Create September 2025 period and stocktake.
Opening stock will come from August closing (to be added later).
For now, we'll create the structure with counted values so it can be closed.
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
print("CREATE SEPTEMBER 2025 PERIOD AND STOCKTAKE")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}")
print()

# Create September 2025 period
print("📅 Creating September 2025 period...")
sept_period, created = StockPeriod.objects.get_or_create(
    hotel=hotel,
    period_type='MONTHLY',
    year=2025,
    month=9,
    defaults={
        'is_closed': False,
        'start_date': date(2025, 9, 1),
        'end_date': date(2025, 9, 30),
        'period_name': 'September 2025'
    }
)

if created:
    print(f"✅ Created September 2025 period (ID: {sept_period.id})")
else:
    print(f"✓ September 2025 period exists (ID: {sept_period.id})")
print()

# Get all active stock items
items = StockItem.objects.filter(
    hotel=hotel,
    active=True
).select_related('category')

print(f"📦 Found {items.count()} active items")
print()

# Create stocktake with transaction
print("📋 Creating September stocktake...")
with transaction.atomic():
    # Create stocktake
    stocktake, st_created = Stocktake.objects.get_or_create(
        hotel=hotel,
        period_start=sept_period.start_date,
        period_end=sept_period.end_date,
        defaults={
            'status': Stocktake.DRAFT,
            'notes': 'September 2025 stocktake - opening from August closing'
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
    
    # Create stocktake lines for each item
    print(f"📝 Creating lines for {items.count()} items...")
    created_lines = 0
    
    for item in items:
        # Create stocktake line
        # Opening will be set later from August closing
        # For now, set counted = current stock
        line = StocktakeLine.objects.create(
            stocktake=stocktake,
            item=item,
            # Opening stock = 0 for now (will update from August)
            opening_qty=Decimal('0.0000'),
            # No movements yet (will be added later if needed)
            purchases=Decimal('0.0000'),
            waste=Decimal('0.0000'),
            transfers_in=Decimal('0.0000'),
            transfers_out=Decimal('0.0000'),
            adjustments=Decimal('0.0000'),
            # Counted = current stock levels
            counted_full_units=item.current_full_units,
            counted_partial_units=item.current_partial_units,
            # Frozen costs
            valuation_cost=item.cost_per_serving
        )
        
        created_lines += 1
        
        if created_lines % 50 == 0:
            print(f"  Created {created_lines}/{items.count()} lines...")
    
    print(f"✅ Created {created_lines} stocktake lines")
    print()

# Calculate totals
total_counted_value = sum(line.counted_value for line in stocktake.lines.all())

print("=" * 80)
print("SEPTEMBER 2025 CREATED")
print("=" * 80)
print(f"Period ID: {sept_period.id}")
print(f"Period: {sept_period.period_name}")
print(f"Status: {'CLOSED' if sept_period.is_closed else 'OPEN'}")
print(f"Dates: {sept_period.start_date} to {sept_period.end_date}")
print()
print(f"Stocktake ID: {stocktake.id}")
print(f"Status: {stocktake.status}")
print(f"Total Lines: {created_lines}")
print(f"Total Counted Value: €{total_counted_value:,.2f}")
print()

print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("1. ✅ September 2025 period created")
print("2. ✅ September stocktake created")
print("3. ✅ Stocktake lines created with counted values (current stock)")
print()
print("To add opening stock from August closing:")
print("   - Create August period and snapshots first")
print("   - Then update September opening_qty from August closing")
print()
print("Current state:")
print("   - Opening: €0.00 (to be set from August)")
print(f"   - Counted: €{total_counted_value:,.2f} (from current stock)")
print()
print("When ready to close:")
print(f"   stocktake = Stocktake.objects.get(id={stocktake.id})")
print("   stocktake.status = 'APPROVED'")
print("   stocktake.approved_at = timezone.now()")
print("   stocktake.save()")
print()
print(f"   period = StockPeriod.objects.get(id={sept_period.id})")
print("   period.is_closed = True")
print("   period.closed_at = timezone.now()")
print("   period.save()")
print("=" * 80)
