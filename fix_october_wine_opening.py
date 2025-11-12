"""
FIX: Copy September closing to October opening for Wine items
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel
from decimal import Decimal

def fix_october_wine_opening():
    """Fix October wine opening from September closing"""
    print("=" * 80)
    print("FIXING OCTOBER WINE OPENING STOCK")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    
    # Get periods
    sep_period = StockPeriod.objects.get(hotel=hotel, year=2025, month=9)
    oct_period = StockPeriod.objects.get(hotel=hotel, year=2025, month=10)
    
    # Get stocktakes
    sep_stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start=sep_period.start_date
    )
    
    oct_stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start=oct_period.start_date
    )
    
    # Get September snapshots
    sep_snapshots = {
        snap.item.sku: snap 
        for snap in StockSnapshot.objects.filter(period=sep_period)
    }
    
    print(f"September Stocktake: {sep_stocktake.id}")
    print(f"October Stocktake: {oct_stocktake.id}\n")
    
    # Get all wine lines in October
    oct_wines = oct_stocktake.lines.filter(item__category__code='W')
    
    print(f"Found {oct_wines.count()} wine items in October\n")
    print("=" * 80)
    
    fixed = 0
    already_correct = 0
    not_in_sep = 0
    
    for oct_line in oct_wines:
        sku = oct_line.item.sku
        
        # Get September closing snapshot
        sep_snap = sep_snapshots.get(sku)
        
        if not sep_snap:
            print(f"⚠️  {sku}: Not in September snapshots")
            not_in_sep += 1
            continue
        
        # Calculate September closing
        sep_closing = (sep_snap.closing_full_units * sep_snap.item.uom + 
                      sep_snap.closing_partial_units)
        
        current_oct_opening = oct_line.opening_qty
        
        if current_oct_opening == 0 and sep_closing > 0:
            # FIX: Set October opening to September closing
            oct_line.opening_qty = sep_closing
            oct_line.save()
            fixed += 1
            print(f"✅ {sku}: Fixed opening from 0.00 → {sep_closing:.2f}")
        elif current_oct_opening == sep_closing:
            already_correct += 1
        else:
            print(f"ℹ️  {sku}: Oct opening {current_oct_opening:.2f}, Sep closing {sep_closing:.2f}")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"   ✅ Fixed: {fixed} items")
    print(f"   ✅ Already Correct: {already_correct} items")
    print(f"   ⚠️  Not in September: {not_in_sep} items")
    print(f"   Total: {fixed + already_correct + not_in_sep} items")
    print(f"{'='*80}\n")
    
    if fixed > 0:
        print("🎉 October wine opening stock has been fixed!")
        print("   Expected values should now be correct.")
    
    return fixed

if __name__ == '__main__':
    fix_october_wine_opening()
