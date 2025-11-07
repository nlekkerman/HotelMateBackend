"""
Check what SKUs exist in the database
"""

import os
import sys
import django
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel

hotel = Hotel.objects.first()

print("="*60)
print("EXISTING SKUs IN DATABASE")
print("="*60)

categories = ['B', 'S', 'W', 'M']

for cat in categories:
    items = StockItem.objects.filter(hotel=hotel, category__code=cat).order_by('sku')
    print(f"\n{cat} - {items.count()} items:")
    for item in items:
        print(f"  {item.sku}: {item.name}")
