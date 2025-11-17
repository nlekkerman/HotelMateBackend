"""
Summary of what was updated for September closing stock
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockSnapshot, StockPeriod
from hotel.models import Hotel

hotel = Hotel.objects.first()

print(f"\n{'='*80}")
print("SUMMARY: SEPTEMBER CLOSING STOCK RESTORATION")
print(f"{'='*80}\n")

# 1. StockItem - check unit costs
items = StockItem.objects.filter(hotel=hotel, active=True)
items_with_cost = items.filter(unit_cost__gt=Decimal('0'))

print("1. STOCK ITEMS (StockItem model):")
print("-" * 80)
print(f"   Total active items: {items.count()}")
print(f"   Items with unit_cost > 0: {items_with_cost.count()}")
print(f"   Items missing unit_cost: {items.count() - items_with_cost.count()}")
print()

# 2. September Snapshots - check closing stock
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)
sept_snaps = StockSnapshot.objects.filter(period=sept_period)

with_qty = sept_snaps.filter(
    models.Q(closing_full_units__gt=0) | 
    models.Q(closing_partial_units__gt=0)
)
with_value = sept_snaps.filter(closing_stock_value__gt=Decimal('0'))

from django.db import models

print("2. SEPTEMBER SNAPSHOTS (StockSnapshot model):")
print("-" * 80)
print(f"   Total snapshots: {sept_snaps.count()}")
print(f"   With closing quantities > 0: {with_qty.count()}")
print(f"   With closing_stock_value > 0: {with_value.count()}")
print(f"   Total September value: €{sept_snaps.aggregate(models.Sum('closing_stock_value'))['closing_stock_value__sum']:,.2f}")
print()

print("3. WHAT WAS UPDATED:")
print("-" * 80)
print("   ✅ StockItem.unit_cost - imported from October Excel (249 items)")
print("   ✅ StockSnapshot.closing_full_units - copied from current stock")
print("   ✅ StockSnapshot.closing_partial_units - copied from current stock")
print("   ✅ StockSnapshot.closing_stock_value - calculated from qty × cost")
print()

print("4. SAMPLE DATA:")
print("-" * 80)
samples = sept_snaps.filter(
    item__sku__in=['B0070', 'D1258', 'S0610', 'W2104', 'M0140']
).select_related('item')

for snap in samples:
    print(f"   {snap.item.sku} - {snap.item.name}")
    print(f"      Item unit_cost: €{snap.item.unit_cost}")
    print(f"      Closing: {snap.closing_full_units} full + "
          f"{snap.closing_partial_units} partial")
    print(f"      Value: €{snap.closing_stock_value}")
    print()

print(f"{'='*80}\n")
