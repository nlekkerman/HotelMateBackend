"""
Insert manual purchase and sales values into October 2025 stocktake
- Manual purchases: €19,000 (COGS)
- Manual sales: €62,000 (Revenue)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod
from decimal import Decimal


def main():
    print("=" * 80)
    print("INSERT MANUAL VALUES - OCTOBER 2025")
    print("=" * 80)
    print()
    
    # Find October 2025 stocktake
    print("1. Finding October 2025 stocktake...")
    stocktake = Stocktake.objects.filter(
        period_start__year=2025,
        period_start__month=10
    ).first()
    
    if not stocktake:
        print("❌ October 2025 stocktake not found!")
        return
    
    print(f"✅ Found stocktake ID: {stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"   Status: {stocktake.status}")
    print()
    
    # Find the corresponding StockPeriod
    print("2. Finding October 2025 period...")
    period = StockPeriod.objects.filter(
        hotel=stocktake.hotel,
        start_date=stocktake.period_start,
        end_date=stocktake.period_end
    ).first()
    
    if not period:
        print("❌ October 2025 period not found!")
        return
    
    print(f"✅ Found period ID: {period.id}")
    print(f"   Period name: {period.period_name}")
    print()
    
    # Show current values
    print("3. Current values:")
    print(f"   StockPeriod.manual_sales_amount: €{period.manual_sales_amount or 0:,.2f}")
    print(f"   Stocktake.total_cogs: €{stocktake.total_cogs:,.2f}")
    print(f"   Stocktake.total_revenue: €{stocktake.total_revenue:,.2f}")
    print()
    
    # Set manual sales in StockPeriod
    print("4. Setting manual sales amount...")
    period.manual_sales_amount = Decimal('62000.00')
    period.save()
    print(f"✅ Set StockPeriod.manual_sales_amount = €62,000.00")
    print()
    
    # Note: For manual purchases, we need to set it on individual lines
    # or create Sale records. Let's check what approach to use.
    print("5. Note about manual purchases (€19,000 COGS):")
    print("   The COGS is typically tracked via:")
    print("   A) Sale records (itemized) - auto-calculated")
    print("   B) StocktakeLine.manual_purchases_value - per item")
    print()
    
    # Check if there are Sale records
    sales_count = stocktake.sales.count()
    print(f"   Current Sale records: {sales_count}")
    
    if sales_count > 0:
        print("   ✅ COGS already tracked via Sale records")
        print(f"   Current COGS: €{stocktake.total_cogs:,.2f}")
    else:
        print("   ⚠️  No Sale records found")
        print("   To track €19,000 COGS, you can:")
        print("   - Run test_october_financials.py (Option A) to create Sale records")
        print("   - Or set manual_purchases_value on individual lines")
    
    print()
    
    # Refresh and show final values
    stocktake.refresh_from_db()
    period.refresh_from_db()
    
    print("=" * 80)
    print("FINAL VALUES")
    print("=" * 80)
    print(f"StockPeriod.manual_sales_amount: €{period.manual_sales_amount:,.2f}")
    print(f"Stocktake.total_cogs: €{stocktake.total_cogs:,.2f}")
    print(f"Stocktake.total_revenue: €{stocktake.total_revenue:,.2f}")
    print()
    
    if stocktake.gross_profit_percentage:
        print(f"Gross Profit %: {stocktake.gross_profit_percentage}%")
    else:
        print("Gross Profit %: N/A (need COGS data)")
    
    if stocktake.pour_cost_percentage:
        print(f"Pour Cost %: {stocktake.pour_cost_percentage}%")
    else:
        print("Pour Cost %: N/A (need COGS data)")
    
    print()
    print("=" * 80)
    print("✅ MANUAL SALES VALUE INSERTED")
    print("=" * 80)
    print()
    print("API Endpoint:")
    print(f"GET /api/stock_tracker/hotel-killarney/stocktakes/{stocktake.id}/")
    print()
    print("Response will include:")
    print("- total_revenue: 62000.00")
    print("- total_cogs: (from Sale records)")
    print("- gross_profit_percentage")
    print("- pour_cost_percentage")
    print()


if __name__ == '__main__':
    main()
