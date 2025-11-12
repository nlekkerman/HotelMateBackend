"""
Script to delete stocktake #16 and create a new one with correct opening balances.
Run with: python repopulate_stocktake.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod
from stock_tracker.stocktake_service import populate_stocktake

def main():
    print("=" * 60)
    print("REPOPULATING STOCKTAKE #16")
    print("=" * 60)
    
    try:
        # Get the stocktake
        stocktake = Stocktake.objects.get(id=16)
        print(f"\n✓ Found Stocktake #16")
        print(f"  Period: {stocktake.period_start} to {stocktake.period_end}")
        print(f"  Status: {stocktake.status}")
        print(f"  Current lines: {stocktake.lines.count()}")
        
        # Delete existing lines
        line_count = stocktake.lines.count()
        stocktake.lines.all().delete()
        print(f"\n✓ Deleted {line_count} existing lines")
        
        # Repopulate with fixed logic
        print("\n⏳ Repopulating stocktake with corrected opening balances...")
        lines_created = populate_stocktake(stocktake)
        print(f"✓ Created {lines_created} new lines")
        
        # Check a sample line
        sample_line = stocktake.lines.first()
        if sample_line:
            print(f"\n📊 Sample line (first item):")
            print(f"  Item: {sample_line.item.sku} - {sample_line.item.name}")
            print(f"  Opening Qty: {sample_line.opening_qty}")
            print(f"  Purchases: {sample_line.purchases}")
            print(f"  Expected: {sample_line.expected_qty}")
            print(f"  Opening Display: {sample_line.opening_display_full_units} + {sample_line.opening_display_partial_units}")
        
        print("\n" + "=" * 60)
        print("✅ REPOPULATION COMPLETE!")
        print("=" * 60)
        print("\nRefresh your frontend to see the updated opening balances.")
        
    except Stocktake.DoesNotExist:
        print("\n❌ ERROR: Stocktake #16 not found!")
        print("Available stocktakes:")
        for st in Stocktake.objects.all()[:10]:
            print(f"  - ID {st.id}: {st.period_start} to {st.period_end} ({st.status})")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
