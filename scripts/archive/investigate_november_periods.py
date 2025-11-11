"""
Script to investigate duplicate November periods
Find when/where draft and empty periods are created
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from hotel.models import Hotel
from datetime import date

print("\n" + "="*70)
print("INVESTIGATING NOVEMBER 2025 PERIODS")
print("="*70)

# Find all November 2025 periods
november_periods = StockPeriod.objects.filter(
    year=2025, 
    month=11
).order_by('created_at', 'id')

print(f"\nFound {november_periods.count()} November 2025 period(s)\n")

for i, period in enumerate(november_periods, 1):
    print(f"\n{'='*70}")
    print(f"PERIOD #{i}")
    print(f"{'='*70}")
    print(f"ID: {period.id}")
    print(f"Hotel: {period.hotel.name} (ID: {period.hotel.id})")
    print(f"Type: {period.period_type}")
    print(f"Name: {period.period_name}")
    print(f"Start Date: {period.start_date}")
    print(f"End Date: {period.end_date}")
    print(f"Is Closed: {period.is_closed}")
    print(f"Closed At: {period.closed_at}")
    print(f"Closed By: {period.closed_by}")
    print(f"Created At: {period.created_at}")
    
    # Check for related stocktake
    stocktake = Stocktake.objects.filter(
        hotel=period.hotel,
        period_start=period.start_date,
        period_end=period.end_date
    ).first()
    
    if stocktake:
        print(f"\n--- STOCKTAKE INFO ---")
        print(f"Stocktake ID: {stocktake.id}")
        print(f"Status: {stocktake.status}")
        print(f"Lines Count: {stocktake.lines.count()}")
        print(f"Created At: {stocktake.created_at}")
        print(f"Approved At: {stocktake.approved_at}")
        print(f"Approved By: {stocktake.approved_by}")
    else:
        print(f"\n--- NO STOCKTAKE FOUND ---")
    
    # Check snapshots
    from stock_tracker.models import StockSnapshot
    snapshots = StockSnapshot.objects.filter(period=period)
    print(f"\n--- SNAPSHOTS ---")
    print(f"Snapshot Count: {snapshots.count()}")
    
    if snapshots.exists():
        print(f"First Snapshot Created: {snapshots.first().created_at}")

print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

if november_periods.count() > 1:
    print("\n⚠️  MULTIPLE NOVEMBER PERIODS FOUND!")
    print("\nPossible causes:")
    print("1. Period created automatically when opening stocktake")
    print("2. Period created manually via admin/API")
    print("3. Period created by management command")
    print("4. Period duplicated during testing")
    
    # Compare periods
    print("\n--- COMPARISON ---")
    for period in november_periods:
        stocktake = Stocktake.objects.filter(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).first()
        
        status = "EMPTY/DRAFT" if not stocktake or stocktake.status == 'DRAFT' else "APPROVED"
        lines = stocktake.lines.count() if stocktake else 0
        
        print(f"\nPeriod ID {period.id}:")
        print(f"  - Created: {period.created_at}")
        print(f"  - Status: {status}")
        print(f"  - Lines: {lines}")
        print(f"  - Closed: {period.is_closed}")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

if november_periods.count() > 1:
    print("\n1. Check views.py for period creation logic")
    print("2. Look for auto-creation in StocktakeViewSet")
    print("3. Check if frontend creates periods unnecessarily")
    print("4. Consider adding unique constraint on (hotel, period_type, start_date, end_date)")
    
    # Find which one to keep
    print("\n--- WHICH PERIOD TO KEEP? ---")
    
    for period in november_periods:
        stocktake = Stocktake.objects.filter(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).first()
        
        has_data = stocktake and stocktake.lines.count() > 0
        is_approved = stocktake and stocktake.status == 'APPROVED'
        
        if has_data or is_approved:
            print(f"\n✅ KEEP Period ID {period.id}")
            print(f"   Reason: {'Has approved stocktake' if is_approved else 'Has stocktake data'}")
        else:
            print(f"\n❌ DELETE Period ID {period.id}")
            print(f"   Reason: Empty or draft only")

print("\n" + "="*70)
