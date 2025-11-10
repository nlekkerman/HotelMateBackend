"""
Script to fetch real periods and stocktakes from September, October, November.
Display purchase costs, sales, profit, stock values, and close November with mock data.
"""
import os
import django
from decimal import Decimal
from datetime import date, datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake, StocktakeLine, Sale
from hotel.models import Hotel

def display_period_data(period, stocktake=None):
    """Display comprehensive period financial data"""
    print(f"\n{'='*80}")
    print(f"PERIOD: {period.period_name}")
    print(f"{'='*80}")
    print(f"Date Range: {period.start_date} to {period.end_date}")
    print(f"Status: {'CLOSED' if period.is_closed else 'OPEN'}")
    if period.is_closed and period.closed_at:
        print(f"Closed At: {period.closed_at}")
        print(f"Closed By: {period.closed_by}")
    print(f"-" * 80)
    
    # Display StockPeriod manual values (if any)
    if period.manual_sales_amount:
        print(f"Manual Sales Amount: €{period.manual_sales_amount:,.2f}")
    if period.manual_purchases_amount:
        print(f"Manual Purchases Amount: €{period.manual_purchases_amount:,.2f}")
    
    # If no stocktake, try to find one
    if not stocktake:
        try:
            stocktake = Stocktake.objects.get(
                hotel=period.hotel,
                period_start=period.start_date,
                period_end=period.end_date
            )
        except Stocktake.DoesNotExist:
            print("\n⚠️  No stocktake found for this period")
            return
    
    # Display Stocktake data
    print(f"\nSTOCKTAKE:")
    print(f"Status: {stocktake.status}")
    print(f"Created: {stocktake.created_at}")
    if stocktake.approved_at:
        print(f"Approved At: {stocktake.approved_at}")
        print(f"Approved By: {stocktake.approved_by}")
    
    # Financial metrics
    print(f"\n{'='*80}")
    print(f"FINANCIAL SUMMARY")
    print(f"{'='*80}")
    
    total_revenue = stocktake.total_revenue
    total_cogs = stocktake.total_cogs
    
    print(f"Total Revenue (Sales): €{total_revenue:,.2f}")
    print(f"Total COGS (Purchases + Waste): €{total_cogs:,.2f}")
    
    if total_revenue and total_revenue > 0:
        gross_profit = total_revenue - total_cogs
        print(f"Gross Profit: €{gross_profit:,.2f}")
        print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
        print(f"Pour Cost %: {stocktake.pour_cost_percentage:.2f}%")
    
    # Stock value
    print(f"\n{'='*80}")
    print(f"STOCK VALUATION")
    print(f"{'='*80}")
    
    lines = stocktake.lines.select_related('item', 'item__category').all()
    
    total_opening_value = sum(line.opening_qty * line.valuation_cost for line in lines)
    total_expected_value = sum(line.expected_value for line in lines)
    total_counted_value = sum(line.counted_value for line in lines)
    total_variance_value = sum(line.variance_value for line in lines)
    
    print(f"Opening Stock Value: €{total_opening_value:,.2f}")
    print(f"Expected Closing Stock Value: €{total_expected_value:,.2f}")
    print(f"Counted Closing Stock Value: €{total_counted_value:,.2f}")
    print(f"Variance: €{total_variance_value:,.2f}")
    
    # Category breakdown
    print(f"\n{'='*80}")
    print(f"BREAKDOWN BY CATEGORY")
    print(f"{'='*80}")
    
    category_totals = stocktake.get_category_totals()
    
    for cat_code, cat_data in sorted(category_totals.items()):
        print(f"\n{cat_data['category_name']} ({cat_code}):")
        print(f"  Items: {cat_data['item_count']}")
        print(f"  Opening Qty: {cat_data['opening_qty']:,.2f}")
        print(f"  Purchases: {cat_data['purchases']:,.2f}")
        print(f"  Waste: {cat_data['waste']:,.2f}")
        print(f"  Expected Qty: {cat_data['expected_qty']:,.2f}")
        print(f"  Counted Qty: {cat_data['counted_qty']:,.2f}")
        print(f"  Variance Qty: {cat_data['variance_qty']:,.2f}")
        print(f"  Expected Value: €{cat_data['expected_value']:,.2f}")
        print(f"  Counted Value: €{cat_data['counted_value']:,.2f}")
        print(f"  Variance Value: €{cat_data['variance_value']:,.2f}")
        if cat_data['manual_purchases_value'] > 0:
            print(f"  Manual Purchases: €{cat_data['manual_purchases_value']:,.2f}")


def close_november_with_mock_data(hotel):
    """Close November period with mock data"""
    print(f"\n{'='*80}")
    print(f"CLOSING NOVEMBER 2024 WITH MOCK DATA")
    print(f"{'='*80}")
    
    # Get or create November period
    nov_period, created = StockPeriod.objects.get_or_create(
        hotel=hotel,
        period_type=StockPeriod.MONTHLY,
        year=2024,
        month=11,
        defaults={
            'start_date': date(2024, 11, 1),
            'end_date': date(2024, 11, 30),
            'period_name': 'November 2024'
        }
    )
    
    if created:
        print(f"✓ Created November 2024 period")
    else:
        print(f"✓ November 2024 period already exists")
    
    # Check if stocktake exists
    try:
        nov_stocktake = Stocktake.objects.get(
            hotel=hotel,
            period_start=nov_period.start_date,
            period_end=nov_period.end_date
        )
        print(f"✓ Stocktake exists with status: {nov_stocktake.status}")
    except Stocktake.DoesNotExist:
        print(f"✗ No stocktake found - creating with mock data")
        nov_stocktake = Stocktake.objects.create(
            hotel=hotel,
            period_start=nov_period.start_date,
            period_end=nov_period.end_date,
            status=Stocktake.DRAFT
        )
    
    # Add mock financial data to the period
    mock_sales = Decimal('25000.00')  # €25,000 sales
    mock_purchases = Decimal('7500.00')  # €7,500 purchases (30% pour cost)
    
    nov_period.manual_sales_amount = mock_sales
    nov_period.manual_purchases_amount = mock_purchases
    nov_period.save()
    
    print(f"\n✓ Added mock financial data:")
    print(f"  Mock Sales: €{mock_sales:,.2f}")
    print(f"  Mock Purchases: €{mock_purchases:,.2f}")
    print(f"  Pour Cost %: {(mock_purchases / mock_sales * 100):.2f}%")
    
    # Get October's closing stock as November's opening
    try:
        oct_period = StockPeriod.objects.get(
            hotel=hotel,
            year=2024,
            month=10
        )
        oct_stocktake = Stocktake.objects.get(
            hotel=hotel,
            period_start=oct_period.start_date,
            period_end=oct_period.end_date
        )
        
        # Populate November lines from October closing
        oct_lines = oct_stocktake.lines.select_related('item').all()
        nov_lines_created = 0
        
        for oct_line in oct_lines:
            # Use October's closing as November's opening
            nov_line, created = StocktakeLine.objects.get_or_create(
                stocktake=nov_stocktake,
                item=oct_line.item,
                defaults={
                    'opening_qty': oct_line.counted_qty,
                    'purchases': Decimal('50.00'),  # Mock purchases
                    'waste': Decimal('2.00'),  # Mock waste
                    'counted_full_units': oct_line.counted_full_units,
                    'counted_partial_units': oct_line.counted_partial_units,
                    'valuation_cost': oct_line.valuation_cost
                }
            )
            if created:
                nov_lines_created += 1
        
        print(f"\n✓ Created {nov_lines_created} stocktake lines from October closing")
        
    except (StockPeriod.DoesNotExist, Stocktake.DoesNotExist):
        print(f"\n⚠️  Could not find October data to populate November opening stock")
    
    # Approve and close November
    if nov_stocktake.status != Stocktake.APPROVED:
        nov_stocktake.status = Stocktake.APPROVED
        nov_stocktake.approved_at = datetime.now()
        nov_stocktake.save()
        print(f"\n✓ Approved November stocktake")
    
    if not nov_period.is_closed:
        nov_period.is_closed = True
        nov_period.closed_at = datetime.now()
        nov_period.save()
        print(f"✓ Closed November period")
    
    return nov_period, nov_stocktake


def main():
    print(f"\n{'#'*80}")
    print(f"# STOCK TRACKER - PERIOD & FINANCIAL DATA ANALYSIS")
    print(f"# September, October, November 2024")
    print(f"{'#'*80}")
    
    # Get the hotel
    try:
        hotel = Hotel.objects.first()
        print(f"\nHotel: {hotel.name}")
    except Exception as e:
        print(f"Error: Could not find hotel - {e}")
        return
    
    # Fetch September period
    print(f"\n\n{'*'*80}")
    print(f"* SEPTEMBER 2024 - REAL DATA")
    print(f"{'*'*80}")
    try:
        sept_period = StockPeriod.objects.get(
            hotel=hotel,
            year=2024,
            month=9
        )
        display_period_data(sept_period)
    except StockPeriod.DoesNotExist:
        print(f"\n⚠️  September 2024 period not found in database")
    
    # Fetch October period
    print(f"\n\n{'*'*80}")
    print(f"* OCTOBER 2024 - REAL DATA")
    print(f"{'*'*80}")
    try:
        oct_period = StockPeriod.objects.get(
            hotel=hotel,
            year=2024,
            month=10
        )
        display_period_data(oct_period)
    except StockPeriod.DoesNotExist:
        print(f"\n⚠️  October 2024 period not found in database")
    
    # Check November and close with mock data
    print(f"\n\n{'*'*80}")
    print(f"* NOVEMBER 2024 - CLOSING WITH MOCK DATA")
    print(f"{'*'*80}")
    
    nov_period, nov_stocktake = close_november_with_mock_data(hotel)
    display_period_data(nov_period, nov_stocktake)
    
    # Summary comparison
    print(f"\n\n{'#'*80}")
    print(f"# COMPARATIVE SUMMARY - SEPTEMBER, OCTOBER, NOVEMBER 2024")
    print(f"{'#'*80}")
    
    periods = [
        ('September', 9),
        ('October', 10),
        ('November', 11)
    ]
    
    print(f"\n{'Month':<15} {'Sales':<15} {'COGS':<15} {'Profit':<15} {'GP%':<10} {'Pour Cost%':<12}")
    print(f"{'-'*80}")
    
    for month_name, month_num in periods:
        try:
            period = StockPeriod.objects.get(hotel=hotel, year=2024, month=month_num)
            stocktake = Stocktake.objects.get(
                hotel=hotel,
                period_start=period.start_date,
                period_end=period.end_date
            )
            
            revenue = stocktake.total_revenue
            cogs = stocktake.total_cogs
            profit = revenue - cogs if revenue else 0
            gp_pct = stocktake.gross_profit_percentage or 0
            pour_cost = stocktake.pour_cost_percentage or 0
            
            print(f"{month_name:<15} €{revenue:<14,.2f} €{cogs:<14,.2f} €{profit:<14,.2f} {gp_pct:<9.2f}% {pour_cost:<11.2f}%")
        except (StockPeriod.DoesNotExist, Stocktake.DoesNotExist):
            print(f"{month_name:<15} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'N/A':<10} {'N/A':<12}")
    
    print(f"\n{'#'*80}")
    print(f"# SCRIPT COMPLETED")
    print(f"{'#'*80}\n")


if __name__ == '__main__':
    main()
