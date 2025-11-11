"""
Fix September 2025 Stocktake - Populate opening stock from September snapshots

The September stocktake opening stock should come from September snapshots
(not August, which doesn't exist).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    Stocktake,
    StocktakeLine,
    StockSnapshot
)
from hotel.models import Hotel
from decimal import Decimal

print("=" * 80)
print("FIXING SEPTEMBER 2025 STOCKTAKE OPENING STOCK")
print("=" * 80)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Get September 2025 stocktake
try:
    stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start__year=2025,
        period_start__month=9
    )
    print(f"✓ September 2025 stocktake found (ID: {stocktake.id})")
    print(f"  Status: {stocktake.status}")
    print(f"  Lines: {stocktake.lines.count()}")
except Stocktake.DoesNotExist:
    print("❌ September 2025 stocktake not found!")
    exit(1)

# Get September snapshots
snapshots = StockSnapshot.objects.filter(
    hotel=hotel,
    period__year=2025,
    period__month=9
)

print(f"  Snapshots: {snapshots.count()}")
print()

if snapshots.count() == 0:
    print("❌ No September snapshots found!")
    print("   Run populate_september_snapshots.py first")
    exit(1)

# Update stocktake lines with opening stock from snapshots
print("Updating stocktake lines with opening stock...")
print("-" * 80)

updated_count = 0
created_count = 0
skipped_count = 0

for snapshot in snapshots:
    # Calculate opening_qty in servings
    category = snapshot.item.category_id
    
    # Draught + BIB (LT) + Dozen: partial = servings already
    if (category == 'D') or (snapshot.item.size and 
        ('Doz' in snapshot.item.size or 'LT' in snapshot.item.size.upper())):
        full_servings = snapshot.closing_full_units * snapshot.item.uom
        opening_qty = full_servings + snapshot.closing_partial_units
    else:
        # Spirits, Wine, Individual: partial = fractional
        full_servings = snapshot.closing_full_units * snapshot.item.uom
        partial_servings = snapshot.closing_partial_units * snapshot.item.uom
        opening_qty = full_servings + partial_servings
    
    # Get or create stocktake line
    line, created = StocktakeLine.objects.get_or_create(
        stocktake=stocktake,
        item=snapshot.item,
        defaults={
            'opening_qty': opening_qty,
            'valuation_cost': snapshot.cost_per_serving,
            'counted_full_units': Decimal('0.00'),
            'counted_partial_units': Decimal('0.00')
        }
    )
    
    if created:
        created_count += 1
    else:
        # Update existing line
        if line.opening_qty == 0:
            line.opening_qty = opening_qty
            line.valuation_cost = snapshot.cost_per_serving
            line.save(update_fields=['opening_qty', 'valuation_cost'])
            updated_count += 1
        else:
            skipped_count += 1
    
    if (updated_count + created_count) % 50 == 0:
        print(f"  Processed {updated_count + created_count} lines...")

print()
print(f"✓ Created {created_count} new lines")
print(f"✓ Updated {updated_count} existing lines")
print(f"  Skipped {skipped_count} lines (already had opening stock)")
print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)

lines = stocktake.lines.all()
lines_with_opening = lines.exclude(opening_qty=0).count()

print(f"Total Lines: {lines.count()}")
print(f"Lines with Opening Stock: {lines_with_opening}")
print()

# Calculate total opening value
from django.db.models import Sum, F

total_opening = lines.aggregate(
    total=Sum(F('opening_qty') * F('valuation_cost'))
)['total'] or Decimal('0.00')

print(f"Total Opening Stock Value: €{total_opening:,.2f}")
print()
print("✅ September 2025 stocktake opening stock updated!")
print()
print("Next: Refresh the stocktake page in your browser")
print("=" * 80)
