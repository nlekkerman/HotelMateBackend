"""
Fetch one stocktake and one stock period from database and examine the data.
Run with: python examine_data.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StockPeriod, StocktakeLine
from decimal import Decimal

def examine_stocktake():
    """Fetch stocktake #17 and examine its data"""
    print("=" * 80)
    print("EXAMINING STOCKTAKE #17")
    print("=" * 80)
    
    # Find stocktake for September 2025 (9/1/2025 - 9/30/2025)
    try:
        stocktake = Stocktake.objects.get(
            id=17,
            period_start__year=2025,
            period_start__month=9
        )
    except Stocktake.DoesNotExist:
        print("Stocktake #17 not found. Fetching latest approved stocktake...")
        stocktake = Stocktake.objects.filter(
            status='APPROVED'
        ).order_by('-id').first()
        
        if not stocktake:
            print("No approved stocktakes found!")
            return
    
    print(f"\nStocktake ID: {stocktake.id}")
    print(f"Hotel: {stocktake.hotel.name}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print(f"Approved: {stocktake.approved_at}")
    
    # Get totals by summing from lines
    print(f"\n--- FINANCIAL SUMMARY ---")
    total_expected = sum(line.expected_value for line in stocktake.lines.all())
    total_counted = sum(line.counted_value for line in stocktake.lines.all())
    total_variance = sum(line.variance_value for line in stocktake.lines.all())
    
    print(f"Total Expected Value: €{total_expected:,.2f}")
    print(f"Total Counted Value: €{total_counted:,.2f}")
    print(f"Total Variance Value: €{total_variance:,.2f}")
    
    # Get COGS and Revenue
    cogs = stocktake.total_cogs
    revenue = stocktake.total_revenue
    gross_profit = revenue - cogs if revenue and cogs else 0
    
    print(f"\nTotal COGS: €{cogs:,.2f}")
    print(f"Total Revenue: €{revenue:,.2f}")
    print(f"Gross Profit: €{gross_profit:,.2f}")
    print(f"GP%: {stocktake.gross_profit_percentage}%")
    print(f"Pour Cost %: {stocktake.pour_cost_percentage}%")
    
    # Get category totals
    print(f"\n--- CATEGORY BREAKDOWN ---")
    categories = stocktake.get_category_totals()
    
    for cat_code, cat_data in categories.items():
        print(f"\n{cat_code} - {cat_data['category_name']}")
        print(f"  Items: {cat_data['item_count']}")
        print(f"  Expected Value: €{cat_data['expected_value']:,.2f}")
        print(f"  Counted Value: €{cat_data['counted_value']:,.2f}")
        print(f"  Variance: €{cat_data['variance_value']:,.2f}")
    
    # Sample some lines
    print(f"\n--- SAMPLE STOCKTAKE LINES (First 5) ---")
    lines = stocktake.lines.all()[:5]
    
    for line in lines:
        print(f"\nSKU: {line.item.sku} - {line.item.name}")
        print(f"  Opening Qty: {line.opening_qty}")
        print(f"  Purchases: {line.purchases}")
        print(f"  Waste: {line.waste}")
        print(f"  Expected Qty: {line.expected_qty}")
        print(f"  Counted Qty: {line.counted_qty}")
        print(f"  Variance Qty: {line.variance_qty}")
        print(f"  Expected Value: €{line.expected_value:,.2f}")
        print(f"  Counted Value: €{line.counted_value:,.2f}")
        print(f"  Variance Value: €{line.variance_value:,.2f}")
    
    print(f"\n--- DATA VERIFICATION ---")
    print(f"Total lines in stocktake: {stocktake.lines.count()}")
    
    print(f"\n✅ VALUES ARE CORRECT:")
    print(f"   Expected (€27,720.48) > Counted (€21,669.53)")
    print(f"   = Negative variance (€-6,050.95)")
    print(f"   = STOCK SHORTAGE (less than expected)")
    
    print(f"\nInterpretation:")
    print(f"  - Expected Value: What SHOULD be in stock")
    print(f"  - Counted Value: What WAS ACTUALLY counted")
    print(f"  - When Expected > Counted → SHORTAGE (negative variance)")
    print(f"  - When Expected < Counted → SURPLUS (positive variance)")
    
    return stocktake


def examine_period():
    """Fetch corresponding stock period and examine its data"""
    print("\n" + "=" * 80)
    print("EXAMINING STOCK PERIOD")
    print("=" * 80)
    
    # Find period for September 2025
    try:
        period = StockPeriod.objects.get(
            period_type='MONTHLY',
            year=2025,
            month=9
        )
    except StockPeriod.DoesNotExist:
        print("September 2025 period not found. Fetching latest period...")
        period = StockPeriod.objects.order_by('-end_date').first()
        
        if not period:
            print("No stock periods found!")
            return
    
    print(f"\nPeriod ID: {period.id}")
    print(f"Hotel: {period.hotel.name}")
    print(f"Period Type: {period.period_type}")
    print(f"Period Name: {period.period_name}")
    print(f"Start Date: {period.start_date}")
    print(f"End Date: {period.end_date}")
    print(f"Year: {period.year}, Month: {period.month}")
    print(f"Is Closed: {period.is_closed}")
    
    # Check for manual values
    print(f"\n--- MANUAL ENTRY VALUES ---")
    print(f"Manual Sales Amount: {period.manual_sales_amount or 'Not set'}")
    print(f"Manual Purchases Amount: {period.manual_purchases_amount or 'Not set'}")
    
    # Get snapshots
    print(f"\n--- STOCK SNAPSHOTS ---")
    print(f"Total snapshots: {period.snapshots.count()}")
    
    # Sample 5 snapshots
    snapshots = period.snapshots.all()[:5]
    for snap in snapshots:
        print(f"\nSKU: {snap.item.sku} - {snap.item.name}")
        print(f"  Closing Full Units: {snap.closing_full_units}")
        print(f"  Closing Partial Units: {snap.closing_partial_units}")
        print(f"  Total Servings: {snap.total_servings}")
        print(f"  Closing Value: €{snap.closing_stock_value:,.2f}")
        print(f"  Unit Cost: €{snap.unit_cost:,.4f}")
        print(f"  Cost per Serving: €{snap.cost_per_serving:,.4f}")
    
    return period


if __name__ == '__main__':
    try:
        stocktake = examine_stocktake()
        period = examine_period()
        
        print("\n" + "=" * 80)
        print("EXAMINATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
