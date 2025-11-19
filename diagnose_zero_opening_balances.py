"""
Diagnose why opening balances are ZERO in frontend
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake

print('='*80)
print('DIAGNOSE ZERO OPENING BALANCES')
print('='*80)

# Check March period (the one frontend is viewing)
march = StockPeriod.objects.get(id=30)
print(f'\nMarch 2025 (Period 30):')
print(f'  Dates: {march.start_date} to {march.end_date}')
print(f'  Closed: {march.is_closed}')

# Check March stocktake
try:
    march_st = Stocktake.objects.get(
        hotel_id=2,
        period_start=march.start_date,
        period_end=march.end_date
    )
    print(f'\nMarch Stocktake (ID={march_st.id}):')
    print(f'  Status: {march_st.status}')
    print(f'  Lines: {march_st.lines.count()}')
    
    # Check first 3 lines for opening stock
    print(f'\nFirst 3 stocktake lines:')
    for line in march_st.lines.all()[:3]:
        print(f'\n  {line.item.name}:')
        print(f'    opening_full_units: {line.opening_full_units}')
        print(f'    opening_partial_units: {line.opening_partial_units}')
        print(f'    expected_qty: {line.expected_qty}')
        print(f'    counted_full_units: {line.counted_full_units}')
        print(f'    counted_partial_units: {line.counted_partial_units}')
        
except Stocktake.DoesNotExist:
    print('\n❌ No March stocktake found!')

# Check February snapshots (should provide March opening stock)
feb = StockPeriod.objects.get(id=29)
feb_snapshots = StockSnapshot.objects.filter(
    hotel_id=2,
    period_id=29
).count()

print(f'\n\nFebruary 2025 (Period 29):')
print(f'  Closed: {feb.is_closed}')
print(f'  Snapshots: {feb_snapshots}')

if feb_snapshots == 0:
    print('\n❌ PROBLEM FOUND: February has NO snapshots!')
    print('   This is why March opening stock is ZERO!')
    print('\n   Solution: Re-approve February stocktake to create snapshots')
    
    # Check February stocktake
    try:
        feb_st = Stocktake.objects.get(
            hotel_id=2,
            period_start=feb.start_date,
            period_end=feb.end_date
        )
        print(f'\nFebruary Stocktake (ID={feb_st.id}):')
        print(f'  Status: {feb_st.status}')
        print(f'  Lines: {feb_st.lines.count()}')
        print(f'\n  Run: python fix_february_snapshots.py')
    except Stocktake.DoesNotExist:
        print('\n❌ No February stocktake found!')
else:
    print(f'\n✅ February has {feb_snapshots} snapshots')
    
    # Sample some snapshots
    print('\nSample February closing stock:')
    for snap in StockSnapshot.objects.filter(
        hotel_id=2, period_id=29
    )[:3]:
        print(f'\n  {snap.item.name}:')
        print(f'    closing_full: {snap.closing_full_units}')
        print(f'    closing_partial: {snap.closing_partial_units}')

print('\n' + '='*80)
print('EXPLANATION')
print('='*80)
print("""
Opening stock population flow:
1. February stocktake approved → Creates February snapshots (closing stock)
2. March stocktake created → Copies February closing → March opening
3. If February has NO snapshots → March opening = ZERO

The approve_and_close endpoint was NOT calling approve_stocktake() service,
so February snapshots were never created!

Fix applied: approve_and_close now calls approve_stocktake()
Next step: Re-approve February OR wait for next period approval to test fix
""")
