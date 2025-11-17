"""
Set September opening stock to 0 for all items
This is done by ensuring no prior period exists before September
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockSnapshot, StockPeriod
from hotel.models import Hotel

print(f"\n{'='*80}")
print("SETTING SEPTEMBER OPENING STOCK TO ZERO")
print(f"{'='*80}\n")

hotel = Hotel.objects.first()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel, year=2025, month=9, period_type='MONTHLY'
)

print(f"Period: {sept_period.period_name}")
print(f"Date range: {sept_period.start_date} to {sept_period.end_date}\n")

# Check for any periods before September
prior_periods = StockPeriod.objects.filter(
    hotel=hotel,
    end_date__lt=sept_period.start_date
).order_by('-end_date')

if prior_periods.exists():
    print(f"Found {prior_periods.count()} period(s) before September:")
    for p in prior_periods:
        print(f"  - {p.period_name}: {p.start_date} to {p.end_date}")
    print("\nDeleting prior periods to ensure September opening = 0...")
    
    deleted_count = prior_periods.delete()[0]
    print(f"✓ Deleted {deleted_count} records (periods + their snapshots)\n")
else:
    print("✓ No periods exist before September - opening stock is already 0\n")

# Verify September snapshots
sept_snaps = StockSnapshot.objects.filter(period=sept_period)
print(f"September has {sept_snaps.count()} snapshots")
print(f"With closing_stock_value > 0: {sept_snaps.filter(closing_stock_value__gt=Decimal('0')).count()}")

total_closing = sept_snaps.aggregate(
    total=django.db.models.Sum('closing_stock_value')
)['total'] or Decimal('0')

print(f"Total September closing value: €{total_closing:,.2f}\n")

print(f"{'='*80}")
print("COMPLETE")
print(f"{'='*80}")
print("✓ September opening stock = 0 (no prior periods)")
print(f"✓ September closing stock = €{total_closing:,.2f}")
print(f"{'='*80}\n")
