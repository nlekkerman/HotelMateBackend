"""
Analyze the relationship between StockPeriod, StockSnapshot, and Stocktake.
Shows how IDs can mismatch if stocktakes are deleted and recreated.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel

print("=" * 80)
print("RELATIONSHIP: StockPeriod → StockSnapshot → Stocktake")
print("=" * 80)
print()

hotel = Hotel.objects.get(id=2)
print(f"Hotel: {hotel.name}")
print()

# Get all periods
periods = StockPeriod.objects.filter(hotel=hotel).order_by('-start_date')

print("=" * 80)
print("ALL PERIODS")
print("=" * 80)

for period in periods:
    print(f"\n📅 Period ID: {period.id}")
    print(f"   Name: {period.period_name}")
    print(f"   Type: {period.period_type}")
    print(f"   Dates: {period.start_date} to {period.end_date}")
    print(f"   Status: {'CLOSED ✓' if period.is_closed else 'OPEN'}")
    
    # Count snapshots
    snapshot_count = StockSnapshot.objects.filter(period=period).count()
    print(f"   Snapshots: {snapshot_count}")
    
    # Find related stocktakes (if any)
    # Note: Stocktake has period_start/period_end, not direct FK to StockPeriod
    stocktakes = Stocktake.objects.filter(
        hotel=hotel,
        period_start=period.start_date,
        period_end=period.end_date
    )
    
    if stocktakes.exists():
        print(f"   Related Stocktakes:")
        for st in stocktakes:
            print(f"      - Stocktake ID: {st.id}")
            print(f"        Status: {st.status}")
            print(f"        Lines: {st.lines.count()}")
            print(f"        Created: {st.created_at}")
    else:
        print(f"   Related Stocktakes: None")

print()
print("=" * 80)
print("KEY OBSERVATIONS")
print("=" * 80)
print()

# Check if there are any stocktakes
all_stocktakes = Stocktake.objects.filter(hotel=hotel)
print(f"Total Stocktakes: {all_stocktakes.count()}")

if all_stocktakes.exists():
    print()
    print("Stocktake Details:")
    for st in all_stocktakes:
        print(f"\n   Stocktake ID: {st.id}")
        print(f"   Period: {st.period_start} to {st.period_end}")
        print(f"   Status: {st.status}")
        print(f"   Lines: {st.lines.count()}")
        
        # Try to find matching period
        matching_period = StockPeriod.objects.filter(
            hotel=hotel,
            start_date=st.period_start,
            end_date=st.period_end
        ).first()
        
        if matching_period:
            print(f"   ✓ Matches Period ID: {matching_period.id} ({matching_period.period_name})")
        else:
            print(f"   ✗ No matching period found!")

print()
print("=" * 80)
print("RELATIONSHIP SUMMARY")
print("=" * 80)
print()
print("1. StockPeriod:")
print("   - Defines time ranges (Oct 2024, Nov 2024, etc.)")
print("   - Has start_date and end_date")
print("   - Unique ID that persists")
print()
print("2. StockSnapshot:")
print("   - Direct FK to StockPeriod (period_id)")
print("   - One snapshot per item per period")
print("   - Created when period is closed OR via populate_opening_stock")
print()
print("3. Stocktake (Legacy?):")
print("   - Has period_start and period_end dates")
print("   - NO direct FK to StockPeriod")
print("   - Can be deleted and recreated (ID changes)")
print("   - Links to period via dates only")
print()
print("⚠️  IMPORTANT:")
print("   - Period ID and Stocktake ID can be different!")
print("   - If stocktake deleted/recreated, its ID changes")
print("   - Period ID stays the same")
print("   - Snapshots always link to Period ID (stable)")
print()

# Show example snapshot to period relationship
if periods.exists():
    first_period = periods.first()
    sample_snapshot = StockSnapshot.objects.filter(
        period=first_period
    ).select_related('item').first()
    
    if sample_snapshot:
        print("=" * 80)
        print("EXAMPLE SNAPSHOT → PERIOD LINK")
        print("=" * 80)
        print()
        print(f"Snapshot ID: {sample_snapshot.id}")
        print(f"Item: {sample_snapshot.item.name} ({sample_snapshot.item.sku})")
        print(f"→ Links to Period ID: {sample_snapshot.period_id}")
        print(f"  Period Name: {sample_snapshot.period.period_name}")
        print(f"  Period Dates: {sample_snapshot.period.start_date} to {sample_snapshot.period.end_date}")
        print()
