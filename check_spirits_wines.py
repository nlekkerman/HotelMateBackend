"""
Check Spirits and Wines discrepancy
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod
from hotel.models import Hotel
from decimal import Decimal


hotel = Hotel.objects.first()
period = StockPeriod.objects.get(hotel=hotel, year=2024, month=10)

print("=" * 70)
print("SPIRITS & WINES ANALYSIS")
print("=" * 70)

# Get Spirits snapshots
spirits = StockSnapshot.objects.filter(
    hotel=hotel, 
    period=period, 
    item__category__code='S'
).select_related('item').order_by('item__sku')

# Get Wines snapshots
wines = StockSnapshot.objects.filter(
    hotel=hotel, 
    period=period, 
    item__category__code='W'
).select_related('item').order_by('item__sku')

print(f"\n🥃 SPIRITS:")
print(f"  Count: {spirits.count()}")
spirits_total = sum(s.closing_stock_value for s in spirits)
print(f"  Database Total: €{spirits_total:,.2f}")
print(f"  Excel Total:    €11,063.66")
print(f"  Difference:     €{spirits_total - Decimal('11063.66'):,.2f}")

print(f"\n  Breakdown:")
for spirit in spirits:
    print(f"    {spirit.item.sku:<20} {spirit.item.name:<50} €{spirit.closing_stock_value:>10.2f}")

print(f"\n🍷 WINES:")
print(f"  Count: {wines.count()}")
wines_total = sum(w.closing_stock_value for w in wines)
print(f"  Database Total: €{wines_total:,.2f}")
print(f"  Excel Total:    €5,580.35")
print(f"  Difference:     €{wines_total - Decimal('5580.35'):,.2f}")

print(f"\n  Breakdown:")
for wine in wines:
    print(f"    {wine.item.sku:<20} {wine.item.name:<50} €{wine.closing_stock_value:>10.2f}")

print(f"\n" + "=" * 70)
print(f"SUMMARY:")
print(f"  Spirits: Database €{spirits_total:,.2f} vs Excel €11,063.66 = diff €{spirits_total - Decimal('11063.66'):,.2f}")
print(f"  Wines:   Database €{wines_total:,.2f} vs Excel €5,580.35 = diff €{wines_total - Decimal('5580.35'):,.2f}")
print(f"=" * 70)
