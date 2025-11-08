"""
Verify October 2024 stocktake matches spreadsheet values.

Expected values from spreadsheet:
    Draught Beers       €5,311.62
    Bottled Beers       €2,288.46
    Spirits             €11,063.66
    Minerals/Syrups     €3,062.43
    Wine                €5,580.35
    TOTAL               €27,306.51
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("OCTOBER 2025 STOCKTAKE VERIFICATION")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Find October 2025 period
try:
    oct_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2025,
        month=10,
        period_name="October 2025"
    )
    print(f"✓ Found October 2025 period (ID: {oct_period.id})")
    print(f"  Status: {'CLOSED' if oct_period.is_closed else 'OPEN'}")
    print(f"  Dates: {oct_period.start_date} to {oct_period.end_date}")
except StockPeriod.DoesNotExist:
    print("❌ October 2025 period not found!")
    print("\nAvailable periods:")
    for period in StockPeriod.objects.filter(hotel=hotel).order_by('-start_date')[:10]:
        print(f"  - {period.period_name} (ID: {period.id})")
    exit(1)

print()

# Get all snapshots for October
snapshots = StockSnapshot.objects.filter(
    hotel=hotel,
    period=oct_period
).select_related('item', 'item__category')

if not snapshots.exists():
    print("❌ No snapshots found for October 2024!")
    exit(1)

print(f"✓ Found {snapshots.count()} stock snapshots")
print()

# Calculate totals by category - October 2025 values
categories = {
    'D': {'name': 'Draught Beers', 'expected': Decimal('5311.62')},
    'B': {'name': 'Bottled Beers', 'expected': Decimal('2288.46')},
    'S': {'name': 'Spirits', 'expected': Decimal('11063.66')},
    'M': {'name': 'Minerals/Syrups', 'expected': Decimal('3062.43')},
    'W': {'name': 'Wine', 'expected': Decimal('5580.35')}
}

print("=" * 100)
print("CATEGORY BREAKDOWN")
print("=" * 100)
print()

total_calculated = Decimal('0.00')
total_expected = Decimal('0.00')

print(f"{'Category':<20} {'Items':<10} {'Calculated':<15} {'Expected':<15} {'Difference':<15} {'Status'}")
print("-" * 100)

for cat_code, cat_info in categories.items():
    cat_snapshots = snapshots.filter(item__category_id=cat_code)
    item_count = cat_snapshots.count()
    
    # Calculate total value for category
    cat_total = Decimal('0.00')
    for snap in cat_snapshots:
        cat_total += snap.closing_stock_value
    
    expected = cat_info['expected']
    difference = cat_total - expected
    
    total_calculated += cat_total
    total_expected += expected
    
    # Determine status (allow €1 tolerance)
    if abs(difference) <= 1:
        status = "✅ MATCH"
    elif abs(difference) <= 10:
        status = "⚠️  CLOSE"
    else:
        status = "❌ DIFF"
    
    print(f"{cat_info['name']:<20} {item_count:<10} €{cat_total:>13.2f} €{expected:>13.2f} €{difference:>13.2f} {status}")

print("-" * 100)
total_diff = total_calculated - total_expected
if abs(total_diff) <= 1:
    status = "✅ MATCH"
elif abs(total_diff) <= 10:
    status = "⚠️  CLOSE"
else:
    status = "❌ DIFF"

print(f"{'TOTAL':<20} {snapshots.count():<10} €{total_calculated:>13.2f} €{total_expected:>13.2f} €{total_diff:>13.2f} {status}")

print()
print("=" * 100)
print("DETAILED ANALYSIS")
print("=" * 100)
print()

# Show items with largest values in each category
for cat_code, cat_info in categories.items():
    cat_snapshots = snapshots.filter(item__category_id=cat_code).order_by('-closing_stock_value')[:5]
    
    if cat_snapshots.exists():
        print(f"\n{cat_info['name']} - Top 5 Items:")
        print(f"{'SKU':<15} {'Name':<40} {'Value':<15}")
        print("-" * 70)
        for snap in cat_snapshots:
            print(f"{snap.item.sku:<15} {snap.item.name[:39]:<40} €{snap.closing_stock_value:>13.2f}")

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print()

if abs(total_diff) <= 1:
    print("✅ SUCCESS! October 2025 stocktake matches spreadsheet (within €1)")
    print(f"\n   Database Total:    €{total_calculated:.2f}")
    print(f"   Spreadsheet Total: €{total_expected:.2f}")
    print(f"   Difference:        €{total_diff:.2f}")
elif abs(total_diff) <= 10:
    print("⚠️  CLOSE! October 2025 stocktake is close to spreadsheet (within €10)")
    print(f"\n   Database Total:    €{total_calculated:.2f}")
    print(f"   Spreadsheet Total: €{total_expected:.2f}")
    print(f"   Difference:        €{total_diff:.2f}")
else:
    print(f"❌ MISMATCH! October 2025 stocktake differs by €{abs(total_diff):.2f}")
    print(f"\n   Database Total:    €{total_calculated:.2f}")
    print(f"   Spreadsheet Total: €{total_expected:.2f}")
    print(f"   Difference:        €{total_diff:.2f}")
    print("\n   Possible causes:")
    print("   1. Missing items in database")
    print("   2. Different unit costs")
    print("   3. Different stock quantities")
    print("   4. Calculation method differences")

print()
print("=" * 100)
