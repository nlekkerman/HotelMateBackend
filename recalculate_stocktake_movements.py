"""
Recalculate purchases and waste for all lines in a stocktake
Use this after deleting movements to sync the line values
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from stock_tracker.stocktake_service import _calculate_period_movements
from decimal import Decimal

def recalculate_stocktake_lines(stocktake_id):
    """Recalculate all line movements for a stocktake"""
    
    try:
        stocktake = Stocktake.objects.get(id=stocktake_id)
    except Stocktake.DoesNotExist:
        print(f"❌ Stocktake {stocktake_id} not found")
        return
    
    print("=" * 70)
    print(f"RECALCULATING STOCKTAKE {stocktake_id}")
    print("=" * 70)
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print(f"Total lines: {stocktake.lines.count()}")
    print()
    
    if stocktake.is_locked:
        print("⚠️  WARNING: This stocktake is APPROVED/LOCKED!")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled")
            return
    
    print("\n🔄 Recalculating movements for all lines...")
    print()
    
    updates_made = 0
    no_changes = 0
    
    for line in stocktake.lines.all():
        # Calculate movements from database
        movements = _calculate_period_movements(
            line.item,
            stocktake.period_start,
            stocktake.period_end
        )
        
        # Check if values changed
        old_purchases = line.purchases
        old_waste = line.waste
        
        new_purchases = movements['purchases']
        new_waste = movements['waste']
        
        if old_purchases != new_purchases or old_waste != new_waste:
            print(f"✏️  {line.item.sku:10} | P: {old_purchases} → {new_purchases} | W: {old_waste} → {new_waste}")
            
            line.purchases = new_purchases
            line.waste = new_waste
            line.save()
            updates_made += 1
        else:
            no_changes += 1
    
    print()
    print("=" * 70)
    print(f"✅ COMPLETE")
    print("=" * 70)
    print(f"Lines updated: {updates_made}")
    print(f"Lines unchanged: {no_changes}")
    print()
    
    # Show summary
    total_purchases = sum(line.purchases for line in stocktake.lines.all())
    total_waste = sum(line.waste for line in stocktake.lines.all())
    print(f"📊 New totals:")
    print(f"   Total purchases: {total_purchases}")
    print(f"   Total waste: {total_waste}")
    print()

def recalculate_all_draft_stocktakes():
    """Recalculate all DRAFT stocktakes"""
    
    draft_stocktakes = Stocktake.objects.filter(status=Stocktake.DRAFT)
    
    print(f"\n📋 Found {draft_stocktakes.count()} DRAFT stocktakes")
    print()
    
    for stocktake in draft_stocktakes:
        print(f"Processing Stocktake {stocktake.id} ({stocktake.period_start} to {stocktake.period_end})...")
        recalculate_stocktake_lines(stocktake.id)
        print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'all':
            recalculate_all_draft_stocktakes()
        else:
            stocktake_id = int(sys.argv[1])
            recalculate_stocktake_lines(stocktake_id)
    else:
        print("Usage:")
        print("  python recalculate_stocktake_movements.py <stocktake_id>")
        print("  python recalculate_stocktake_movements.py all  # all DRAFT stocktakes")
        print()
        
        # Show available stocktakes
        stocktakes = Stocktake.objects.all().order_by('-period_start')
        print("Available stocktakes:")
        for st in stocktakes:
            print(f"  ID {st.id}: {st.period_start} to {st.period_end} ({st.status})")
