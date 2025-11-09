"""
Check and update October 2025 StockPeriod with manual values
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from datetime import date
from stock_tracker.models import StockPeriod, Stocktake

def check_october_period():
    """Check if October 2025 period exists"""
    
    print("\n=== Checking October 2025 Stock Period ===\n")
    
    # Find October 2025 periods
    october_periods = StockPeriod.objects.filter(
        start_date=date(2025, 10, 1),
        end_date=date(2025, 10, 31)
    )
    
    print(f"Found {october_periods.count()} October 2025 period(s)\n")
    
    for period in october_periods:
        print(f"Period ID: {period.id}")
        print(f"Hotel: {period.hotel.name}")
        print(f"Dates: {period.start_date} to {period.end_date}")
        print(f"Period Type: {period.period_type}")
        print(f"Manual Sales Amount: €{period.manual_sales_amount or 0:,.2f}")
        print("-" * 50)
    
    # Check if stocktake exists for October
    stocktake = Stocktake.objects.filter(
        period_start=date(2025, 10, 1),
        period_end=date(2025, 10, 31)
    ).first()
    
    if stocktake:
        print(f"\nStocktake ID: {stocktake.id}")
        print(f"Status: {stocktake.status}")
        print(f"Total COGS: €{stocktake.total_cogs:,.2f}")
        print(f"Total Revenue: €{stocktake.total_revenue:,.2f}")
        print(f"Gross Profit %: {stocktake.gross_profit_percentage:.2f}%")
    
    return october_periods

def add_manual_values_to_period():
    """Add €19,000 purchases and €62,000 sales to October period"""
    
    print("\n=== Adding Manual Values to October 2025 Period ===\n")
    
    # Find or create October 2025 period
    october_periods = StockPeriod.objects.filter(
        start_date=date(2025, 10, 1),
        end_date=date(2025, 10, 31)
    )
    
    if not october_periods.exists():
        print("❌ No October 2025 period found!")
        print("\nTo create one, you need to:")
        print("1. Know which hotel this is for")
        print("2. Create the period via API or admin")
        return
    
    for period in october_periods:
        print(f"Updating Period ID: {period.id} ({period.hotel.name})")
        
        # Note: StockPeriod only has manual_sales_amount field
        # Purchases are tracked via StocktakeLine.manual_purchases_value
        period.manual_sales_amount = Decimal('62000.00')
        period.save()
        
        print(f"✅ Set manual_sales_amount = €62,000.00")
        print(f"\nNote: Purchase amount (€19,000) should be entered on")
        print(f"      StocktakeLine.manual_purchases_value fields")
        
        # Check related stocktake
        stocktake = Stocktake.objects.filter(
            hotel=period.hotel,
            period_start=period.start_date,
            period_end=period.end_date
        ).first()
        
        if stocktake:
            print(f"\n📊 Related Stocktake ID: {stocktake.id}")
            print(f"   Total Revenue: €{stocktake.total_revenue:,.2f}")
            print(f"   Total COGS: €{stocktake.total_cogs:,.2f}")

def show_options():
    """Show how to add values"""
    print("\n" + "="*60)
    print("HOW TO ADD MANUAL VALUES FOR OCTOBER 2025")
    print("="*60)
    print("\nOption 1: Add to StockPeriod (Revenue Only)")
    print("-" * 60)
    print("StockPeriod only has 'manual_sales_amount' field")
    print("Use this for total revenue: €62,000")
    print("\nCode example:")
    print("  period = StockPeriod.objects.get(id=X)")
    print("  period.manual_sales_amount = Decimal('62000.00')")
    print("  period.save()")
    
    print("\n\nOption 2: Add to StocktakeLine (All Values)")
    print("-" * 60)
    print("StocktakeLine has three manual fields:")
    print("  • manual_purchases_value  (€19,000 total)")
    print("  • manual_waste_value      (if any)")
    print("  • manual_sales_value      (€62,000 total)")
    print("\nDistribute across lines, e.g.:")
    print("  line.manual_purchases_value = Decimal('3800.00')  # per line")
    print("  line.manual_waste_value = Decimal('500.00')       # per line")
    print("  line.manual_sales_value = Decimal('12400.00')     # per line")
    print("  line.save()")
    
    print("\n\nCalculation Priority:")
    print("-" * 60)
    print("Revenue: manual_sales_value → manual_sales_amount → Sale records")
    print("COGS:    manual_purchases_value + manual_waste_value → Sale records")
    print("\n")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'add':
            add_manual_values_to_period()
        elif sys.argv[1] == 'help':
            show_options()
    else:
        check_october_period()
        print("\n" + "="*60)
        print("Run with 'add' to add manual values to period")
        print("Run with 'help' to see all options")
        print("="*60)
