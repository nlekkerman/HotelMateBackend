"""
Test that opening stock now populates for ALL categories (not just beers)
after approving a stocktake.

This verifies the fix to approve_stocktake() function.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel
from decimal import Decimal

print("=" * 80)
print("TESTING OPENING STOCK FIX FOR ALL CATEGORIES")
print("=" * 80)

hotel = Hotel.objects.first()

# Find a recent closed period
recent_period = StockPeriod.objects.filter(
    hotel=hotel,
    is_closed=True,
    year=2025
).order_by('-end_date').first()

if not recent_period:
    print("\n❌ No closed periods found for testing")
    exit()

print(f"\n✓ Testing with closed period: {recent_period.period_name}")
print(f"  Dates: {recent_period.start_date} to {recent_period.end_date}")

# Check snapshots by category
snapshots = StockSnapshot.objects.filter(
    period=recent_period
).select_related('item', 'item__category')

# Group by category
category_stats = {}
for snapshot in snapshots:
    cat_code = snapshot.item.category_id
    cat_name = snapshot.item.category.name if snapshot.item.category else 'N/A'
    
    if cat_code not in category_stats:
        category_stats[cat_code] = {
            'name': cat_name,
            'total_items': 0,
            'items_with_stock': 0,
            'total_value': Decimal('0.00')
        }
    
    category_stats[cat_code]['total_items'] += 1
    
    if (snapshot.closing_full_units > 0 or 
        snapshot.closing_partial_units > 0):
        category_stats[cat_code]['items_with_stock'] += 1
        category_stats[cat_code]['total_value'] += snapshot.closing_stock_value

print("\n" + "=" * 80)
print("CLOSING STOCK BY CATEGORY (for next period's opening stock)")
print("=" * 80)

for cat_code in sorted(category_stats.keys()):
    stats = category_stats[cat_code]
    print(f"\n{cat_code} - {stats['name']}")
    print(f"  Total items: {stats['total_items']}")
    print(f"  Items with stock: {stats['items_with_stock']}")
    print(f"  Total value: €{stats['total_value']:.2f}")
    
    # Status indicator
    if stats['items_with_stock'] > 0:
        print(f"  ✅ HAS CLOSING STOCK - will populate next period")
    else:
        print(f"  ⚠️  NO STOCK - check if stocktake was approved")

# Check if there's a next period
next_period = StockPeriod.objects.filter(
    hotel=hotel,
    start_date__gt=recent_period.end_date,
    year=2025
).order_by('start_date').first()

if next_period:
    print("\n" + "=" * 80)
    print(f"NEXT PERIOD: {next_period.period_name}")
    print("=" * 80)
    
    next_snapshots = StockSnapshot.objects.filter(
        period=next_period
    ).select_related('item', 'item__category')
    
    if next_snapshots.exists():
        next_cat_stats = {}
        for snapshot in next_snapshots:
            cat_code = snapshot.item.category_id
            if cat_code not in next_cat_stats:
                next_cat_stats[cat_code] = {
                    'items': 0,
                    'with_opening': 0
                }
            
            next_cat_stats[cat_code]['items'] += 1
            
            # Check if has opening stock via serializer logic
            # (gets from previous period's closing)
            prev_snap = StockSnapshot.objects.filter(
                hotel=snapshot.hotel,
                item=snapshot.item,
                period__end_date__lt=next_period.start_date
            ).order_by('-period__end_date').first()
            
            if prev_snap and prev_snap.total_servings > 0:
                next_cat_stats[cat_code]['with_opening'] += 1
        
        print("\nOpening stock status in next period:")
        for cat_code in sorted(next_cat_stats.keys()):
            stats = next_cat_stats[cat_code]
            cat_name = category_stats.get(cat_code, {}).get('name', 'Unknown')
            print(f"\n{cat_code} - {cat_name}")
            print(f"  Items: {stats['items']}")
            print(f"  With opening stock: {stats['with_opening']}")
            
            if stats['with_opening'] > 0:
                print(f"  ✅ Opening stock populated!")
            else:
                print(f"  ❌ No opening stock - needs fix")
    else:
        print("\n⚠️  Next period has no snapshots yet")
else:
    print("\n⚠️  No next period found")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nTo fix opening stock for existing periods:")
print("1. Reopen the stocktake")
print("2. Re-approve it (this will update snapshots)")
print("3. Check next period's opening stock")

