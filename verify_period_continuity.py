"""
Verify that October opening = September closing (counted)
This ensures continuity between stocktake periods
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, StockSnapshot, Stocktake
from hotel.models import Hotel
from decimal import Decimal

def verify_period_continuity():
    """Verify October opening matches September counted"""
    print("=" * 80)
    print("PERIOD CONTINUITY VERIFICATION")
    print("Checking: September Counted = October Opening")
    print("=" * 80)
    
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found")
        return
    
    print(f"✅ Hotel: {hotel.name}\n")
    
    # Get September and October periods
    sep_period = StockPeriod.objects.filter(
        hotel=hotel, 
        year=2025, 
        month=9
    ).first()
    
    oct_period = StockPeriod.objects.filter(
        hotel=hotel, 
        year=2025, 
        month=10
    ).first()
    
    if not sep_period:
        print("❌ September 2025 period not found")
        return
    
    if not oct_period:
        print("❌ October 2025 period not found")
        return
    
    print(f"✅ September Period: ID {sep_period.id}")
    print(f"   Dates: {sep_period.start_date} to {sep_period.end_date}")
    
    print(f"✅ October Period: ID {oct_period.id}")
    print(f"   Dates: {oct_period.start_date} to {oct_period.end_date}\n")
    
    # Check if stocktakes exist
    sep_stocktake = Stocktake.objects.filter(
        hotel=hotel,
        period_start=sep_period.start_date,
        period_end=sep_period.end_date
    ).first()
    
    oct_stocktake = Stocktake.objects.filter(
        hotel=hotel,
        period_start=oct_period.start_date,
        period_end=oct_period.end_date
    ).first()
    
    print("=" * 80)
    print("METHOD 1: Compare via Stocktakes (if they exist)")
    print("=" * 80)
    
    if sep_stocktake and oct_stocktake:
        print(f"✅ September Stocktake: ID {sep_stocktake.id}")
        print(f"✅ October Stocktake: ID {oct_stocktake.id}\n")
        
        # Get all items
        sep_lines = {line.item.sku: line for line in sep_stocktake.lines.all()}
        oct_lines = {line.item.sku: line for line in oct_stocktake.lines.all()}
        
        print(f"Comparing {len(sep_lines)} items...\n")
        
        matches = 0
        mismatches = 0
        
        for sku in sorted(sep_lines.keys()):
            if sku not in oct_lines:
                print(f"⚠️  {sku}: Not in October stocktake")
                continue
            
            sep_line = sep_lines[sku]
            oct_line = oct_lines[sku]
            
            # September counted should equal October opening
            sep_counted = sep_line.counted_qty
            oct_opening = oct_line.opening_qty
            
            diff = abs(sep_counted - oct_opening)
            
            if diff < Decimal('0.01'):  # Allow tiny rounding differences
                matches += 1
                if matches <= 5:  # Show first 5 matches
                    print(f"✅ {sku}: Sep counted {sep_counted} = Oct opening {oct_opening}")
            else:
                mismatches += 1
                print(f"❌ {sku}: Sep counted {sep_counted} ≠ Oct opening {oct_opening} (diff: {diff})")
        
        print(f"\n{'='*80}")
        print(f"STOCKTAKE METHOD SUMMARY:")
        print(f"   ✅ Matches: {matches}")
        print(f"   ❌ Mismatches: {mismatches}")
        print(f"{'='*80}\n")
    else:
        print("⚠️  September or October stocktake not found")
        print("   (Stocktakes are used for counting, snapshots for opening/closing)")
    
    print("\n" + "=" * 80)
    print("METHOD 2: Compare via Snapshots (Period Opening/Closing)")
    print("=" * 80)
    
    # Get snapshots
    sep_snapshots = {snap.item.sku: snap for snap in StockSnapshot.objects.filter(period=sep_period)}
    oct_snapshots = {snap.item.sku: snap for snap in StockSnapshot.objects.filter(period=oct_period)}
    
    print(f"✅ September Snapshots: {len(sep_snapshots)}")
    print(f"✅ October Snapshots: {len(oct_snapshots)}\n")
    
    if not sep_snapshots or not oct_snapshots:
        print("❌ No snapshots found")
        return
    
    print("Comparing snapshots (September closing should = October opening)...\n")
    
    matches = 0
    mismatches = 0
    total_sep_value = Decimal('0')
    total_oct_value = Decimal('0')
    
    # Show first 10 items from each category
    categories = {}
    
    for sku in sorted(sep_snapshots.keys()):
        if sku not in oct_snapshots:
            print(f"⚠️  {sku}: Not in October snapshots")
            continue
        
        sep_snap = sep_snapshots[sku]
        oct_snap = oct_snapshots[sku]
        
        # September closing = October opening (conceptually)
        # But StockSnapshot only stores closing values
        # October's closing is the opening for November
        
        sep_closing_qty = (sep_snap.closing_full_units * sep_snap.item.uom + 
                          sep_snap.closing_partial_units)
        oct_closing_qty = (oct_snap.closing_full_units * oct_snap.item.uom + 
                          oct_snap.closing_partial_units)
        
        sep_closing_value = sep_snap.closing_stock_value
        oct_closing_value = oct_snap.closing_stock_value
        
        total_sep_value += sep_closing_value
        total_oct_value += oct_closing_value
        
        cat = sku[0]
        if cat not in categories:
            categories[cat] = {'matches': 0, 'mismatches': 0, 'shown': 0}
        
        # For snapshots, we compare closing values
        # October opening would be stored in stocktake, not snapshot
        # Show some examples
        if categories[cat]['shown'] < 2:
            print(f"ℹ️  {sku} ({sep_snap.item.category.name}):")
            print(f"   Sep Closing: {sep_closing_qty:.4f} servings = €{sep_closing_value:.2f}")
            print(f"   Oct Closing: {oct_closing_qty:.4f} servings = €{oct_closing_value:.2f}")
            categories[cat]['shown'] += 1
    
    print(f"\n{'='*80}")
    print(f"SNAPSHOT VALUES:")
    print(f"   September Total Closing: €{total_sep_value:.2f}")
    print(f"   October Total Closing: €{total_oct_value:.2f}")
    print(f"{'='*80}\n")
    
    # Now check if October stocktake opening matches September closing
    if oct_stocktake:
        print("=" * 80)
        print("METHOD 3: October Stocktake Opening vs September Snapshot Closing")
        print("=" * 80)
        
        matches = 0
        mismatches = 0
        
        oct_lines = {line.item.sku: line for line in oct_stocktake.lines.all()}
        
        print("Checking if October stocktake opening = September closing...\n")
        
        for sku in sorted(sep_snapshots.keys())[:10]:  # Check first 10
            if sku not in oct_lines:
                continue
            
            sep_snap = sep_snapshots[sku]
            oct_line = oct_lines[sku]
            
            # September closing (from snapshot)
            sep_closing = (sep_snap.closing_full_units * sep_snap.item.uom + 
                          sep_snap.closing_partial_units)
            
            # October opening (from stocktake line)
            oct_opening = oct_line.opening_qty
            
            diff = abs(sep_closing - oct_opening)
            
            if diff < Decimal('0.01'):
                matches += 1
                print(f"✅ {sku}: Sep closing {sep_closing:.4f} = Oct opening {oct_opening:.4f}")
            else:
                mismatches += 1
                print(f"❌ {sku}: Sep closing {sep_closing:.4f} ≠ Oct opening {oct_opening:.4f} (diff: {diff:.4f})")
        
        print(f"\n{'='*80}")
        print(f"CONTINUITY CHECK (first 10 items):")
        print(f"   ✅ Matches: {matches}")
        print(f"   ❌ Mismatches: {mismatches}")
        
        if matches > 0 and mismatches == 0:
            print(f"\n   ✅✅✅ PERFECT! September closing = October opening")
        elif mismatches > 0:
            print(f"\n   ⚠️  WARNING: Found mismatches in continuity")
        
        print(f"{'='*80}")
    
    print("\n✅ VERIFICATION COMPLETE\n")

if __name__ == '__main__':
    verify_period_continuity()
