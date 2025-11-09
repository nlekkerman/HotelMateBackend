"""
Reopen September 2025 and add financial values
Cost of Stock: €18,265.03
Revenue/Profit: €51,207.00
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockPeriod, Stocktake
from decimal import Decimal

# Find September 2025 period
try:
    september_period = StockPeriod.objects.get(
        period_name__icontains='September 2025'
    )
    print(f"\n✅ Found: {september_period.period_name}")
    print(f"   ID: {september_period.id}")
    print(f"   Dates: {september_period.start_date} to {september_period.end_date}")
    print(f"   Current Status: {'CLOSED' if september_period.is_closed else 'OPEN'}")
    
    # Reopen the period if closed
    if september_period.is_closed:
        september_period.is_closed = False
        september_period.save()
        print(f"\n✅ September 2025 period REOPENED")
    
    # Add financial values
    print(f"\n📊 Adding Financial Values:")
    print(f"   Cost of Stock (COGS): €18,265.03")
    print(f"   Revenue: €51,207.00")
    
    september_period.manual_purchases_amount = Decimal('18265.03')
    september_period.manual_sales_amount = Decimal('51207.00')
    september_period.save()
    
    print(f"\n✅ Financial values saved:")
    print(f"   manual_purchases_amount: €{september_period.manual_purchases_amount:,.2f}")
    print(f"   manual_sales_amount: €{september_period.manual_sales_amount:,.2f}")
    
    # Calculate GP%
    if september_period.manual_sales_amount > 0:
        gross_profit = september_period.manual_sales_amount - september_period.manual_purchases_amount
        gp_percentage = (gross_profit / september_period.manual_sales_amount) * 100
        print(f"\n💰 Calculated Metrics:")
        print(f"   Gross Profit: €{gross_profit:,.2f}")
        print(f"   GP%: {gp_percentage:.2f}%")
        print(f"   Pour Cost%: {100 - gp_percentage:.2f}%")
    
    # Check if there's a stocktake for September
    try:
        september_stocktake = Stocktake.objects.get(
            period_start=september_period.start_date,
            period_end=september_period.end_date
        )
        print(f"\n✅ Found September 2025 Stocktake:")
        print(f"   ID: {september_stocktake.id}")
        print(f"   Status: {september_stocktake.status}")
        
        if september_stocktake.status == Stocktake.APPROVED:
            september_stocktake.status = Stocktake.DRAFT
            september_stocktake.approved_at = None
            september_stocktake.approved_by = None
            september_stocktake.save()
            print(f"   ✅ Stocktake REOPENED to DRAFT status")
        
        # Display stocktake financials (these will use the period manual values)
        print(f"\n📊 Stocktake Financial Summary:")
        print(f"   Total COGS: €{september_stocktake.total_cogs:,.2f}")
        print(f"   Total Revenue: €{september_stocktake.total_revenue:,.2f}")
        if september_stocktake.gross_profit_percentage:
            print(f"   GP%: {september_stocktake.gross_profit_percentage}%")
        if september_stocktake.pour_cost_percentage:
            print(f"   Pour Cost%: {september_stocktake.pour_cost_percentage}%")
            
    except Stocktake.DoesNotExist:
        print(f"\n⚠️  No stocktake found for September 2025")
        print(f"   You may need to create one if needed")
    
    print(f"\n✅ September 2025 is now ready for editing!\n")
    
except StockPeriod.DoesNotExist:
    print("\n❌ September 2025 period not found!")
    print("\nAvailable periods:")
    all_periods = StockPeriod.objects.all().order_by('start_date')
    for p in all_periods:
        print(f"   • {p.period_name} ({p.start_date} to {p.end_date})")
    print("\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
