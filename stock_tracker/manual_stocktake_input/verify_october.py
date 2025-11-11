"""
Verify October 2025 objects were created by the script.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake, StocktakeLine
from hotel.models import Hotel

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name if hotel else 'None'}")

# October period
oct_period = StockPeriod.objects.filter(hotel=hotel, year=2025, month=10, period_type='MONTHLY').first()
if not oct_period:
    print("October 2025 period: NOT FOUND")
else:
    snaps = StockSnapshot.objects.filter(period=oct_period)
    print(f"October period ID: {oct_period.id}, snapshots: {snaps.count()}")

# Stocktake for October
stocktake = Stocktake.objects.filter(hotel=hotel, period_start=oct_period.start_date if oct_period else None, period_end=oct_period.end_date if oct_period else None).first()
if not stocktake:
    print("October stocktake: NOT FOUND")
else:
    lines = StocktakeLine.objects.filter(stocktake=stocktake)
    print(f"Stocktake ID: {stocktake.id}, status: {stocktake.status}, lines: {lines.count()}")
    # print totals
    total_opening = sum(line.opening_qty * line.valuation_cost for line in lines)
    print(f"Calculated opening value (sum opening_qty * valuation_cost): €{total_opening:.2f}")

# Also show recent stocktakes
print('\nRecent stocktakes (last 5):')
for st in Stocktake.objects.filter(hotel=hotel).order_by('-created_at')[:5]:
    print(f"  ID {st.id}: {st.period_start} to {st.period_end} ({st.status}) Lines: {st.lines.count()}")
