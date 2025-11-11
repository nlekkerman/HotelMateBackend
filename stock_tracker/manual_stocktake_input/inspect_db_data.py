"""
Inspect current database state for stock periods and snapshots
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake, StocktakeLine
from hotel.models import Hotel

print("=" * 100)
print("DATABASE INSPECTION - STOCK PERIODS & STOCKTAKES")
print("=" * 100)
print()

# Get hotel
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found!")
    exit(1)

print(f"Hotel: {hotel.name} (ID: {hotel.id})")
print()

# List all periods
print("=" * 100)
print("ALL STOCK PERIODS")
print("=" * 100)
periods = StockPeriod.objects.filter(hotel=hotel).order_by('start_date')
print(f"Total periods: {periods.count()}")
print()

for period in periods:
    snapshot_count = StockSnapshot.objects.filter(period=period).count()
    print(f"Period: {period.period_name}")
    print(f"  ID: {period.id}")
    print(f"  Dates: {period.start_date} to {period.end_date}")
    print(f"  Type: {period.period_type}")
    print(f"  Closed: {period.is_closed}")
    print(f"  Snapshots: {snapshot_count}")
    print()

# Check September 2025 specifically
print("=" * 100)
print("SEPTEMBER 2025 DETAILS")
print("=" * 100)

try:
    sept_period = StockPeriod.objects.get(
        hotel=hotel,
        year=2025,
        month=9,
        period_type='MONTHLY'
    )
    print(f"✓ September 2025 found (ID: {sept_period.id})")
    print(f"  Period Name: {sept_period.period_name}")
    print(f"  Dates: {sept_period.start_date} to {sept_period.end_date}")
    print(f"  Closed: {sept_period.is_closed}")
    print()
    
    # Check snapshots
    sept_snapshots = StockSnapshot.objects.filter(period=sept_period)
    print(f"  Total Snapshots: {sept_snapshots.count()}")
    print()
    
    # Calculate category totals
    categories = {
        'D': 'Draught Beer',
        'B': 'Bottled Beer',
        'S': 'Spirits',
        'W': 'Wine',
        'M': 'Minerals/Syrups'
    }
    
    print("  Category Breakdown (Closing Stock Values):")
    print("  " + "-" * 80)
    
    category_totals = {}
    for cat_code, cat_name in categories.items():
        cat_snaps = sept_snapshots.filter(item__category_id=cat_code)
        total_value = sum(snap.closing_stock_value for snap in cat_snaps)
        category_totals[cat_code] = total_value
        print(f"  {cat_code} - {cat_name:<25} Items: {cat_snaps.count():>3}  Value: €{total_value:>12.2f}")
    
    print("  " + "-" * 80)
    grand_total = sum(category_totals.values())
    print(f"  {'TOTAL':<30} Items: {sept_snapshots.count():>3}  Value: €{grand_total:>12.2f}")
    print()
    
    # Show sample snapshots
    print("  Sample Snapshots (first 5):")
    for snap in sept_snapshots[:5]:
        print(f"    {snap.item.sku} - {snap.item.name[:40]}")
        print(f"      Full: {snap.closing_full_units}, Partial: {snap.closing_partial_units}")
        print(f"      Value: €{snap.closing_stock_value}")
    
except StockPeriod.DoesNotExist:
    print("❌ September 2025 period NOT FOUND!")
    print()

# Check October 2025
print()
print("=" * 100)
print("OCTOBER 2025 CHECK")
print("=" * 100)

oct_periods = StockPeriod.objects.filter(
    hotel=hotel,
    year=2025,
    month=10,
    period_type='MONTHLY'
)

if oct_periods.exists():
    print(f"⚠️  October 2025 period ALREADY EXISTS!")
    for period in oct_periods:
        print(f"  ID: {period.id}")
        print(f"  Period Name: {period.period_name}")
        print(f"  Dates: {period.start_date} to {period.end_date}")
        snapshot_count = StockSnapshot.objects.filter(period=period).count()
        print(f"  Snapshots: {snapshot_count}")
        print()
else:
    print("✓ October 2025 period does NOT exist yet (ready to create)")
    print()

# Check stocktakes
print("=" * 100)
print("STOCKTAKES")
print("=" * 100)

stocktakes = Stocktake.objects.filter(hotel=hotel).order_by('period_start')
print(f"Total stocktakes: {stocktakes.count()}")
print()

for stocktake in stocktakes:
    line_count = StocktakeLine.objects.filter(stocktake=stocktake).count()
    print(f"Stocktake ID: {stocktake.id}")
    print(f"  Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"  Status: {stocktake.status}")
    print(f"  Lines: {line_count}")
    print(f"  Created: {stocktake.created_at}")
    print()

print("=" * 100)
print("INSPECTION COMPLETE")
print("=" * 100)
