"""
Test script to add manual values to stocktake lines and verify calculations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import Stocktake, StocktakeLine

def test_manual_values():
    """Add manual values to October 2025 stocktake lines and verify totals"""
    
    # Get October 2025 stocktake
    stocktake = Stocktake.objects.get(id=5)
    
    print(f"\n=== Testing Manual Values on Stocktake Lines ===")
    print(f"Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"\n--- BEFORE Manual Values ---")
    print(f"Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"Total Revenue: €{stocktake.total_revenue:,.2f}")
    print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    
    # Get first few lines to add manual values
    lines = stocktake.lines.all()[:5]
    
    print(f"\n--- Adding Manual Values to {len(lines)} Lines ---")
    
    # Add manual purchases, waste, and sales to lines
    total_manual_purchases = Decimal('0')
    total_manual_waste = Decimal('0')
    total_manual_sales = Decimal('0')
    
    for i, line in enumerate(lines, 1):
        # Distribute €19,000 purchases across lines
        purchases = Decimal('3800.00')  # €19,000 / 5 lines
        waste = Decimal('500.00')       # €500 waste per line
        sales = Decimal('12400.00')     # €62,000 / 5 lines
        
        line.manual_purchases_value = purchases
        line.manual_waste_value = waste
        line.manual_sales_value = sales
        line.save()
        
        total_manual_purchases += purchases
        total_manual_waste += waste
        total_manual_sales += sales
        
        print(f"Line {i} ({line.item.name}):")
        print(f"  Purchases: €{purchases:,.2f}")
        print(f"  Waste: €{waste:,.2f}")
        print(f"  Sales: €{sales:,.2f}")
    
    print(f"\nTotal Manual Purchases: €{total_manual_purchases:,.2f}")
    print(f"Total Manual Waste: €{total_manual_waste:,.2f}")
    print(f"Total Manual Sales: €{total_manual_sales:,.2f}")
    
    # Clear cached properties
    if hasattr(stocktake, '_total_cogs'):
        delattr(stocktake, '_total_cogs')
    
    # Refresh from DB
    stocktake = Stocktake.objects.get(id=5)
    
    print(f"\n--- AFTER Manual Values ---")
    print(f"Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"  (Expected: €{total_manual_purchases + total_manual_waste:,.2f} from manual values)")
    print(f"Total Revenue: €{stocktake.total_revenue:,.2f}")
    print(f"  (Expected: €{total_manual_sales:,.2f} from manual values)")
    print(f"Gross Profit: €{stocktake.total_revenue - stocktake.total_cogs:,.2f}")
    print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    print(f"Pour Cost %: {stocktake.pour_cost_percentage:.2f}%")
    
    # Verify calculations
    expected_cogs = total_manual_purchases + total_manual_waste
    expected_revenue = total_manual_sales
    expected_gp_pct = ((expected_revenue - expected_cogs) / expected_revenue) * 100
    
    print(f"\n--- Verification ---")
    print(f"COGS Match: {stocktake.total_cogs == expected_cogs} ({stocktake.total_cogs} vs {expected_cogs})")
    print(f"Revenue Match: {stocktake.total_revenue == expected_revenue} ({stocktake.total_revenue} vs {expected_revenue})")
    print(f"GP% Expected: {expected_gp_pct:.2f}%")
    
    if stocktake.total_cogs == expected_cogs and stocktake.total_revenue == expected_revenue:
        print("\n✅ SUCCESS! Manual values are correctly calculating totals!")
    else:
        print("\n❌ FAILED! Totals don't match expected values")

def clear_manual_values():
    """Clear manual values from October 2025 lines"""
    stocktake = Stocktake.objects.get(id=5)
    lines = stocktake.lines.filter(
        manual_purchases_value__isnull=False
    ) | stocktake.lines.filter(
        manual_waste_value__isnull=False
    ) | stocktake.lines.filter(
        manual_sales_value__isnull=False
    )
    
    count = lines.count()
    lines.update(
        manual_purchases_value=None,
        manual_waste_value=None,
        manual_sales_value=None
    )
    print(f"Cleared manual values from {count} lines")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'clear':
        clear_manual_values()
    else:
        test_manual_values()
