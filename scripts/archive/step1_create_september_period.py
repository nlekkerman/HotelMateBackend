"""
Step 1: Create September 2025 StockPeriod
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod
from hotel.models import Hotel
from decimal import Decimal

print("=" * 80)
print("STEP 1: CREATE SEPTEMBER 2025 STOCK PERIOD")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Create September 2025 period
sept_period, created = StockPeriod.objects.get_or_create(
    hotel=hotel,
    period_name="September 2025",
    defaults={
        'period_type': 'MONTHLY',
        'start_date': date(2025, 9, 1),
        'end_date': date(2025, 9, 30),
        'year': 2025,
        'month': 9,
        'is_closed': False,
        'manual_sales_amount': Decimal('51207.00'),
        'notes': 'September 2025 period - Ready for snapshots'
    }
)

if created:
    print(f"✅ Created September 2025 Period (ID: {sept_period.id})")
else:
    print(f"✓ September 2025 Period already exists (ID: {sept_period.id})")

print(f"  Period: {sept_period.start_date} to {sept_period.end_date}")
print(f"  Type: {sept_period.period_type}")
print(f"  Status: {'CLOSED' if sept_period.is_closed else 'OPEN'}")
print(f"  Sales: €{sept_period.manual_sales_amount:,.2f}")
print()
print("=" * 80)
print("✅ STEP 1 COMPLETE - Period created")
print("=" * 80)
print()
print("NEXT: Run script to create StockSnapshots")
