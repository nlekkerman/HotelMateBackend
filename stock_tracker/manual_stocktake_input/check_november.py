"""
Check November 2025 period and stocktake status
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel
from datetime import date

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Check for November period
nov_periods = StockPeriod.objects.filter(hotel=hotel, year=2025, month=11)
print(f"November 2025 periods: {nov_periods.count()}")
for p in nov_periods:
    print(f"  ID {p.id}: {p.start_date} to {p.end_date} ({p.period_type})")
    snaps = StockSnapshot.objects.filter(period=p)
    print(f"  Snapshots: {snaps.count()}")
print()

# Check for November stocktake
nov_stocktakes = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=11
)
print(f"November 2025 stocktakes: {nov_stocktakes.count()}")
for st in nov_stocktakes:
    print(f"  ID {st.id}: {st.period_start} to {st.period_end} ({st.status})")
    print(f"  Lines: {st.lines.count()}")
print()

# Create November period if it doesn't exist
if nov_periods.count() == 0:
    print("Creating November 2025 period...")
    from dateutil.relativedelta import relativedelta
    
    nov_period = StockPeriod.objects.create(
        hotel=hotel,
        year=2025,
        month=11,
        start_date=date(2025, 11, 1),
        end_date=date(2025, 11, 30),
        period_type='MONTHLY'
    )
    print(f"✅ Created November period: ID {nov_period.id}")
    print()
    
    # Create snapshots for all items
    from stock_tracker.models import StockItem
    items = StockItem.objects.filter(hotel=hotel)
    print(f"Creating {items.count()} snapshots...")
    
    created = 0
    for item in items:
        StockSnapshot.objects.create(
            hotel=hotel,
            period=nov_period,
            item=item,
            closing_full_units=0,
            closing_partial_units=0,
            unit_cost=item.cost_per_unit,
            cost_per_serving=item.cost_per_serving,
            closing_stock_value=0
        )
        created += 1
    
    print(f"✅ Created {created} snapshots for November")
