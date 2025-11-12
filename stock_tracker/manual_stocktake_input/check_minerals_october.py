"""
List all Minerals (M) closing stock values for October
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

print("MINERALS (M) - OCTOBER CLOSING STOCK")
print("=" * 80)

snapshots = StockSnapshot.objects.filter(
    period=oct_period,
    item__sku__startswith='M'
).select_related('item').order_by('item__sku')

total = Decimal('0.00')
for snap in snapshots:
    if snap.closing_stock_value > 0 or snap.closing_full_units > 0 or snap.closing_partial_units > 0:
        print(f"{snap.item.sku:20s}: {snap.closing_full_units:>6.2f} cases + "
              f"{snap.closing_partial_units:>7.4f} bottles = €{snap.closing_stock_value:>8.2f}")
        total += snap.closing_stock_value

print("=" * 80)
print(f"{'TOTAL':20s}: €{total:.2f}")
print()
print("Expected: €3,062.43")
print(f"Difference: €{total - Decimal('3062.43'):.2f}")
