import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    Stocktake, StocktakeLine, StockSnapshot, 
    StockPeriod, StockItem
)

# Get October stocktake
oct_stocktake = Stocktake.objects.filter(
    hotel__name='Hotel Killarney',
    period_start__year=2025,
    period_start__month=10
).first()

if not oct_stocktake:
    print("❌ No October stocktake found")
    exit()

print(f"Found October stocktake: ID {oct_stocktake.id}")
print(f"Period: {oct_stocktake.period_start} to {oct_stocktake.period_end}")

# Get September period
sept_period = StockPeriod.objects.filter(
    hotel__name='Hotel Killarney',
    start_date__year=2025,
    start_date__month=9
).first()

if not sept_period:
    print("❌ September period not found")
    exit()

# Get September closing snapshots
sept_snapshots = StockSnapshot.objects.filter(
    period=sept_period
).select_related('item')

print(f"\nSeptember snapshots: {sept_snapshots.count()}")

# Update October opening_qty for each line
updated = 0
errors = []

for snapshot in sept_snapshots:
    item = snapshot.item
    
    # Calculate expected opening qty from September closing
    # opening_qty = (full_units × uom) + partial_units
    expected_opening = (snapshot.closing_full_units * item.uom) + snapshot.closing_partial_units
    
    # Get October stocktake line for this item
    try:
        oct_line = StocktakeLine.objects.get(
            stocktake=oct_stocktake,
            item=item
        )
        
        # Update opening_qty
        old_opening = oct_line.opening_qty
        oct_line.opening_qty = expected_opening
        oct_line.save()
        
        updated += 1
        
        if updated <= 5:
            print(f"\n{item.sku}:")
            print(f"  Sept closing: {snapshot.closing_full_units} full + {snapshot.closing_partial_units} partial")
            print(f"  Old opening_qty: {old_opening}")
            print(f"  New opening_qty: {expected_opening}")
    
    except StocktakeLine.DoesNotExist:
        errors.append(f"{item.sku}: No October line found")

print(f"\n✅ Updated {updated} October opening quantities")

if errors:
    print(f"\n⚠️ Errors: {len(errors)}")
    for error in errors[:10]:
        print(f"  {error}")
