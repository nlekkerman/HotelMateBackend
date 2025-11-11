"""
Check what stock periods exist in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from hotel.models import Hotel

print("=" * 80)
print("CHECKING EXISTING STOCK PERIODS")
print("=" * 80)
print()

hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"🏨 Hotel: {hotel.name}")
print()

# Get all periods
periods = StockPeriod.objects.filter(hotel=hotel).order_by('-year', '-month')

print(f"Total Periods: {periods.count()}")
print()

if periods.count() == 0:
    print("❌ No periods found!")
else:
    print("=" * 80)
    print("EXISTING PERIODS:")
    print("=" * 80)
    
    for period in periods:
        print(f"\n📅 Period ID: {period.id}")
        print(f"   Name: {period.period_name}")
        print(f"   Year: {period.year}, Month: {period.month}")
        print(f"   Type: {period.period_type}")
        print(f"   Dates: {period.start_date} to {period.end_date}")
        print(f"   Status: {'CLOSED ✓' if period.is_closed else 'OPEN'}")
        
        # Check for stocktake
        stocktake = Stocktake.objects.filter(
            hotel=hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).first()
        
        if stocktake:
            print(f"   Stocktake: ID {stocktake.id}, Status: {stocktake.status}, Lines: {stocktake.lines.count()}")
        else:
            print(f"   Stocktake: None")

print()
print("=" * 80)
