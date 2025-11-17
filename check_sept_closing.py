"""
Check September closing stock values
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod
from hotel.models import Hotel

hotel = Hotel.objects.first()
sept = StockPeriod.objects.get(hotel=hotel, year=2025, month=9, period_type='MONTHLY')

snaps = StockSnapshot.objects.filter(period=sept).select_related('item', 'item__category')

print(f"\n{'='*80}")
print(f"SEPTEMBER 2025 CLOSING STOCK CHECK")
print(f"{'='*80}\n")

total = snaps.count()
with_full = snaps.filter(closing_full_units__gt=0).count()
with_partial = snaps.filter(closing_partial_units__gt=0).count()
with_value = snaps.filter(closing_stock_value__gt=Decimal('0')).count()

print(f"Total snapshots: {total}")
print(f"With closing_full_units > 0: {with_full}")
print(f"With closing_partial_units > 0: {with_partial}")
print(f"With closing_stock_value > 0: {with_value}\n")

print("Sample items:")
print("-" * 80)

samples = snaps.filter(item__sku__in=['B0070', 'B0085', 'B0012', 'D0004', 'S0610'])
for snap in samples:
    cat = snap.item.category.code
    print(f"{snap.item.sku:<10} {snap.item.name:<40} [{cat}]")
    print(f"  Closing: {snap.closing_full_units} full, {snap.closing_partial_units} partial")
    print(f"  Value: €{snap.closing_stock_value}\n")

print(f"{'='*80}\n")
