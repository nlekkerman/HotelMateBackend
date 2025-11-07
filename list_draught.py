"""
List all draught beers in database to find discrepancies
"""
import os
import sys
import django
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot
from hotel.models import Hotel

hotel = Hotel.objects.first()
period = StockPeriod.objects.filter(hotel=hotel, year=2024, month=10).first()

snapshots = StockSnapshot.objects.filter(
    hotel=hotel,
    period=period,
    item__category_id='D'
).select_related('item').order_by('item__sku')

print("ALL DRAUGHT BEERS IN DATABASE:")
print("=" * 80)
total = 0
for s in snapshots:
    print(f"{s.item.sku}: {s.item.name} = €{s.closing_stock_value:.2f}")
    total += s.closing_stock_value

print("=" * 80)
print(f"TOTAL: €{total:.2f}")
