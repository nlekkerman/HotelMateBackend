"""
Check item costs
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel

hotel = Hotel.objects.first()
items = StockItem.objects.filter(hotel=hotel, active=True)

print(f"\n{'='*80}")
print("ITEM COST CHECK")
print(f"{'='*80}\n")

total = items.count()
with_unit_cost = items.filter(unit_cost__gt=Decimal('0')).count()

print(f"Total items: {total}")
print(f"With unit_cost > 0: {with_unit_cost}\n")

print("Sample items:")
print("-" * 80)

samples = items.filter(sku__in=['B0070', 'B0085', 'D0004', 'S0610', 'W2104'])
for item in samples:
    print(f"{item.sku:<10} {item.name:<40}")
    print(f"  unit_cost: €{item.unit_cost}\n")

print(f"{'='*80}\n")
