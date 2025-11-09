"""
Test the complete workflow as if from frontend
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockPeriod, Stocktake

def test_workflow():
    """Test the complete workflow"""
    
    print("\n" + "="*60)
    print("TESTING COMPLETE WORKFLOW")
    print("="*60)
    
    # Step 1: Check current state
    print("\n📋 Step 1: Current State")
    print("-" * 60)
    stocktake = Stocktake.objects.get(id=5)
    period = StockPeriod.objects.get(id=7)
    
    print(f"Stocktake ID: {stocktake.id}")
    print(f"Status: {stocktake.status}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"\nPeriod ID: {period.id}")
    print(f"Period Name: {period.period_name}")
    print(f"Manual Purchases: €{period.manual_purchases_amount or 0:,.2f}")
    print(f"Manual Sales: €{period.manual_sales_amount or 0:,.2f}")
    
    # Step 2: Simulate frontend entering values
    print("\n\n💰 Step 2: Enter Manual Values (simulating frontend)")
    print("-" * 60)
    print("User enters:")
    print("  Total Purchases: €19,000.00")
    print("  Total Sales: €62,000.00")
    
    # Update period (this is what PATCH /periods/7/ would do)
    period.manual_purchases_amount = Decimal('19000.00')
    period.manual_sales_amount = Decimal('62000.00')
    period.save()
    print("✅ Period updated successfully")
    
    # Step 3: Check calculations BEFORE approving
    print("\n\n📊 Step 3: Preview Calculations (before closing)")
    print("-" * 60)
    # Clear cached property
    if hasattr(stocktake, '_total_cogs'):
        delattr(stocktake, '_total_cogs')
    stocktake = Stocktake.objects.get(id=5)
    
    print(f"Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"Total Revenue: €{stocktake.total_revenue:,.2f}")
    print(f"Gross Profit: €{stocktake.total_revenue - stocktake.total_cogs:,.2f}")
    print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    print(f"Pour Cost %: {stocktake.pour_cost_percentage:.2f}%")
    
    # Step 4: Approve stocktake
    print("\n\n✅ Step 4: Close/Approve Stocktake")
    print("-" * 60)
    print(f"Current Status: {stocktake.status}")
    
    user_choice = input("\nDo you want to close the stocktake now? (yes/no): ")
    
    if user_choice.lower() in ['yes', 'y']:
        from django.utils import timezone
        stocktake.status = Stocktake.APPROVED
        stocktake.approved_at = timezone.now()
        stocktake.save()
        print(f"✅ Status changed to: {stocktake.status}")
        print(f"✅ Approved at: {stocktake.approved_at}")
    else:
        print("ℹ️  Stocktake remains in DRAFT status")
    
    # Step 5: Final verification
    print("\n\n🎉 Step 5: Final Results")
    print("-" * 60)
    # Refresh
    if hasattr(stocktake, '_total_cogs'):
        delattr(stocktake, '_total_cogs')
    stocktake = Stocktake.objects.get(id=5)
    period = StockPeriod.objects.get(id=7)
    
    print(f"Stocktake Status: {stocktake.status}")
    print(f"\nPeriod Values:")
    print(f"  manual_purchases_amount: €{period.manual_purchases_amount:,.2f}")
    print(f"  manual_sales_amount: €{period.manual_sales_amount:,.2f}")
    print(f"\nCalculated Metrics:")
    print(f"  Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"  Total Revenue: €{stocktake.total_revenue:,.2f}")
    print(f"  Gross Profit: €{stocktake.total_revenue - stocktake.total_cogs:,.2f}")
    print(f"  Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    print(f"  Pour Cost %: {stocktake.pour_cost_percentage:.2f}%")
    
    # Verification
    print(f"\n✅ VERIFICATION:")
    cogs_ok = stocktake.total_cogs == Decimal('19000.00')
    revenue_ok = stocktake.total_revenue == Decimal('62000.00')
    gp_ok = abs(stocktake.gross_profit_percentage - 69.35) < 0.01
    
    print(f"  COGS correct: {cogs_ok}")
    print(f"  Revenue correct: {revenue_ok}")
    print(f"  GP% correct: {gp_ok}")
    
    if cogs_ok and revenue_ok and gp_ok:
        print("\n🎉 SUCCESS! Everything is working correctly!")
    else:
        print("\n⚠️  WARNING: Some values don't match expected!")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    test_workflow()
