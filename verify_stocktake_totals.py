import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from decimal import Decimal

print("=" * 80)
print("STOCKTAKE VERIFICATION - OCTOBER VS SEPTEMBER")
print("=" * 80)

# Get periods
october = StockPeriod.objects.get(period_name="October 2024")
september = StockPeriod.objects.get(period_name="September 2024")

print(f"\nOctober Period: {october.start_date} to {october.end_date}")
print(f"September Period: {september.start_date} to {september.end_date}")

# Category mapping
categories = {
    'D': 'Draught Beers',
    'B': 'Bottled Beers',
    'S': 'Spirits',
    'M': 'Minerals/Syrups',
    'W': 'Wine'
}

print("\n" + "=" * 80)
print("CATEGORY TOTALS")
print("=" * 80)
print(f"{'Category':<20} {'October':<15} {'September':<15} {'Difference':<15}")
print("-" * 80)

october_grand_total = Decimal('0.00')
september_grand_total = Decimal('0.00')

for code, name in categories.items():
    # October totals
    oct_snapshots = StockSnapshot.objects.filter(
        period=october,
        item__category_id=code
    )
    oct_total = sum(s.closing_stock_value for s in oct_snapshots)
    
    # September totals
    sept_snapshots = StockSnapshot.objects.filter(
        period=september,
        item__category_id=code
    )
    sept_total = sum(s.closing_stock_value for s in sept_snapshots)
    
    difference = oct_total - sept_total
    
    october_grand_total += oct_total
    september_grand_total += sept_total
    
    print(f"{name:<20} €{oct_total:>13,.2f} €{sept_total:>13,.2f} €{difference:>13,.2f}")

print("-" * 80)
difference_total = october_grand_total - september_grand_total
print(f"{'TOTAL':<20} €{october_grand_total:>13,.2f} €{september_grand_total:>13,.2f} €{difference_total:>13,.2f}")

print("\n" + "=" * 80)
print("COMPARISON WITH YOUR DATA")
print("=" * 80)

your_data = {
    'Draught Beers': (Decimal('5311.62'), Decimal('5303.15'), Decimal('8.47')),
    'Bottled Beers': (Decimal('2288.46'), Decimal('3079.04'), Decimal('-790.58')),
    'Spirits': (Decimal('11063.66'), Decimal('10406.35'), Decimal('657.30')),
    'Minerals/Syrups': (Decimal('3062.43'), Decimal('4185.61'), Decimal('-1123.18')),
    'Wine': (Decimal('5580.35'), Decimal('4466.13'), Decimal('1114.21'))
}

print(f"\n{'Category':<20} {'Status':<15} {'DB Oct':<15} {'Your Oct':<15} {'Variance':<15}")
print("-" * 80)

all_match = True
for code, name in categories.items():
    oct_snapshots = StockSnapshot.objects.filter(period=october, item__category_id=code)
    db_oct = sum(s.closing_stock_value for s in oct_snapshots)
    
    your_oct, your_sept, your_diff = your_data[name]
    variance = db_oct - your_oct
    
    if abs(variance) < Decimal('1.00'):
        status = "✓ MATCH"
    else:
        status = "✗ MISMATCH"
        all_match = False
    
    print(f"{name:<20} {status:<15} €{db_oct:>13,.2f} €{your_oct:>13,.2f} €{variance:>13,.2f}")

print("\n" + "=" * 80)
print(f"{'Category':<20} {'Status':<15} {'DB Sept':<15} {'Your Sept':<15} {'Variance':<15}")
print("-" * 80)

for code, name in categories.items():
    sept_snapshots = StockSnapshot.objects.filter(period=september, item__category_id=code)
    db_sept = sum(s.closing_stock_value for s in sept_snapshots)
    
    your_oct, your_sept, your_diff = your_data[name]
    variance = db_sept - your_sept
    
    if abs(variance) < Decimal('1.00'):
        status = "✓ MATCH"
    else:
        status = "✗ MISMATCH"
        all_match = False
    
    print(f"{name:<20} {status:<15} €{db_sept:>13,.2f} €{your_sept:>13,.2f} €{variance:>13,.2f}")

print("\n" + "=" * 80)
if all_match:
    print("✓ ALL DATA MATCHES - READY TO CALCULATE OCTOBER SALES")
else:
    print("✗ SOME DISCREPANCIES FOUND - REVIEW NEEDED")
print("=" * 80)

print("\n" + "=" * 80)
print("INTERPRETATION")
print("=" * 80)
print("\nOctober closing stock represents END OF OCTOBER stocktake")
print("September closing stock represents END OF SEPTEMBER stocktake (= start of October)")
print("\nDifference = October - September")
print("  Positive difference = Stock INCREASED (purchases > sales)")
print("  Negative difference = Stock DECREASED (sales > purchases)")
print("\nTo calculate sales, we need:")
print("  Sales = Opening Stock + Purchases - Closing Stock")
print("  Sales = September Closing + Purchases - October Closing")
