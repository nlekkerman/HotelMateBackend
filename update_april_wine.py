"""
Update April 2025 Wine counted stock to 3.5 bottles for all items.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("UPDATE APRIL 2025 WINE - SET TO 3.5 BOTTLES")
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

# Get all Wine lines (category W)
wine_lines = StocktakeLine.objects.filter(
    stocktake=april_stocktake,
    item__category__code='W'
).select_related('item')

total_lines = wine_lines.count()
print(f"Found {total_lines} Wine items")
print()

if total_lines == 0:
    print("❌ No wine items found in this stocktake!")
    exit(1)

# Confirm before updating
print("This will set counted stock to:")
print("  - counted_full_units: 3.5 (bottles)")
print("  - counted_partial_units: 0 (with UOM=1)")
print("  Total: 3.5 bottles")
print()
response = input("Continue? (yes/no): ")

if response.lower() != 'yes':
    print("❌ Cancelled")
    exit(0)

print()
print("Updating...")
print("-" * 100)

updated = 0
for line in wine_lines:
    # Store old values
    old_full = line.counted_full_units
    old_partial = line.counted_partial_units
    old_counted_qty = line.counted_qty
    old_counted_value = line.counted_value
    
    # Update to 3.5 bottles (UOM=1, so full_units holds total)
    line.counted_full_units = Decimal('3.50')
    line.counted_partial_units = Decimal('0.00')
    line.save()
    
    # Refresh to get calculated values
    line.refresh_from_db()
    
    updated += 1
    
    # Show change
    print(f"{line.item.sku} - {line.item.name}")
    print(f"  Old: {float(old_full + old_partial):.2f} bottles")
    print(f"       {old_counted_qty:.2f} glasses (€{old_counted_value:.2f})")
    print(f"  New: {float(line.counted_full_units):.2f} bottles")
    print(f"       {line.counted_qty:.2f} glasses "
          f"(€{line.counted_value:.2f})")
    print(f"  Variance: {line.variance_qty:.2f} glasses "
          f"(€{line.variance_value:.2f})")
    print()

print("-" * 100)
print(f"✅ Updated {updated} Wine items")
print()

# Calculate new totals
total_counted_value = sum(line.counted_value for line in wine_lines)
total_variance_value = sum(line.variance_value for line in wine_lines)

print("New Totals:")
print(f"  Total Counted Value: €{total_counted_value:,.2f}")
print(f"  Total Variance: €{total_variance_value:,.2f}")
print()
print("=" * 100)
