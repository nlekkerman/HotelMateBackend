"""
Create snapshots for November 2025 period
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, StockItem
from hotel.models import Hotel

hotel = Hotel.objects.first()
nov_period = StockPeriod.objects.get(hotel=hotel, year=2025, month=11, period_type='MONTHLY')

print(f"Creating snapshots for November period (ID: {nov_period.id})...")

items = StockItem.objects.filter(hotel=hotel)
print(f"Found {items.count()} stock items")

created = 0
for item in items:
    snapshot, was_created = StockSnapshot.objects.get_or_create(
        hotel=hotel,
        period=nov_period,
        item=item,
        defaults={
            'closing_full_units': 0,
            'closing_partial_units': 0,
            'unit_cost': item.unit_cost,
            'cost_per_serving': item.cost_per_serving,
            'closing_stock_value': 0
        }
    )
    if was_created:
        created += 1

print(f"✅ Created {created} new snapshots")
print(f"Total snapshots in November: {StockSnapshot.objects.filter(period=nov_period).count()}")
