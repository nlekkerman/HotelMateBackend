"""Quick script to reset purchases to zero"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine
from decimal import Decimal

# Reset all purchases and waste for November stocktake
lines = StocktakeLine.objects.filter(
    stocktake__period_start__year=2025,
    stocktake__period_start__month=11
)

print(f"Found {lines.count()} lines in November stocktake")
print(f"Lines with purchases > 0: {lines.filter(purchases__gt=0).count()}")

# Update
updated = lines.update(purchases=Decimal('0'), waste=Decimal('0'))
print(f"✅ Reset {updated} lines - purchases and waste now 0")
