"""
DIAGNOSTIC: Why Opening Stock Only Populates for Beers

This script investigates why opening stock is populated for beers but not for 
other categories (Spirits, Wine, Minerals).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem, Stocktake
from decimal import Decimal

print("=" * 120)
print("DIAGNOSTIC: OPENING STOCK POPULATION ISSUE")
print("=" * 120)
print()

# Get recent closed period
closed_period = StockPeriod.objects.filter(
    hotel_id=2,
    is_closed=True,
    year=2025
).order_by('-end_date').first()

if not closed_period:
    print("❌ No closed period found")
    exit()

print(f"CLOSED PERIOD: {closed_period.period_name}")
print(f"Dates: {closed_period.start_date} to {closed_period.end_date}")
print(f"Closed: {closed_period.is_closed}")
print()

# Check snapshots in this period
snapshots = StockSnapshot.objects.filter(period=closed_period)
print(f"Total Snapshots: {snapshots.count()}")
print()

# Group by category
categories = {
    'D': 'Draught Beer',
    'B': 'Bottled Beer',
    'S': 'Spirits',
    'W': 'Wine',
    'M': 'Minerals'
}

print("=" * 120)
print("SNAPSHOTS BY CATEGORY (Closing Stock)")
print("=" * 120)
print()

category_data = {}

for cat_code, cat_name in categories.items():
    cat_snaps = snapshots.filter(item__category_id=cat_code)
    
    # Count snapshots with actual stock
    snaps_with_stock = cat_snaps.filter(
        closing_full_units__gt=0
    ) | cat_snaps.filter(
        closing_partial_units__gt=0
    )
    
    total_value = sum(snap.closing_stock_value for snap in cat_snaps)
    
    category_data[cat_code] = {
        'name': cat_name,
        'total_snaps': cat_snaps.count(),
        'with_stock': snaps_with_stock.count(),
        'without_stock': cat_snaps.count() - snaps_with_stock.count(),
        'total_value': total_value
    }
    
    print(f"{cat_code} - {cat_name}")
    print("-" * 120)
    print(f"  Total snapshots: {cat_snaps.count()}")
    print(f"  With stock (full or partial > 0): {snaps_with_stock.count()}")
    print(f"  Without stock (both = 0): {cat_snaps.count() - snaps_with_stock.count()}")
    print(f"  Total value: €{total_value:.2f}")
    
    # Show sample items
    if cat_snaps.count() > 0:
        print(f"\n  Sample items:")
        for snap in cat_snaps[:3]:
            print(f"    {snap.item.sku} - {snap.item.name}")
            print(f"      Full: {snap.closing_full_units}, Partial: {snap.closing_partial_units}, Value: €{snap.closing_stock_value:.2f}")
    print()

# Check if there's a next period
print()
print("=" * 120)
print("CHECKING NEXT PERIOD")
print("=" * 120)
print()

next_period = StockPeriod.objects.filter(
    hotel_id=2,
    start_date__gt=closed_period.end_date,
    year=2025
).order_by('start_date').first()

if next_period:
    print(f"NEXT PERIOD: {next_period.period_name}")
    print(f"Dates: {next_period.start_date} to {next_period.end_date}")
    print(f"Closed: {next_period.is_closed}")
    print()
    
    # Check snapshots in next period
    next_snapshots = StockSnapshot.objects.filter(period=next_period)
    print(f"Total Snapshots: {next_snapshots.count()}")
    print()
    
    if next_snapshots.count() > 0:
        print("=" * 120)
        print("NEXT PERIOD SNAPSHOTS BY CATEGORY")
        print("=" * 120)
        print()
        
        for cat_code, cat_name in categories.items():
            cat_snaps = next_snapshots.filter(item__category_id=cat_code)
            
            # These are CLOSING snapshots, but they show what was used as OPENING
            # for the stocktake
            snaps_with_closing = cat_snaps.filter(
                closing_full_units__gt=0
            ) | cat_snaps.filter(
                closing_partial_units__gt=0
            )
            
            print(f"{cat_code} - {cat_name}")
            print("-" * 120)
            print(f"  Total snapshots: {cat_snaps.count()}")
            print(f"  With closing stock: {snaps_with_closing.count()}")
            print(f"  Without closing stock: {cat_snaps.count() - snaps_with_closing.count()}")
            
            # Show samples
            if cat_snaps.count() > 0:
                print(f"\n  Sample items:")
                for snap in cat_snaps[:3]:
                    print(f"    {snap.item.sku} - {snap.item.name}")
                    print(f"      Full: {snap.closing_full_units}, Partial: {snap.closing_partial_units}")
            print()
    else:
        print("⚠️  Next period has NO snapshots - opening stock was never populated!")
        print()
else:
    print("⚠️  No next period found")
    print()

# Check stocktake for closed period
print()
print("=" * 120)
print("CHECKING STOCKTAKE FOR CLOSED PERIOD")
print("=" * 120)
print()

stocktake = Stocktake.objects.filter(
    hotel_id=2,
    period_start=closed_period.start_date,
    period_end=closed_period.end_date
).first()

if stocktake:
    print(f"Stocktake found: ID {stocktake.id}")
    print(f"Status: {stocktake.status}")
    print(f"Approved: {stocktake.approved_at}")
    print(f"Total lines: {stocktake.lines.count()}")
    print()
    
    # Check lines by category
    print("=" * 120)
    print("STOCKTAKE LINES BY CATEGORY")
    print("=" * 120)
    print()
    
    for cat_code, cat_name in categories.items():
        lines = stocktake.lines.filter(item__category_id=cat_code)
        
        # Count lines with counted values
        lines_counted = lines.filter(
            counted_full_units__gt=0
        ) | lines.filter(
            counted_partial_units__gt=0
        )
        
        print(f"{cat_code} - {cat_name}")
        print("-" * 120)
        print(f"  Total lines: {lines.count()}")
        print(f"  Lines with counted stock: {lines_counted.count()}")
        print(f"  Lines without counted stock: {lines.count() - lines_counted.count()}")
        
        # Show samples
        if lines.count() > 0:
            print(f"\n  Sample lines:")
            for line in lines[:3]:
                print(f"    {line.item.sku} - {line.item.name}")
                print(f"      Counted: Full={line.counted_full_units}, Partial={line.counted_partial_units}")
        print()
else:
    print("❌ No stocktake found for this period!")
    print()

# THE KEY QUESTION
print()
print("=" * 120)
print("DIAGNOSIS")
print("=" * 120)
print()

print("THE ISSUE:")
print("-" * 120)
print("""
When a stocktake is approved, the system should:
1. ✅ Create adjustment movements for variances
2. ✅ Update StockSnapshot.closing_full_units and closing_partial_units

The SECOND step is critical because next period's opening stock comes from
the previous period's closing snapshots.

IF snapshots are NOT updated during approval, then:
- Beers might work if they had manual data entry
- Other categories will have zero opening stock

Let's check the approve_stocktake() function to see if it updates ALL categories...
""")

print()
print("CHECKING: Which categories have closing stock in snapshots?")
print("-" * 120)

for cat_code, data in category_data.items():
    symbol = "✅" if data['with_stock'] > 0 else "❌"
    print(f"{symbol} {cat_code} - {data['name']}: {data['with_stock']}/{data['total_snaps']} items with stock")

print()
print()
print("=" * 120)
print("POSSIBLE CAUSES")
print("=" * 120)
print()

causes = [
    {
        'title': '1. Stocktake Not Approved for All Categories',
        'description': '''
        The stocktake might have been approved, but only certain categories
        had counted values entered. If counted_full_units and counted_partial_units
        are both 0, the snapshot won't have closing stock.
        '''
    },
    {
        'title': '2. approve_stocktake() Not Updating Snapshots',
        'description': '''
        The approve_stocktake() function might not be updating StockSnapshot
        closing values for all categories. Check stock_tracker/stocktake_service.py
        
        It should do this for EVERY line:
        
        snapshot.closing_full_units = line.counted_full_units
        snapshot.closing_partial_units = line.counted_partial_units
        snapshot.closing_stock_value = line.counted_value
        snapshot.save()
        '''
    },
    {
        'title': '3. Snapshots Created Manually for Beers Only',
        'description': '''
        Someone might have manually created or updated snapshots for beers
        but not for other categories. Check if there are any manual scripts
        that update snapshots.
        '''
    },
    {
        'title': '4. Different Approval Process for Different Categories',
        'description': '''
        There might be conditional logic in approve_stocktake() that only
        updates snapshots for certain categories (like beers).
        '''
    }
]

for cause in causes:
    print(f"\n{cause['title']}")
    print("-" * 120)
    print(cause['description'])

print()
print()
print("=" * 120)
print("RECOMMENDATION")
print("=" * 120)
print()

print("""
1. Check stock_tracker/stocktake_service.py → approve_stocktake() function
   - Does it update snapshots for ALL categories?
   - Is there any conditional logic that skips certain categories?

2. Check if counted values were entered for all categories:
   - Look at stocktake lines above
   - If counted_full_units and counted_partial_units are 0, that's the issue

3. Verify the OPENING_STOCK_FIX.md was applied:
   - The fix should update snapshots for ALL categories
   - File location: stock_tracker/stocktake_service.py lines 231-268

4. Re-approve the stocktake if needed:
   - Reopen it via API: POST /api/stock-tracker/{hotel}/periods/{id}/reopen/
   - Re-approve it: POST /api/stock-tracker/{hotel}/stocktakes/{id}/approve/
   - This will update snapshots with current counted values
""")

print()
print("=" * 120)
print("END OF DIAGNOSIS")
print("=" * 120)
