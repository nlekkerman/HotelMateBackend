"""
Populate September 2025 snapshots with counted stock from backup
Updates closing_full_units and closing_partial_units from september_closing_stock.json
"""
import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod, StockItem
from hotel.models import Hotel

print(f"\n{'='*80}")
print("POPULATING SEPTEMBER SNAPSHOTS FROM BACKUP")
print(f"{'='*80}\n")

# Load September closing stock backup
json_file = 'september_closing_stock.json'
if not os.path.exists(json_file):
    print(f"❌ ERROR: {json_file} not found!")
    exit(1)

with open(json_file, 'r') as f:
    backup_data = json.load(f)

print(f"Loaded {len(backup_data)} items from backup\n")

# Get September period
hotel = Hotel.objects.first()
sept_period = StockPeriod.objects.get(
    hotel=hotel,
    year=2025,
    month=9,
    period_type='MONTHLY'
)

print(f"Period: {sept_period.period_name}")
print(f"Date range: {sept_period.start_date} to {sept_period.end_date}\n")

# Update snapshots
print("Updating snapshots...")
print("-" * 80)

updated_count = 0
not_found_count = 0
skipped_count = 0

for sku, data in backup_data.items():
    try:
        # Get the item
        item = StockItem.objects.get(hotel=hotel, sku=sku)
        
        # Get the snapshot for this item in September period
        snapshot = StockSnapshot.objects.get(
            hotel=hotel,
            item=item,
            period=sept_period
        )
        
        # Update closing stock from backup
        old_full = snapshot.closing_full_units
        old_partial = snapshot.closing_partial_units
        
        new_full = Decimal(data.get('counted_full_units', '0.00'))
        new_partial = Decimal(data.get('counted_partial_units', '0.00'))
        
        # Calculate stock value
        if item.category.code in ['D', 'B', 'M']:
            # For these categories, partial = individual servings/bottles
            full_value = new_full * item.unit_cost
            partial_value = new_partial * item.cost_per_serving
        else:
            # For Spirits and Wine, partial = fractional units
            full_value = new_full * item.unit_cost
            partial_value = new_partial * item.unit_cost
        
        closing_value = (full_value + partial_value).quantize(Decimal('0.01'))
        
        # Update snapshot
        snapshot.closing_full_units = new_full
        snapshot.closing_partial_units = new_partial
        snapshot.closing_stock_value = closing_value
        snapshot.save()
        
        updated_count += 1
        
        if updated_count % 20 == 0:
            print(f"Updated {updated_count} snapshots...")
            
    except StockItem.DoesNotExist:
        not_found_count += 1
        if not_found_count <= 5:
            print(f"⚠ Item not found: {sku}")
    except StockSnapshot.DoesNotExist:
        skipped_count += 1
        if skipped_count <= 5:
            print(f"⚠ Snapshot not found for: {sku}")

print(f"\n{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print(f"✓ Updated: {updated_count} snapshots")
print(f"⚬ Skipped (not found): {skipped_count} snapshots")
print(f"⚠ Items not in DB: {not_found_count} items")
print(f"{'='*80}\n")

# Show sample of updated snapshots
print("Sample of updated September snapshots:")
print("-" * 80)

sample_snapshots = StockSnapshot.objects.filter(
    period=sept_period,
    closing_stock_value__gt=Decimal('0')
).select_related('item', 'item__category')[:10]

for snap in sample_snapshots:
    cat = snap.item.category.code
    print(f"{snap.item.sku:<10} {snap.item.name:<40}")
    print(f"  [{cat}] Closing: {snap.closing_full_units} full, {snap.closing_partial_units} partial")
    print(f"  Value: €{snap.closing_stock_value}\n")

print(f"{'='*80}\n")
