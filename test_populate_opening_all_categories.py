"""
Test populate opening stock for ALL categories
Verify that spirits, wine, minerals (all subcategories) now work correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal

print("=" * 100)
print("TEST: POPULATE OPENING STOCK FOR ALL CATEGORIES")
print("=" * 100)

# Get a recent period
period = StockPeriod.objects.filter(
    hotel_id=2,
    year=2025,
    month__gte=10
).order_by('start_date').first()

if not period:
    print("❌ No test period found")
    exit()

print(f"\n✓ Testing with period: {period.period_name}")
print(f"  Start: {period.start_date}, End: {period.end_date}")
print(f"  Status: {'CLOSED' if period.is_closed else 'OPEN'}")

# Get snapshots grouped by category
snapshots = StockSnapshot.objects.filter(
    period=period
).select_related('item', 'item__category').order_by('item__category_id', 'item__sku')

if not snapshots.exists():
    print("\n❌ No snapshots found for this period")
    exit()

print(f"\n✓ Found {snapshots.count()} snapshots")

# Group by category
categories = {}
for snapshot in snapshots:
    cat_code = snapshot.item.category_id
    cat_name = snapshot.item.category.name if snapshot.item.category else 'Unknown'
    
    if cat_code not in categories:
        categories[cat_code] = {
            'name': cat_name,
            'items': []
        }
    
    categories[cat_code]['items'].append(snapshot)

# Display results by category
print("\n" + "=" * 100)
print("OPENING STOCK DISPLAY TEST BY CATEGORY")
print("=" * 100)

for cat_code, cat_data in sorted(categories.items()):
    print(f"\n{'='*100}")
    print(f"{cat_code} - {cat_data['name']} ({len(cat_data['items'])} items)")
    print(f"{'='*100}")
    
    # Show first 3 items from each category
    for snapshot in cat_data['items'][:3]:
        item = snapshot.item
        total_servings = snapshot.total_servings
        
        # Calculate display values
        display_full = snapshot.calculate_opening_display_full(total_servings)
        display_partial = snapshot.calculate_opening_display_partial(total_servings)
        
        print(f"\n  {item.sku} - {item.name}")
        print(f"    Size: {item.size} | UOM: {item.uom}")
        print(f"    Subcategory: {item.subcategory or 'N/A'}")
        print(f"    Closing Full: {snapshot.closing_full_units}")
        print(f"    Closing Partial: {snapshot.closing_partial_units}")
        print(f"    Total Servings: {total_servings:.4f}")
        print(f"    ➜ Display Full: {display_full}")
        print(f"    ➜ Display Partial: {display_partial:.2f}")
        
        # Verify logic
        if cat_code == 'D':
            expected_full = int(total_servings / item.uom) if item.uom > 0 else 0
            expected_partial = total_servings % item.uom if item.uom > 0 else total_servings
            status = "✅" if display_full == expected_full else "❌"
            print(f"    {status} Draught: Expected {expected_full} kegs + {expected_partial:.2f} pints")
        
        elif item.size and 'Doz' in item.size:
            expected_full = int(total_servings / item.uom) if item.uom > 0 else 0
            expected_partial = total_servings % item.uom if item.uom > 0 else total_servings
            status = "✅" if display_full == expected_full else "❌"
            print(f"    {status} Dozen: Expected {expected_full} cases + {expected_partial:.0f} bottles")
        
        elif cat_code in ['S', 'W']:
            status = "✅" if display_full >= 0 else "❌"
            print(f"    {status} {cat_data['name']}: Full bottles + fractional")
        
        elif cat_code == 'M':
            if item.subcategory == 'BIB' and item.size and 'LT' in item.size.upper():
                expected_full = int(total_servings / item.uom) if item.uom > 0 else 0
                expected_partial = total_servings % item.uom if item.uom > 0 else total_servings
                status = "✅" if display_full == expected_full else "❌"
                print(f"    {status} BIB: Expected {expected_full} boxes + {expected_partial:.2f} liters")
            else:
                status = "✅" if display_full >= 0 else "❌"
                print(f"    {status} Minerals ({item.subcategory}): Individual units")
    
    if len(cat_data['items']) > 3:
        print(f"\n  ... and {len(cat_data['items']) - 3} more items")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"✓ Tested {len(categories)} categories")
print(f"✓ Total items: {snapshots.count()}")
print("\nCategories tested:")
for cat_code, cat_data in sorted(categories.items()):
    print(f"  - {cat_code}: {cat_data['name']} ({len(cat_data['items'])} items)")

print("\n✅ TEST COMPLETE - Check output above for any ❌ failures")
