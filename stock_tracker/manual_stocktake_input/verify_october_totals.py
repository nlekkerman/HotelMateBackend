"""
Verify October closing stock totals by category
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()
oct_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=10, period_type='MONTHLY'
)

print("=" * 80)
print("OCTOBER 2025 CLOSING STOCK BY CATEGORY")
print("=" * 80)
print()

# Get all snapshots
snapshots = StockSnapshot.objects.filter(period=oct_period).select_related('item')

# Categorize by SKU prefix
categories = {
    'D': {'name': 'Draught Beer', 'total': Decimal('0.00')},
    'B': {'name': 'Bottled Beer', 'total': Decimal('0.00')},
    'S': {'name': 'Spirits', 'total': Decimal('0.00')},
    'M': {'name': 'Minerals', 'total': Decimal('0.00')},
    'W': {'name': 'Wine', 'total': Decimal('0.00')},
}

for snap in snapshots:
    prefix = snap.item.sku[0]
    if prefix in categories:
        categories[prefix]['total'] += snap.closing_stock_value

# Display totals
grand_total = Decimal('0.00')
for prefix in ['D', 'B', 'S', 'M', 'W']:
    cat = categories[prefix]
    print(f"{cat['name']:20s}: €{cat['total']:>10.2f}")
    grand_total += cat['total']

print("-" * 80)
print(f"{'GRAND TOTAL':20s}: €{grand_total:>10.2f}")
print()

# Expected totals
expected = {
    'D': Decimal('5311.62'),
    'B': Decimal('2288.46'),
    'S': Decimal('11063.66'),
    'M': Decimal('3062.43'),
    'W': Decimal('5580.35'),
}
expected_total = sum(expected.values())

print("EXPECTED TOTALS:")
for prefix in ['D', 'B', 'S', 'M', 'W']:
    cat = categories[prefix]
    exp = expected[prefix]
    diff = cat['total'] - exp
    status = "✅" if abs(diff) < Decimal('0.10') else "⚠️"
    print(f"{status} {cat['name']:20s}: €{exp:>10.2f} (diff: €{diff:>8.2f})")

print("-" * 80)
total_diff = grand_total - expected_total
status = "✅" if abs(total_diff) < Decimal('1.00') else "⚠️"
print(f"{status} {'EXPECTED TOTAL':20s}: €{expected_total:>10.2f} (diff: €{total_diff:>8.2f})")
print()
print("=" * 80)
