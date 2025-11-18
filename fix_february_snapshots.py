"""
Re-approve February 2025 stocktake to generate missing snapshots
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod, StockSnapshot
from stock_tracker.stocktake_service import approve_stocktake

print('='*80)
print('RE-APPROVE FEBRUARY STOCKTAKE TO GENERATE SNAPSHOTS')
print('='*80)

# Get February stocktake
stocktake = Stocktake.objects.get(id=37)
print(f'\nStocktake 37 (Feb 2025):')
print(f'  Status: {stocktake.status}')
print(f'  Lines: {stocktake.lines.count()}')
print(f'  Approved at: {stocktake.approved_at}')

# Get February period
period = StockPeriod.objects.get(id=29)
print(f'\nPeriod 29 (Feb 2025):')
print(f'  Dates: {period.start_date} to {period.end_date}')
print(f'  Closed: {period.is_closed}')

# Check current snapshots
snapshots_before = StockSnapshot.objects.filter(
    hotel_id=2,
    period_id=29
).count()
print(f'\nSnapshots BEFORE: {snapshots_before}')

# Change status back to DRAFT so we can re-approve
print('\n--- Changing status to DRAFT ---')
stocktake.status = Stocktake.DRAFT
stocktake.save()

# Re-approve using the service function
print('\n--- Re-approving stocktake ---')
try:
    # Get staff who originally approved
    staff = stocktake.approved_by
    if not staff:
        from staff.models import Staff
        staff = Staff.objects.filter(hotel_id=2).first()
    
    adjustments = approve_stocktake(stocktake, staff)
    print(f'✅ Stocktake re-approved!')
    print(f'   Adjustments created: {adjustments}')
    
    # Check snapshots after
    snapshots_after = StockSnapshot.objects.filter(
        hotel_id=2,
        period_id=29
    ).count()
    print(f'\nSnapshots AFTER: {snapshots_after}')
    print(f'Snapshots created: {snapshots_after - snapshots_before}')
    
    # Check by category
    d = StockSnapshot.objects.filter(
        hotel_id=2, period_id=29, item__category_id='D'
    ).count()
    b = StockSnapshot.objects.filter(
        hotel_id=2, period_id=29, item__category_id='B'
    ).count()
    s = StockSnapshot.objects.filter(
        hotel_id=2, period_id=29, item__category_id='S'
    ).count()
    w = StockSnapshot.objects.filter(
        hotel_id=2, period_id=29, item__category_id='W'
    ).count()
    m = StockSnapshot.objects.filter(
        hotel_id=2, period_id=29, item__category_id='M'
    ).count()
    
    print(f'\nSnapshots by category:')
    print(f'  Draught: {d}')
    print(f'  Bottled Beer: {b}')
    print(f'  Spirits: {s}')
    print(f'  Wine: {w}')
    print(f'  Minerals: {m}')
    print(f'  Total: {d+b+s+w+m}')
    
    print('\n✅ SUCCESS! February period now has snapshots for ALL categories!')
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
