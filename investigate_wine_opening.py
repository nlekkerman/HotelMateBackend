"""
Deep dive into Wine category - checking September vs October
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel
from decimal import Decimal

def check_wine_opening():
    """Check wine opening values in detail"""
    print("=" * 80)
    print("WINE CATEGORY OPENING STOCK INVESTIGATION")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    
    # Get periods
    sep_period = StockPeriod.objects.get(hotel=hotel, year=2025, month=9)
    oct_period = StockPeriod.objects.get(hotel=hotel, year=2025, month=10)
    
    # Get stocktakes
    sep_stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start=sep_period.start_date,
        period_end=sep_period.end_date
    )
    
    oct_stocktake = Stocktake.objects.get(
        hotel=hotel,
        period_start=oct_period.start_date,
        period_end=oct_period.end_date
    )
    
    # Get snapshots
    sep_snapshots = {snap.item.sku: snap for snap in StockSnapshot.objects.filter(period=sep_period)}
    oct_snapshots = {snap.item.sku: snap for snap in StockSnapshot.objects.filter(period=oct_period)}
    
    print(f"September Stocktake ID: {sep_stocktake.id}")
    print(f"October Stocktake ID: {oct_stocktake.id}\n")
    
    # Get all wine items from September
    sep_wines = sep_stocktake.lines.filter(item__category__code='W').order_by('item__sku')
    
    print(f"Total Wine Items: {sep_wines.count()}\n")
    print("=" * 80)
    
    issues_found = 0
    
    for sep_line in sep_wines:
        sku = sep_line.item.sku
        
        # Get October line
        try:
            oct_line = oct_stocktake.lines.get(item__sku=sku)
        except:
            print(f"❌ {sku}: Not found in October stocktake!")
            continue
        
        # Get snapshots
        sep_snap = sep_snapshots.get(sku)
        oct_snap = oct_snapshots.get(sku)
        
        # Calculate values
        sep_counted = sep_line.counted_qty
        sep_closing = (sep_snap.closing_full_units * sep_snap.item.uom + 
                      sep_snap.closing_partial_units) if sep_snap else Decimal('0')
        oct_opening = oct_line.opening_qty
        oct_snap_closing = (oct_snap.closing_full_units * oct_snap.item.uom + 
                           oct_snap.closing_partial_units) if oct_snap else Decimal('0')
        
        # Check if October opening is 0 but September had stock
        if oct_opening == 0 and sep_counted > 0:
            issues_found += 1
            print(f"\n🔴 {sku} - {sep_line.item.name}")
            print(f"   Sep Counted: {sep_counted:.2f} bottles")
            print(f"   Sep Closing Snapshot: {sep_closing:.2f} bottles")
            print(f"   Oct Opening: {oct_opening:.2f} bottles ❌ ZERO!")
            print(f"   Oct Closing Snapshot: {oct_snap_closing:.2f} bottles")
            
            # Check if September closing snapshot is also 0
            if sep_closing == 0:
                print(f"   ⚠️  September closing snapshot is ALSO 0.00")
                print(f"   🔍 This means stock was consumed AFTER counting but BEFORE period end")
            else:
                print(f"   ❌ PROBLEM: Sep closing {sep_closing} but Oct opening is 0!")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"   Total Wine Items Checked: {sep_wines.count()}")
    print(f"   Issues Found (Oct opening = 0 but Sep had stock): {issues_found}")
    
    if issues_found > 0:
        print(f"\n   ⚠️  WARNING: {issues_found} wine items have opening = 0 in October")
        print(f"   This could be:")
        print(f"   1. ✅ Correct - stock sold out between Sep count and Sep 30th")
        print(f"   2. ❌ Bug - October opening not copied from September closing")
    
    print(f"{'='*80}\n")
    
    # Now check a few that DO have opening stock
    print("\n" + "=" * 80)
    print("WINES WITH NON-ZERO OCTOBER OPENING (for comparison)")
    print("=" * 80)
    
    good_wines = oct_stocktake.lines.filter(
        item__category__code='W',
        opening_qty__gt=0
    ).order_by('item__sku')[:5]
    
    for oct_line in good_wines:
        sku = oct_line.item.sku
        sep_line = sep_stocktake.lines.get(item__sku=sku)
        sep_snap = sep_snapshots.get(sku)
        
        sep_counted = sep_line.counted_qty
        sep_closing = (sep_snap.closing_full_units * sep_snap.item.uom + 
                      sep_snap.closing_partial_units) if sep_snap else Decimal('0')
        oct_opening = oct_line.opening_qty
        
        print(f"\n✅ {sku} - {oct_line.item.name}")
        print(f"   Sep Counted: {sep_counted:.2f}")
        print(f"   Sep Closing Snapshot: {sep_closing:.2f}")
        print(f"   Oct Opening: {oct_opening:.2f}")
        
        if sep_closing == oct_opening:
            print(f"   ✅ PERFECT MATCH!")
        else:
            print(f"   ⚠️  Difference: {sep_closing - oct_opening:.2f}")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    check_wine_opening()
