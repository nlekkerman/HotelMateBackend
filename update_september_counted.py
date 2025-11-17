"""
Update September stocktake counted values from closing stock
This populates the counted fields in StocktakeLine from StockSnapshot closing values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    Stocktake, StocktakeLine, StockSnapshot, StockPeriod, StockItem
)
from hotel.models import Hotel

print(f"\n{'='*80}")
print("UPDATING SEPTEMBER STOCKTAKE COUNTED VALUES")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

print(f"Period: {sept_period.period_name}")
print(f"Date range: {sept_period.start_date} to {sept_period.end_date}\n")

# Get or create September stocktake
stocktake, created = Stocktake.objects.get_or_create(
    hotel=hotel,
    period_start=sept_period.start_date,
    period_end=sept_period.end_date,
    defaults={
        'status': 'DRAFT',
        'notes': 'September 2025 stocktake - populated from closing stock'
    }
)

if created:
    print(f"✓ Created new stocktake for September\n")
else:
    print(f"✓ Found existing stocktake (ID: {stocktake.id})\n")

# Get all items
items = StockItem.objects.filter(hotel=hotel, active=True)
print(f"Processing {items.count()} items...\n")

updated_count = 0
created_count = 0

for item in items:
    try:
        # Get September snapshot (has closing stock)
        sept_snapshot = StockSnapshot.objects.get(
            hotel=hotel, item=item, period=sept_period
        )
        
        # Get or create stocktake line
        line, line_created = StocktakeLine.objects.get_or_create(
            stocktake=stocktake,
            item=item,
            defaults={
                'opening_qty': Decimal('0'),  # September opening = 0
                'counted_full_units': sept_snapshot.closing_full_units,
                'counted_partial_units': sept_snapshot.closing_partial_units,
                'location': None,
            }
        )
        
        if line_created:
            created_count += 1
        else:
            # Update existing line
            line.counted_full_units = sept_snapshot.closing_full_units
            line.counted_partial_units = sept_snapshot.closing_partial_units
            line.save()
            updated_count += 1
        
        if (created_count + updated_count) % 50 == 0:
            print(f"Processed {created_count + updated_count} lines...")
            
    except StockSnapshot.DoesNotExist:
        print(f"⚠ No snapshot for {item.sku}")
        continue

print(f"\n{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print(f"✓ Created: {created_count} new stocktake lines")
print(f"✓ Updated: {updated_count} existing lines")
print(f"✓ Total lines: {stocktake.lines.count()}")
print(f"{'='*80}\n")

# Show sample data
print("Sample stocktake lines:")
print("-" * 80)

samples = stocktake.lines.filter(
    item__sku__in=['B0070', 'B0085', 'D0004', 'S0610', 'M0140']
).select_related('item')

for line in samples:
    print(f"{line.item.sku} - {line.item.name}")
    print(f"  Opening: {line.opening_qty} servings")
    print(f"  Counted: {line.counted_full_units} full + "
          f"{line.counted_partial_units} partial")
    print(f"  Expected: {line.expected_qty} servings")
    print(f"  Variance: {line.variance_qty} servings\n")

print(f"{'='*80}\n")
