"""
Reopen October 2025, clear test data, add real manual values, and close again
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from datetime import date
from django.utils import timezone
from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine


def reopen_october():
    """Reopen October 2025 stocktake"""
    stocktake = Stocktake.objects.get(id=5)
    
    print("\n=== STEP 1: Reopening October 2025 Stocktake ===")
    print(f"Current Status: {stocktake.status}")
    
    stocktake.status = Stocktake.DRAFT
    stocktake.approved_at = None
    stocktake.approved_by = None
    stocktake.save()
    
    print(f"✅ Status changed to: {stocktake.status}")
    return stocktake


def clear_test_data(stocktake):
    """Clear manual values from lines that were added for testing"""
    print("\n=== STEP 2: Clearing Test Data from Lines ===")
    
    lines_with_manual = StocktakeLine.objects.filter(
        stocktake=stocktake
    ).filter(
        manual_purchases_value__isnull=False
    ) | StocktakeLine.objects.filter(
        stocktake=stocktake
    ).filter(
        manual_waste_value__isnull=False
    ) | StocktakeLine.objects.filter(
        stocktake=stocktake
    ).filter(
        manual_sales_value__isnull=False
    )
    
    count = lines_with_manual.count()
    print(f"Found {count} lines with manual values")
    
    if count > 0:
        lines_with_manual.update(
            manual_purchases_value=None,
            manual_waste_value=None,
            manual_sales_value=None
        )
        print(f"✅ Cleared manual values from {count} lines")
    else:
        print("ℹ️  No manual values to clear")


def add_period_manual_values():
    """Add €19,000 and €62,000 to StockPeriod"""
    print("\n=== STEP 3: Adding Manual Values to Period ===")
    
    period = StockPeriod.objects.get(id=7)
    
    print(f"Period: {period.period_name}")
    print(f"Dates: {period.start_date} to {period.end_date}")
    print("\nBEFORE:")
    print(f"  manual_purchases_amount: {period.manual_purchases_amount}")
    print(f"  manual_sales_amount: {period.manual_sales_amount}")
    
    # Check if field exists
    try:
        period.manual_purchases_amount = Decimal('19000.00')
        period.manual_sales_amount = Decimal('62000.00')
        period.save()
        
        print("\nAFTER:")
        print(f"  manual_purchases_amount: €{period.manual_purchases_amount:,.2f} ✅")
        print(f"  manual_sales_amount: €{period.manual_sales_amount:,.2f} ✅")
        
    except AttributeError as e:
        print(f"\n❌ ERROR: {e}")
        print("\nThe 'manual_purchases_amount' field doesn't exist yet!")
        print("You need to run the migration first:")
        print("  python manage.py makemigrations stock_tracker")
        print("  python manage.py migrate")
        return False
    
    return True


def close_stocktake(stocktake):
    """Close the stocktake and verify calculations"""
    print("\n=== STEP 4: Closing Stocktake ===")
    
    stocktake.status = Stocktake.APPROVED
    stocktake.approved_at = timezone.now()
    # Note: You'd normally set approved_by to a Staff member
    stocktake.save()
    
    print(f"✅ Status changed to: {stocktake.status}")
    print(f"   Approved at: {stocktake.approved_at}")


def verify_calculations(stocktake):
    """Verify final calculations"""
    print("\n=== STEP 5: Verifying Calculations ===")
    
    # Clear cached property
    if hasattr(stocktake, '_total_cogs'):
        delattr(stocktake, '_total_cogs')
    
    # Refresh from DB
    stocktake = Stocktake.objects.get(id=stocktake.id)
    
    print(f"\nFINAL RESULTS:")
    print(f"Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"Total Revenue: €{stocktake.total_revenue:,.2f}")
    print(f"Gross Profit: €{stocktake.total_revenue - stocktake.total_cogs:,.2f}")
    print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    print(f"Pour Cost %: {stocktake.pour_cost_percentage:.2f}%")
    
    # Expected values
    expected_cogs = Decimal('19000.00')
    expected_revenue = Decimal('62000.00')
    expected_gp = ((expected_revenue - expected_cogs) / expected_revenue) * 100
    
    print(f"\nVERIFICATION:")
    cogs_match = stocktake.total_cogs == expected_cogs
    revenue_match = stocktake.total_revenue == expected_revenue
    
    print(f"✅ COGS: {cogs_match} (Expected: €{expected_cogs:,.2f})")
    print(f"✅ Revenue: {revenue_match} (Expected: €{expected_revenue:,.2f})")
    print(f"✅ Expected GP%: {expected_gp:.2f}%")
    
    if cogs_match and revenue_match:
        print("\n🎉 SUCCESS! All calculations are correct!")
    else:
        print("\n⚠️  WARNING: Values don't match expected!")


def full_workflow():
    """Execute complete workflow"""
    print("\n" + "="*60)
    print("OCTOBER 2025 REOPEN & REAL DATA TEST")
    print("="*60)
    
    try:
        # Step 1: Reopen
        stocktake = reopen_october()
        
        # Step 2: Clear test data
        clear_test_data(stocktake)
        
        # Step 3: Add period manual values
        success = add_period_manual_values()
        if not success:
            print("\n⛔ Workflow stopped - migration needed")
            return
        
        # Step 4: Close stocktake
        close_stocktake(stocktake)
        
        # Step 5: Verify
        verify_calculations(stocktake)
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        full_workflow()
    else:
        print("\n" + "="*60)
        print("October 2025 Reopen & Test Workflow")
        print("="*60)
        print("\nThis script will:")
        print("1. Reopen October 2025 stocktake (APPROVED → DRAFT)")
        print("2. Clear test data from lines")
        print("3. Add €19,000 purchases + €62,000 sales to StockPeriod")
        print("4. Close stocktake (DRAFT → APPROVED)")
        print("5. Verify calculations")
        print("\nRun with 'run' argument to execute:")
        print("  python reopen_and_test_october.py run")
        print("\n⚠️  Note: You must run migration first!")
        print("  python manage.py makemigrations stock_tracker")
        print("  python manage.py migrate")
        print("="*60)
