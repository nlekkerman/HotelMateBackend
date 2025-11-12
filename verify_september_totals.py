"""
Verify September closing stock totals after Wine update
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

print("=" * 80)
print("SEPTEMBER 2025 CLOSING STOCK - UPDATED WITH WINE")
print("=" * 80)
print()

snapshots = StockSnapshot.objects.filter(period=sept_period)

# Group by category
categories = {}
for snapshot in snapshots:
    cat = snapshot.item.category.name if snapshot.item.category else 'Uncategorized'
    if cat not in categories:
        categories[cat] = Decimal('0.00')
    categories[cat] += snapshot.closing_stock_value

# Display by category
for cat in sorted(categories.keys()):
    print(f"{cat:30s}: €{categories[cat]:>10,.2f}")

total = sum(categories.values())
print("-" * 80)
print(f"{'TOTAL':30s}: €{total:>10,.2f}")
print()
print(f"Previous total (no Wine): €21,669.53")
print(f"Wine added: €4,466.14")
print(f"Expected new total: €26,135.67")
print()
if abs(total - Decimal('26135.67')) < Decimal('1.00'):
    print("✅ Total matches expected!")
else:
    difference = total - Decimal('26135.67')
    print(f"⚠️  Difference: €{difference:.2f}")
print()
print("=" * 80)
