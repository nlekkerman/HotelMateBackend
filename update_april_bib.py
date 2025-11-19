"""
Update April 2025 BIB counted stock to 2.5 boxes for all items.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("UPDATE APRIL 2025 BIB - SET TO 2.5 BOXES")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Find April 2025 stocktake
april_stocktakes = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=4
).order_by('-period_start')

if not april_stocktakes.exists():
    print("❌ No April 2025 stocktake found!")
    exit(1)

april_stocktake = april_stocktakes.first()
print(f"Found stocktake: ID {april_stocktake.id}")
print(f"Period: {april_stocktake.period_start} to {april_stocktake.period_end}")
print(f"Status: {april_stocktake.status}")
print()

# Get all BIB lines (category M, subcategory BIB)
bib_lines = StocktakeLine.objects.filter(
    stocktake=april_stocktake,
    item__category__code='M',
    item__subcategory='BIB'
).select_related('item')

total_lines = bib_lines.count()
print(f"Found {total_lines} BIB items")
print()

if total_lines == 0:
    print("❌ No BIB items found in this stocktake!")
    exit(1)

# Confirm before updating
print("This will set counted stock to:")
print("  - counted_full_units: 2 (boxes)")
print("  - counted_partial_units: 0.5 (half box = 9 liters)")
print("  Total: 2.5 boxes")
print()
response = input("Continue? (yes/no): ")

if response.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

print()
print("Updating...")
print("-" * 100)

updated = 0
for line in bib_lines:
    # Store old values
    old_full = line.counted_full_units
    old_partial = line.counted_partial_units
    old_counted_qty = line.counted_qty
    old_counted_value = line.counted_value
    
    # Update to 2.5 boxes (2 full + 0.5 partial)
    line.counted_full_units = Decimal('2.00')
    line.counted_partial_units = Decimal('0.50')
    line.save()
    
    # Refresh to get calculated values
    line.refresh_from_db()
    
    updated += 1
    
    # Show change
    total_boxes = line.counted_full_units + line.counted_partial_units
    print(f"{line.item.sku} - {line.item.name}")
    print(f"  Old: {old_full} + {old_partial} = "
          f"{float(old_full + old_partial):.2f} boxes")
    print(f"       {old_counted_qty:.2f} servings (€{old_counted_value:.2f})")
    print(f"  New: {line.counted_full_units} + "
          f"{line.counted_partial_units} = {float(total_boxes):.2f} boxes")
    print(f"       {line.counted_qty:.2f} servings "
          f"(€{line.counted_value:.2f})")
    print(f"  Variance: {line.variance_qty:.2f} servings "
          f"(€{line.variance_value:.2f})")
    print()

print("-" * 100)
print(f"✅ Updated {updated} BIB items")
print()

# Calculate new totals
total_counted_value = sum(line.counted_value for line in bib_lines)
total_variance_value = sum(line.variance_value for line in bib_lines)

print("New Totals:")
print(f"  Total Counted Value: €{total_counted_value:,.2f}")
print(f"  Total Variance: €{total_variance_value:,.2f}")
print()
print("=" * 100)
