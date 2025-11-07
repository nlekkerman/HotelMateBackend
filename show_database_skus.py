"""
Show actual database SKUs for all categories
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockItem
from hotel.models import Hotel


hotel = Hotel.objects.first()

categories = ['D', 'B', 'S', 'W', 'M']

for cat in categories:
    items = StockItem.objects.filter(hotel=hotel, category_id=cat).order_by('sku')
    print(f"\n{cat} Category ({items.count()} items):")
    for item in items:
        full = item.current_full_units or 0
        partial = item.current_partial_units or 0
        value = item.total_stock_value or 0
        print(f"  {item.sku:<20} {item.name:<50} full={full:>6} partial={partial:>8} value=€{value:>10.2f}")
