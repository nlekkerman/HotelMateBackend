"""
Create October 2025 Stocktake from existing Period data.
This will allow November 2025 to have opening stock.
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine, StockSnapshot
from hotel.models import Hotel

print("=" * 100)
print("CREATE OCTOBER 2025 STOCKTAKE FROM PERIOD")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name}")
print()

# Find October 2025 Period
print("Searching for October 2025 Period...")
oct_period = StockPeriod.objects.filter(
    hotel=hotel,
    period_name="October 2025"
).first()

if not oct_period:
    print("❌ October 2025 Period not found!")
    print("\nAvailable periods:")
    for period in StockPeriod.objects.filter(hotel=hotel).order_by('-start_date')[:10]:
        print(f"  - {period.period_name} ({period.start_date} to {period.end_date}) - Closed: {period.is_closed}")
    exit(1)

print(f"✓ Found October 2025 Period")
print(f"  Period ID: {oct_period.id}")
print(f"  Period Name: {oct_period.period_name}")
print(f"  Dates: {oct_period.start_date} to {oct_period.end_date}")
print(f"  Is Closed: {oct_period.is_closed}")
print(f"  Snapshots: {oct_period.snapshots.count()}")
print()

# Check if stocktake already exists
existing_stocktake = Stocktake.objects.filter(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date
).first()

if existing_stocktake:
    print(f"⚠️  October 2025 Stocktake already exists (ID: {existing_stocktake.id})")
    response = input("Delete and recreate? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        exit(0)
    
    print(f"Deleting existing stocktake {existing_stocktake.id}...")
    existing_stocktake.delete()
    print("✓ Deleted")
    print()

# Create Stocktake
print("Creating October 2025 Stocktake...")
stocktake = Stocktake.objects.create(
    hotel=hotel,
    period_start=oct_period.start_date,
    period_end=oct_period.end_date,
    status='APPROVED',
    approved_at=datetime.now(),
    notes="Created from October 2025 Period data"
)
print(f"✓ Created Stocktake ID: {stocktake.id}")
print()

# Get all snapshots from period
snapshots = StockSnapshot.objects.filter(
    period=oct_period
).select_related('item', 'item__category')

print(f"Creating {snapshots.count()} stocktake lines from period snapshots...")
print()

created_count = 0
for snapshot in snapshots:
    # Create stocktake line with closing stock as counted stock
    StocktakeLine.objects.create(
        stocktake=stocktake,
        item=snapshot.item,
        opening_qty=snapshot.closing_partial_units,  # Will be 0 if no previous period
        purchases=0,
        sales=0,
        waste=0,
        transfers_in=0,
        transfers_out=0,
        adjustments=0,
        counted_full_units=snapshot.closing_full_units,
        counted_partial_units=snapshot.closing_partial_units,
        valuation_cost=snapshot.unit_cost
    )
    created_count += 1
    
    if created_count % 50 == 0:
        print(f"  Created {created_count} lines...")

print(f"✓ Created {created_count} stocktake lines")
print()

# Summary
print("=" * 100)
print("SUCCESS!")
print("=" * 100)
print()
print(f"✅ October 2025 Stocktake created (ID: {stocktake.id})")
print(f"   Status: {stocktake.status}")
print(f"   Lines: {stocktake.lines.count()}")
print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
print()
print("=" * 100)
print("NEXT STEPS")
print("=" * 100)
print("1. November 2025 Stocktake should now show opening stock from October")
print("2. Verify opening stock in November stocktake")
print("3. Check that values match October closing")
print()
print("Run this to verify:")
print("  python -c \"import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings'); django.setup(); from stock_tracker.models import Stocktake; from stock_tracker.stock_serializers import StocktakeSerializer; nov = Stocktake.objects.get(id=4); data = StocktakeSerializer(nov).data; print('November Opening Lines:', len([l for l in data['lines'] if float(l['opening_qty']) > 0]))\"")
print("=" * 100)
