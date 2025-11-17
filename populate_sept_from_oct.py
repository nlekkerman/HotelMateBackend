"""
Populate September closing stock from October opening stock
Since October opening = September closing in stock tracking
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod, StockItem
from hotel.models import Hotel

print(f"\n{'='*80}")
print("POPULATING SEPTEMBER CLOSING FROM OCTOBER OPENING")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Get periods
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)
oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

print(f"September: {sept_period.start_date} to {sept_period.end_date}")
print(f"October:   {oct_period.start_date} to {oct_period.end_date}\n")

# Get all items
items = StockItem.objects.filter(hotel=hotel, active=True)
print(f"Processing {items.count()} items...\n")

updated_count = 0
skipped_count = 0

for item in items:
    try:
        # Get October snapshot (has the opening stock we want)
        oct_snapshot = StockSnapshot.objects.get(
            hotel=hotel, item=item, period=oct_period
        )
        
        # Get September snapshot (needs closing stock)
        sept_snapshot = StockSnapshot.objects.get(
            hotel=hotel, item=item, period=sept_period
        )
        
        # October's closing stock becomes September's closing stock
        # (because Sept closing = Oct opening in normal flow)
        sept_snapshot.closing_full_units = oct_snapshot.closing_full_units
        sept_snapshot.closing_partial_units = oct_snapshot.closing_partial_units
        
        # Recalculate value
        if item.category.code in ['D', 'B', 'M']:
            full_value = sept_snapshot.closing_full_units * item.unit_cost
            partial_value = sept_snapshot.closing_partial_units * item.cost_per_serving
        else:
            full_value = sept_snapshot.closing_full_units * item.unit_cost
            partial_value = sept_snapshot.closing_partial_units * item.unit_cost
        
        sept_snapshot.closing_stock_value = (full_value + partial_value).quantize(
            Decimal('0.01')
        )
        sept_snapshot.save()
        
        updated_count += 1
        if updated_count % 50 == 0:
            print(f"Updated {updated_count} snapshots...")
            
    except StockSnapshot.DoesNotExist:
        skipped_count += 1

print(f"\n{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print(f"✓ Updated: {updated_count} September snapshots")
print(f"⚬ Skipped: {skipped_count} snapshots")
print(f"{'='*80}\n")

# Verify with samples
print("Sample September closing stock (now populated):")
print("-" * 80)

sample = StockSnapshot.objects.filter(
    period=sept_period,
    closing_stock_value__gt=Decimal('0')
).select_related('item', 'item__category')[:10]

for snap in sample:
    cat = snap.item.category.code
    print(f"{snap.item.sku:<10} {snap.item.name:<40}")
    print(f"  [{cat}] {snap.closing_full_units} full, {snap.closing_partial_units} partial - €{snap.closing_stock_value}\n")

print(f"{'='*80}\n")
