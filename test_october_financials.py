"""
Test October 2025 Stocktake Financial Operations

This script demonstrates:
1. Fetching October 2025 stocktake
2. Adding purchase costs (via Sale model COGS)
3. Adding sales revenue (via StockPeriod.manual_sales_amount)
4. Calculating and displaying GP% and Pour Cost%

Two approaches for tracking financials:
A) Itemized Sales: Create Sale records with cost & revenue per item
B) Manual Total: Set StockPeriod.manual_sales_amount for period total
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import (
    Stocktake, StocktakeLine, Sale, StockPeriod
)
from decimal import Decimal
from django.db.models import Sum, F

def display_stocktake_summary(stocktake):
    """Display stocktake financial summary"""
    print("=" * 80)
    print("📊 STOCKTAKE FINANCIAL SUMMARY")
    print("=" * 80)
    print(f"Stocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"Status: {stocktake.status}")
    print(f"Total Lines: {stocktake.lines.count()}")
    print()
    
    print("💰 FINANCIAL METRICS:")
    print(f"   Total COGS: €{stocktake.total_cogs:,.2f}")
    print(f"   Total Revenue: €{stocktake.total_revenue:,.2f}")
    
    if stocktake.gross_profit_percentage:
        print(f"   Gross Profit %: {stocktake.gross_profit_percentage}%")
    else:
        print(f"   Gross Profit %: N/A (no revenue data)")
    
    if stocktake.pour_cost_percentage:
        print(f"   Pour Cost %: {stocktake.pour_cost_percentage}%")
    else:
        print(f"   Pour Cost %: N/A (no revenue data)")
    print()

def approach_a_itemized_sales(stocktake):
    """
    Approach A: Create itemized Sale records
    Each item sold has its own record with cost and revenue
    Uses real values: €19,000 COGS, €62,000 Revenue
    """
    print("=" * 80)
    print("APPROACH A: ITEMIZED SALES")
    print("=" * 80)
    print("Creating Sale records based on consumption...")
    print("Target: €19,000 COGS | €62,000 Revenue")
    print()
    
    # Check existing sales
    existing_sales = Sale.objects.filter(stocktake=stocktake)
    print(f"Existing sales records: {existing_sales.count()}")
    
    if existing_sales.exists():
        response = input(
            "Delete existing sales and create new ones? (yes/no): "
        )
        if response.lower() == 'yes':
            deleted = existing_sales.delete()
            print(f"✅ Deleted {deleted[0]} sales records")
            print()
        else:
            print("❌ Keeping existing sales")
            return
    
    # Get all lines with consumption (expected > counted)
    lines = stocktake.lines.all()
    
    print(f"Analyzing {lines.count()} items for consumption...")
    print()
    
    # Calculate actual consumption for each item
    consumption_data = []
    total_consumption_value = Decimal('0.00')
    
    for line in lines:
        # Consumption = Expected - Counted (what was sold/used)
        expected_qty = line.expected_qty
        counted_qty = line.counted_qty
        consumed_qty = expected_qty - counted_qty
        
        if consumed_qty > 0:  # Only items with consumption
            consumption_value = consumed_qty * line.valuation_cost
            consumption_data.append({
                'line': line,
                'consumed_qty': consumed_qty,
                'unit_cost': line.valuation_cost,
                'consumption_value': consumption_value
            })
            total_consumption_value += consumption_value
    
    print(f"Found {len(consumption_data)} items with consumption")
    print(f"Total consumption value: €{total_consumption_value:,.2f}")
    print()
    
    # Target values
    target_cogs = Decimal('19000.00')
    target_revenue = Decimal('62000.00')
    
    # Calculate scaling factor to match target COGS
    if total_consumption_value > 0:
        scale_factor = target_cogs / total_consumption_value
    else:
        print("❌ No consumption found!")
        return
    
    # Calculate markup to achieve target revenue
    markup = target_revenue / target_cogs
    
    print(f"Scaling consumption by {scale_factor:.2f}x to match €19,000")
    print(f"Applying markup of {markup:.2f}x to achieve €62,000 revenue")
    print()
    
    confirm = input("Create sales with these values? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print()
    print("Creating sales records...")
    print()
    
    sales_created = []
    total_cost = Decimal('0.00')
    total_revenue = Decimal('0.00')
    
    for idx, data in enumerate(consumption_data[:50], 1):  # Top 50 items
        line = data['line']
        
        # Scale consumption to match target
        scaled_qty = data['consumed_qty'] * scale_factor
        unit_cost = data['unit_cost']
        unit_price = unit_cost * markup
        
        # Create sale record
        sale = Sale.objects.create(
            stocktake=stocktake,
            item=line.item,
            quantity=scaled_qty,
            unit_cost=unit_cost,
            unit_price=unit_price,
            sale_date=stocktake.period_start,
            notes=f"October sales - Item {idx}"
        )
        
        sales_created.append(sale)
        total_cost += sale.total_cost
        total_revenue += sale.total_revenue
        
        if idx <= 10:  # Show first 10
            print(f"   {idx}. {line.item.sku[:20]}: {scaled_qty:.2f} servings")
            print(f"      Cost: €{sale.total_cost:.2f} | "
                  f"Revenue: €{sale.total_revenue:.2f}")
    
    if len(consumption_data) > 50:
        print(f"   ... and {len(consumption_data) - 50} more items")
    
    print()
    print(f"✅ Created {len(sales_created)} sales records")
    print(f"   Total COGS: €{total_cost:,.2f}")
    print(f"   Total Revenue: €{total_revenue:,.2f}")
    
    gp = ((total_revenue - total_cost) / total_revenue * 100) if total_revenue > 0 else 0
    print(f"   Gross Profit %: {gp:.2f}%")
    print()

def approach_b_manual_total(stocktake):
    """
    Approach B: Set manual total sales amount in StockPeriod
    Use when you have period total but not itemized sales
    Default: €62,000
    """
    print("=" * 80)
    print("APPROACH B: MANUAL SALES TOTAL")
    print("=" * 80)
    print("Setting manual_sales_amount in StockPeriod...")
    print()
    
    # Get the period
    period = StockPeriod.objects.filter(
        hotel=stocktake.hotel,
        start_date=stocktake.period_start,
        end_date=stocktake.period_end
    ).first()
    
    if not period:
        print("❌ No StockPeriod found for this stocktake")
        return
    
    print(f"Period: {period.period_name}")
    current = period.manual_sales_amount or 0
    print(f"Current manual_sales_amount: €{current:,.2f}")
    print()
    
    # Default to €62,000
    print("Enter manual sales amount")
    manual_amount = input("Press Enter for €62,000.00 or type amount: ")
    
    if not manual_amount:
        manual_amount = "62000.00"
    
    try:
        period.manual_sales_amount = Decimal(manual_amount)
        period.save()
        amount = period.manual_sales_amount
        print(f"✅ Set manual_sales_amount to €{amount:,.2f}")
        print()
        
        # Show GP% if COGS exists
        if stocktake.total_cogs > 0:
            gp_pct = stocktake.gross_profit_percentage
            print(f"   Gross Profit %: {gp_pct}%")
            print()
    except Exception as e:
        print(f"❌ Invalid amount: {e}")
        return

def calculate_totals_from_variance(stocktake):
    """
    Alternative: Calculate COGS from variance
    COGS = Opening + Purchases - Waste - Counted (consumption)
    """
    print("=" * 80)
    print("APPROACH C: CALCULATE COGS FROM CONSUMPTION")
    print("=" * 80)
    print("Calculating cost of goods sold from consumption...")
    print()
    
    # Get all lines
    lines = stocktake.lines.all()
    
    total_consumption_qty = Decimal('0.0000')
    total_consumption_value = Decimal('0.00')
    
    for line in lines:
        # Consumption = Expected - Counted
        # Expected = Opening + Purchases - Waste
        expected_qty = line.expected_qty
        counted_qty = line.counted_qty
        
        consumption_qty = expected_qty - counted_qty
        consumption_value = consumption_qty * line.valuation_cost
        
        total_consumption_qty += consumption_qty
        total_consumption_value += consumption_value
    
    print(f"Total Consumption (servings): {total_consumption_qty:,.2f}")
    print(f"Total COGS from consumption: €{total_consumption_value:,.2f}")
    print()
    print("Note: This shows what was consumed/sold based on stock variance")
    print("To get GP%, you still need to enter revenue (Approach A or B)")
    print()

def main():
    print("=" * 80)
    print("🧪 OCTOBER 2025 STOCKTAKE - FINANCIAL OPERATIONS TEST")
    print("=" * 80)
    print()
    
    # Fetch October 2025 stocktake
    print("1️⃣  Fetching October 2025 stocktake...")
    stocktake = Stocktake.objects.filter(
        period_start__year=2025,
        period_start__month=10
    ).first()
    
    if not stocktake:
        print("❌ October 2025 stocktake not found!")
        print()
        print("Available stocktakes:")
        for st in Stocktake.objects.all().order_by('-period_start')[:5]:
            print(f"   - {st.period_start} to {st.period_end}")
        return
    
    print(f"✅ Found stocktake ID: {stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print(f"   Status: {stocktake.status}")
    print()
    
    # Display current state
    display_stocktake_summary(stocktake)
    
    # Menu
    while True:
        print("=" * 80)
        print("SELECT OPERATION:")
        print("=" * 80)
        print("A. Create itemized sales (Sale records)")
        print("B. Set manual sales total (StockPeriod.manual_sales_amount)")
        print("C. Calculate COGS from consumption")
        print("D. View current summary")
        print("E. Clear all sales data")
        print("Q. Quit")
        print()
        
        choice = input("Your choice: ").strip().upper()
        print()
        
        if choice == 'A':
            approach_a_itemized_sales(stocktake)
            stocktake.refresh_from_db()
            display_stocktake_summary(stocktake)
        
        elif choice == 'B':
            approach_b_manual_total(stocktake)
            stocktake.refresh_from_db()
            display_stocktake_summary(stocktake)
        
        elif choice == 'C':
            calculate_totals_from_variance(stocktake)
        
        elif choice == 'D':
            stocktake.refresh_from_db()
            display_stocktake_summary(stocktake)
        
        elif choice == 'E':
            # Clear sales data
            print("🧹 Clearing sales data...")
            sales = Sale.objects.filter(stocktake=stocktake)
            if sales.exists():
                deleted = sales.delete()
                print(f"✅ Deleted {deleted[0]} sales records")
            
            period = StockPeriod.objects.filter(
                hotel=stocktake.hotel,
                start_date=stocktake.period_start,
                end_date=stocktake.period_end
            ).first()
            if period and period.manual_sales_amount:
                period.manual_sales_amount = None
                period.save()
                print("✅ Cleared manual_sales_amount")
            
            print()
            stocktake.refresh_from_db()
            display_stocktake_summary(stocktake)
        
        elif choice == 'Q':
            print("=" * 80)
            print("✅ TEST COMPLETE")
            print("=" * 80)
            print()
            print("📝 SUMMARY:")
            print()
            print("What we have for financial tracking:")
            print("✅ Sale model - for itemized sales with cost & revenue")
            print("✅ StockPeriod.manual_sales_amount - for period total revenue")
            print("✅ Stocktake.total_cogs - auto-calculated from Sale records")
            print("✅ Stocktake.total_revenue - from Sale records OR manual_sales_amount")
            print("✅ Stocktake.gross_profit_percentage - auto-calculated GP%")
            print("✅ Stocktake.pour_cost_percentage - auto-calculated Pour Cost%")
            print()
            print("API Endpoints:")
            print(f"   GET /api/stock_tracker/hotel-killarney/stocktakes/{stocktake.id}/")
            print("   Response includes: total_cogs, total_revenue, gross_profit_percentage, pour_cost_percentage")
            print()
            break
        
        else:
            print("❌ Invalid choice")
            print()

if __name__ == '__main__':
    main()
