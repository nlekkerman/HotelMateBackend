"""
Step 3: Create September 2025 Stocktake
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from hotel.models import Hotel

print("=" * 80)
print("STEP 3: CREATE SEPTEMBER 2025 STOCKTAKE")
print("=" * 80)
print()

hotel = Hotel.objects.first()
print(f"Hotel: {hotel.name}")
print()

# Get September period
sept_period = StockPeriod.objects.get(
    hotel=hotel,
    period_name="September 2025"
)
print(f"✓ September Period found (ID: {sept_period.id})")
print()

# Check for existing stocktake
existing = Stocktake.objects.filter(
    hotel=hotel,
    period_start__year=2025,
    period_start__month=9
).first()

if existing:
    print(f"⚠️  Stocktake already exists (ID: {existing.id})")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    existing.delete()
    print("✓ Deleted existing stocktake")
    print()

# Create stocktake
stocktake = Stocktake.objects.create(
    hotel=hotel,
    period_start=sept_period.start_date,
    period_end=sept_period.end_date,
    status='DRAFT',
    notes='September 2025 stocktake - Ready for line items'
)

print(f"✅ Created Stocktake (ID: {stocktake.id})")
print(f"  Period: {stocktake.period_start} to {stocktake.period_end}")
print(f"  Status: {stocktake.status}")
print()

print("=" * 80)
print("✅ STEP 3 COMPLETE - Stocktake created")
print("=" * 80)
print()
print("NEXT: Run step4 to create StocktakeLine items")
