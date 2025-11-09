"""
Test September 2025 Stocktake Data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake
from decimal import Decimal

september = Stocktake.objects.get(id=8)

print("\n" + "=" * 80)
print("SEPTEMBER 2025 STOCKTAKE TEST")
print("=" * 80)

print(f"\n📅 Period: {september.period_start} to {september.period_end}")
print(f"Status: {september.status}")
print(f"Hotel: {september.hotel.name}")

# Get category totals
print("\n" + "=" * 80)
print("STOCK COUNT BY CATEGORY")
print("=" * 80)

categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

total_items = 0
total_counted = 0

for code, name in categories.items():
    lines = september.lines.filter(item__category__code=code)
    counted = lines.exclude(
        counted_full_units=0,
        counted_partial_units=0
    ).count()
    
    print(f"\n{code} - {name}:")
    print(f"   Total items: {lines.count()}")
    print(f"   Items counted: {counted}")
    print(f"   Items at zero: {lines.count() - counted}")
    
    total_items += lines.count()
    total_counted += counted
    
    # Show a few examples
    if counted > 0:
        print(f"   Examples:")
        for line in lines.exclude(
            counted_full_units=0,
            counted_partial_units=0
        )[:3]:
            print(f"      {line.item.sku} - {line.item.name}: "
                  f"{line.counted_full_units} + {line.counted_partial_units}")

print("\n" + "=" * 80)
print("TOTALS")
print("=" * 80)
print(f"Total items: {total_items}")
print(f"Items with counts: {total_counted}")
print(f"Items at zero: {total_items - total_counted}")

# Financial summary
print("\n" + "=" * 80)
print("FINANCIAL SUMMARY")
print("=" * 80)
print(f"Total COGS:  €{september.total_cogs:>12,.2f}")
print(f"Total Revenue: €{september.total_revenue:>12,.2f}")

if september.total_revenue > 0:
    gross_profit = september.total_revenue - september.total_cogs
    print(f"Gross Profit:  €{gross_profit:>12,.2f}")

if september.gross_profit_percentage:
    print(f"GP%:           {september.gross_profit_percentage:>12.2f}%")
if september.pour_cost_percentage:
    print(f"Pour Cost%:    {september.pour_cost_percentage:>12.2f}%")

# Verification checks
print("\n" + "=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)

# Check some specific items from the spreadsheet
test_items = [
    ('D1258', Decimal('6.00'), Decimal('39.75')),
    ('B0070', Decimal('0.00'), Decimal('145.00')),
    ('S0610', Decimal('45.00'), Decimal('0.80')),
    ('M0123', Decimal('0.00'), Decimal('580.00')),
    ('W2108', Decimal('50.80'), Decimal('0.00')),
]

all_correct = True
for sku, expected_full, expected_partial in test_items:
    try:
        line = september.lines.get(item__sku=sku)
        matches = (
            line.counted_full_units == expected_full and
            line.counted_partial_units == expected_partial
        )
        status = "✅" if matches else "❌"
        print(f"{status} {sku}: {line.counted_full_units} + "
              f"{line.counted_partial_units} "
              f"(expected {expected_full} + {expected_partial})")
        if not matches:
            all_correct = False
    except:
        print(f"❌ {sku}: NOT FOUND")
        all_correct = False

print("\n" + "=" * 80)
if all_correct:
    print("✅ ALL VERIFICATION CHECKS PASSED!")
else:
    print("⚠️  SOME CHECKS FAILED - Please review")
print("=" * 80 + "\n")
