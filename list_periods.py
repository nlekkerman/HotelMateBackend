"""
List all existing periods
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from stock_tracker.models import StockPeriod
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}\n")

periods = StockPeriod.objects.filter(hotel=hotel).order_by('-year', '-month')

print("Existing Periods:")
for p in periods:
    print(f"  ID: {p.id} | {p.period_name} | {p.start_date} to {p.end_date} | Closed: {p.is_closed}")
