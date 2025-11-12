import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockSnapshot

print("=" * 100)
print("UPDATING SEPTEMBER COUNTED QTY WITH CORRECT VALUES FROM SNAPSHOTS")
print("=" * 100)

# Get September stocktake
sept_stocktake = Stocktake.objects.get(hotel_id=2, period_start='2025-09-01')
print(f"\n✅ September Stocktake: ID={sept_stocktake.id}, Status={sept_stocktake.status}")

# Get September snapshots (these have the CORRECT values we just updated)
sept_snapshots = StockSnapshot.objects.filter(
    period__hotel_id=2,
    period__start_date='2025-09-01',
    item__category__code='M'
).select_related('item')

print(f"✅ Found {sept_snapshots.count()} September snapshots")

# Create lookup dict: SKU -> (closing_full_units, closing_partial_units)
correct_values = {}
for snap in sept_snapshots:
    correct_values[snap.item.sku] = (snap.closing_full_units, snap.closing_partial_units)

print("\n" + "=" * 100)
print("UPDATING SEPTEMBER COUNTED QUANTITIES:")
print("-" * 100)
print(f"{'SKU':<10} {'Item':<30} {'Old Full':<12} {'Old Partial':<12} {'New Full':<12} {'New Partial':<12}")
print("-" * 100)

updated_count = 0

for sku, (correct_full, correct_partial) in correct_values.items():
    try:
        line = StocktakeLine.objects.get(
            stocktake=sept_stocktake,
            item__sku=sku
        )
        
        old_full = line.counted_full_units
        old_partial = line.counted_partial_units
        
        # Update BOTH full and partial units from snapshot
        line.counted_full_units = correct_full
        line.counted_partial_units = correct_partial
        line.save()
        
        print(f"{sku:<10} {line.item.name[:30]:<30} "
              f"{old_full:<12.2f} {old_partial:<12.2f} "
              f"{correct_full:<12.2f} {correct_partial:<12.2f}")
        updated_count += 1
        
    except StocktakeLine.DoesNotExist:
        print(f"❌ {sku}: No stocktake line found")

print("-" * 100)
print(f"Updated: {updated_count} lines")

print("\n" + "=" * 100)
print("VERIFICATION:")
print("=" * 100)

# Recalculate totals
sept_lines = StocktakeLine.objects.filter(
    stocktake=sept_stocktake,
    item__category__code='M'
).select_related('item')

total_counted = Decimal('0')
for line in sept_lines:
    total_counted += line.counted_qty * line.item.cost_per_serving

print(f"\nSeptember Minerals Counted Total: €{total_counted:,.2f}")
print(f"Expected (from Excel): €4,185.64")
print(f"Difference: €{abs(total_counted - Decimal('4185.64')):,.2f}")

if abs(total_counted - Decimal('4185.64')) < Decimal('1.00'):
    print("\n✅ SUCCESS! September counted values now correct!")
else:
    print("\n⚠️ Warning: Small difference detected")

print("=" * 100)
