"""
Compare February closing stock with March opening stock
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockSnapshot
from decimal import Decimal

print('='*80)
print('COMPARE FEBRUARY CLOSING vs MARCH OPENING')
print('='*80)

# Get February stocktake (approved)
feb_st = Stocktake.objects.get(id=37)
print(f'\nFebruary Stocktake #{feb_st.id}:')
print(f'  Status: {feb_st.status}')
print(f'  Lines: {feb_st.lines.count()}')
print(f'  Dates: {feb_st.period_start} to {feb_st.period_end}')

# Get March stocktake
march_st = Stocktake.objects.get(id=44)
print(f'\nMarch Stocktake #{march_st.id}:')
print(f'  Status: {march_st.status}')
print(f'  Lines: {march_st.lines.count()}')
print(f'  Dates: {march_st.period_start} to {march_st.period_end}')

# Check February snapshots
feb_snapshots = StockSnapshot.objects.filter(
    hotel_id=2,
    period_id=29
).count()
print(f'\nFebruary snapshots (Period 29): {feb_snapshots}')

# Sample comparison - check first 5 items
print('\n' + '='*80)
print('SAMPLE COMPARISON (First 5 items):')
print('='*80)

for feb_line in feb_st.lines.all()[:5]:
    # Find matching March line
    try:
        march_line = march_st.lines.get(item=feb_line.item)
        
        print(f'\n{feb_line.item.name} ({feb_line.item.sku}):')
        print(f'  FEB CLOSING (counted):')
        print(f'    Full: {feb_line.counted_full_units}')
        print(f'    Partial: {feb_line.counted_partial_units}')
        print(f'    Value: €{feb_line.counted_value}')
        
        print(f'  MARCH OPENING:')
        print(f'    Full: {march_line.opening_full_units}')
        print(f'    Partial: {march_line.opening_partial_units}')
        print(f'    Value: €{march_line.opening_value}')
        
        # Check if they match
        if (feb_line.counted_full_units == march_line.opening_full_units and
            feb_line.counted_partial_units == march_line.opening_partial_units):
            print(f'  ✅ MATCH')
        else:
            print(f'  ❌ MISMATCH')
            
    except Exception as e:
        print(f'\n{feb_line.item.name}: Error - {e}')

# Check specific problem items (syrups)
print('\n' + '='*80)
print('CHECK PROBLEM ITEMS (Syrups with huge values):')
print('='*80)

problem_skus = ['M0320', 'M0008', 'M0009', 'M3']  # Grenadine, Lemon Juice, Lime Juice, Agave

for sku in problem_skus:
    try:
        feb_line = feb_st.lines.get(item__sku=sku)
        march_line = march_st.lines.get(item__sku=sku)
        
        print(f'\n{feb_line.item.name} ({sku}):')
        print(f'  FEB counted: {feb_line.counted_full_units} + {feb_line.counted_partial_units}')
        print(f'  FEB value: €{feb_line.counted_value}')
        print(f'  MARCH opening: {march_line.opening_full_units} + {march_line.opening_partial_units}')
        print(f'  MARCH opening value: €{march_line.opening_value}')
        
        if march_line.opening_full_units == Decimal('157.5'):
            print(f'  ⚠️ PROBLEM: March has wrong opening value (157.5 bottles!)')
            
    except Exception as e:
        print(f'\n{sku}: Error - {e}')

print('\n' + '='*80)
print('DIAGNOSIS')
print('='*80)
print("""
If March opening values are WRONG (like 157.5 bottles for syrups):
- February closing stock was saved incorrectly in snapshots
- OR March opening was calculated from wrong source
- OR Frontend is displaying calculated values incorrectly

Next steps:
1. Check February snapshots in database
2. Check where March opening stock is pulled from
3. Check if issue is in storage or display
""")
