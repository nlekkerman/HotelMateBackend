"""
Check purchases and waste for a specific stocktake line
Shows all movements and explains why numbers appear
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StocktakeLine, StockMovement
from decimal import Decimal

def check_line_movements(line_id):
    """Check movements for a specific line"""
    
    try:
        line = StocktakeLine.objects.get(id=line_id)
    except StocktakeLine.DoesNotExist:
        print(f"❌ Line {line_id} not found")
        return
    
    print("=" * 70)
    print(f"CHECKING LINE {line_id}")
    print("=" * 70)
    print(f"Item: {line.item.sku} - {line.item.name}")
    print(f"Stocktake: {line.stocktake.id} ({line.stocktake.period_start} to {line.stocktake.period_end})")
    print()
    
    print("📊 CURRENT LINE VALUES:")
    print(f"   Purchases: {line.purchases}")
    print(f"   Waste: {line.waste}")
    print(f"   Opening: {line.opening_qty}")
    print(f"   Expected: {line.expected_qty}")
    print(f"   Counted: {line.counted_qty}")
    print(f"   Variance: {line.variance_qty}")
    print()
    
    # Get all movements for this item in the period
    movements = StockMovement.objects.filter(
        item=line.item,
        timestamp__gte=line.stocktake.period_start,
        timestamp__lte=line.stocktake.period_end
    ).order_by('timestamp')
    
    print(f"📦 MOVEMENTS IN PERIOD ({movements.count()} total):")
    print()
    
    if movements.count() == 0:
        print("   ⚠️  NO MOVEMENTS FOUND IN THIS PERIOD!")
        print()
        print("   🤔 If purchases/waste show non-zero values,")
        print("      they might be:")
        print("      1. Cached from populate (not recalculated)")
        print("      2. From movements OUTSIDE the period")
        print("      3. From deleted movements (orphaned data)")
    else:
        purchases_total = Decimal('0')
        waste_total = Decimal('0')
        
        for mov in movements:
            print(f"   {mov.timestamp} | {mov.movement_type:15} | {mov.quantity:10} | ID: {mov.id}")
            if mov.movement_type == 'PURCHASE':
                purchases_total += mov.quantity
            elif mov.movement_type == 'WASTE':
                waste_total += mov.quantity
        
        print()
        print(f"   💰 Total PURCHASES: {purchases_total}")
        print(f"   🗑️  Total WASTE: {waste_total}")
        print()
        
        # Check if they match
        if purchases_total != line.purchases:
            print(f"   ⚠️  MISMATCH: Line shows {line.purchases} but movements total {purchases_total}")
        else:
            print(f"   ✅ Purchases match!")
        
        if waste_total != line.waste:
            print(f"   ⚠️  MISMATCH: Line shows {line.waste} but movements total {waste_total}")
        else:
            print(f"   ✅ Waste matches!")
    
    print()
    print("🔍 CHECKING ALL MOVEMENTS FOR THIS ITEM (ANY TIME):")
    all_movements = StockMovement.objects.filter(item=line.item).order_by('timestamp')
    print(f"   Total movements (all time): {all_movements.count()}")
    
    if all_movements.count() > 0:
        print()
        print("   Recent movements:")
        for mov in all_movements[:10]:
            in_period = "✅" if (line.stocktake.period_start <= mov.timestamp <= line.stocktake.period_end) else "❌"
            print(f"   {in_period} {mov.timestamp} | {mov.movement_type:15} | {mov.quantity:10} | ID: {mov.id}")
    
    print()
    print("=" * 70)

def check_november_stocktake():
    """Check November stocktake lines"""
    from stock_tracker.models import Stocktake
    
    try:
        stocktake = Stocktake.objects.get(
            period_start__year=2025,
            period_start__month=11
        )
        print(f"\n📋 Found November 2025 Stocktake (ID: {stocktake.id})")
        print(f"   Status: {stocktake.status}")
        print(f"   Lines: {stocktake.lines.count()}")
        print()
        
        # Show some lines with non-zero purchases/waste
        lines_with_movements = stocktake.lines.filter(
            purchases__gt=0
        ) | stocktake.lines.filter(
            waste__gt=0
        )
        
        print(f"   Lines with purchases or waste: {lines_with_movements.count()}")
        
        if lines_with_movements.exists():
            print("\n   First 5 lines with movements:")
            for line in lines_with_movements[:5]:
                print(f"   - Line {line.id}: {line.item.sku} (P: {line.purchases}, W: {line.waste})")
            
            print("\n🔍 Checking first line in detail:\n")
            check_line_movements(lines_with_movements.first().id)
    
    except Stocktake.DoesNotExist:
        print("❌ November 2025 stocktake not found")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        line_id = int(sys.argv[1])
        check_line_movements(line_id)
    else:
        check_november_stocktake()
