import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod

print("\nAll periods in database:")
periods = StockPeriod.objects.filter(hotel_id=1).order_by('-start_date')
for p in periods:
    print(f"  ID={p.id}, {p.period_name}, {p.start_date} to {p.end_date}, closed={p.is_closed}")
