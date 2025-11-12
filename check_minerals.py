"""
Check Minerals & Syrups closing stock values
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
print("MINERALS & SYRUPS - SEPTEMBER CLOSING STOCK")
print("=" * 100)
print()

snapshots = StockSnapshot.objects.filter(
    period=sept_period,
    item__category__name='Minerals & Syrups'
).order_by('item__sku')

print(f"{'SKU':<20s} {'Name':<50s} {'Value':>12s}")
print("-" * 100)

total = Decimal('0.00')
for snapshot in snapshots:
    if snapshot.closing_stock_value > 0:
        print(f"{snapshot.item.sku:<20s} {snapshot.item.name:<50s} €{snapshot.closing_stock_value:>10.2f}")
        total += snapshot.closing_stock_value

print("-" * 100)
print(f"{'TOTAL':<71s} €{total:>10.2f}")
print()
print(f"Expected (from HTML): €2,880.09")
print(f"Difference: €{total - Decimal('2880.09'):.2f}")
print()
print("=" * 100)
