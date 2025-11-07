"""
Check stock data in database
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockItem, StockSnapshot
from hotel.models import Hotel


hotel = Hotel.objects.first()

print(f"🏨 Hotel: {hotel.name}")
print(f"\n📦 StockItem Records: {StockItem.objects.filter(hotel=hotel).count()}")
print(f"📸 StockSnapshot Records: {StockSnapshot.objects.filter(hotel=hotel).count()}")

# Check if any items exist
items = StockItem.objects.filter(hotel=hotel)[:5]
print(f"\n🔍 Sample Items:")
for item in items:
    print(f"  - {item.sku}: {item.name}")

# Check if any snapshots exist
snapshots = StockSnapshot.objects.all()[:5]
print(f"\n📸 Sample Snapshots:")
for snap in snapshots:
    print(f"  - {snap.item.sku}: full={snap.closing_full_units}, partial={snap.closing_partial_units}, value=€{snap.closing_stock_value:.2f}, period={snap.period}")
