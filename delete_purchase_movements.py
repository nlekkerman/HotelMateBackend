"""
Script to delete purchase movements for specific items in November 2025 stocktake
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockMovement, StocktakeLine, Stocktake
from datetime import date

# November 2025 stocktake period
period_start = date(2025, 11, 1)
period_end = date(2025, 11, 30)

print("Finding purchase movements in November 2025...")
print("=" * 60)

# Get the November stocktake
stocktake = Stocktake.objects.filter(
    period_start=period_start,
    period_end=period_end,
    hotel__slug='hotel-killarney'
).first()

if not stocktake:
    print("❌ November stocktake not found!")
    exit()

print(f"✅ Found stocktake: {stocktake}")
print()

# Find all PURCHASE movements in this period
purchase_movements = StockMovement.objects.filter(
    hotel__slug='hotel-killarney',
    movement_type='PURCHASE',
    timestamp__gte=period_start,
    timestamp__lte=period_end
).select_related('item')

print(f"Found {purchase_movements.count()} PURCHASE movements")
print()

# Group by item to show totals
from django.db.models import Sum
purchases_by_item = purchase_movements.values(
    'item__code',
    'item__name'
).annotate(
    total_qty=Sum('quantity')
).order_by('-total_qty')

print("Purchases by item:")
print("-" * 60)
for item in purchases_by_item:
    print(f"{item['item__code']:15} {item['item__name']:30} {item['total_qty']:>10}")

print()
print("=" * 60)

# Ask for confirmation
response = input("\n⚠️  DELETE ALL these purchase movements? (yes/no): ").strip().lower()

if response == 'yes':
    count = purchase_movements.count()
    purchase_movements.delete()
    print(f"\n✅ Deleted {count} purchase movements")
    
    # Recalculate all affected stocktake lines
    print("\n♻️  Recalculating stocktake lines...")
    from stock_tracker.stocktake_service import _calculate_period_movements
    
    affected_lines = StocktakeLine.objects.filter(
        stocktake=stocktake
    )
    
    for line in affected_lines:
        movements = _calculate_period_movements(
            line.item,
            stocktake.period_start,
            stocktake.period_end
        )
        line.purchases = movements['purchases']
        line.waste = movements['waste']
        line.save()
    
    print(f"✅ Recalculated {affected_lines.count()} stocktake lines")
    print("\n✨ All purchases cleared!")
    
else:
    print("\n❌ Cancelled - no changes made")
