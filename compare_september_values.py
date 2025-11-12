"""
Compare September closing stock against expected values
Find the €338.71 difference
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()

sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

print("=" * 100)
print("SEPTEMBER CLOSING STOCK - DETAILED BREAKDOWN")
print("=" * 100)
print()

# Expected values from September stocktake HTML you provided
expected_values = {
    'Bottled Beer': Decimal('3079.03'),
    'Draught Beer': Decimal('5304.05'),  # Was 5304.05 in HTML
    'Minerals & Syrups': Decimal('2880.09'),
    'Spirits': Decimal('10406.36'),
    'Wine': Decimal('4466.14'),  # Just updated
}

snapshots = StockSnapshot.objects.filter(period=sept_period)

# Group by category
actual_values = {}
for snapshot in snapshots:
    cat = snapshot.item.category.name if snapshot.item.category else 'Uncategorized'
    if cat not in actual_values:
        actual_values[cat] = Decimal('0.00')
    actual_values[cat] += snapshot.closing_stock_value

print(f"{'Category':<30s} {'Actual':>12s} {'Expected':>12s} {'Difference':>12s}")
print("-" * 100)

total_actual = Decimal('0.00')
total_expected = Decimal('0.00')
total_diff = Decimal('0.00')

for cat in sorted(actual_values.keys()):
    actual = actual_values[cat]
    expected = expected_values.get(cat, Decimal('0.00'))
    diff = actual - expected
    
    total_actual += actual
    total_expected += expected
    total_diff += diff
    
    status = ""
    if abs(diff) > Decimal('0.10'):
        status = " ⚠️"
    elif abs(diff) > Decimal('0.01'):
        status = " ⚠️"
    
    print(f"{cat:<30s} €{actual:>10,.2f} €{expected:>10,.2f} €{diff:>10,.2f}{status}")

print("-" * 100)
print(f"{'TOTAL':<30s} €{total_actual:>10,.2f} €{total_expected:>10,.2f} €{total_diff:>10,.2f}")
print()

print("Expected from September HTML: €21,669.53 (before Wine)")
print("Wine added: €4,466.14")
print("Expected total: €26,135.67")
print(f"Actual total: €{total_actual:,.2f}")
print(f"Difference: €{total_actual - Decimal('26135.67'):.2f}")
print()

# Check for differences
if abs(total_diff) > Decimal('1.00'):
    print("INVESTIGATING DIFFERENCES:")
    print()
    
    for cat in sorted(actual_values.keys()):
        diff = actual_values[cat] - expected_values.get(cat, Decimal('0.00'))
        if abs(diff) > Decimal('0.10'):
            print(f"{cat}: €{diff:.2f} difference")
            print(f"  Actual: €{actual_values[cat]:.2f}")
            print(f"  Expected: €{expected_values.get(cat, Decimal('0.00')):.2f}")
            print()

print("=" * 100)
