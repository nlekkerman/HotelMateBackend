"""
Script to check all sales grouped by stocktake period
Shows which periods have sales saved
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale, Stocktake
from django.db.models import Count, Sum
from decimal import Decimal

print("=" * 80)
print("ALL SALES - GROUPED BY DATE AND STOCKTAKE")
print("=" * 80)

# Get total sales count
total_sales = Sale.objects.count()
print(f"\n📊 Total Sales in Database: {total_sales}\n")

if total_sales == 0:
    print("❌ NO SALES FOUND IN DATABASE\n")
else:
    # 1. Sales linked to stocktake periods
    print("=" * 80)
    print("SALES LINKED TO STOCKTAKE PERIODS")
    print("=" * 80)
    
    sales_by_stocktake = Sale.objects.filter(
        stocktake__isnull=False
    ).values(
        'stocktake__id',
        'stocktake__period_start',
        'stocktake__period_end'
    ).annotate(
        count=Count('id'),
        total_revenue=Sum('total_revenue'),
        total_cost=Sum('total_cost')
    ).order_by('stocktake__period_start')
    
    if not sales_by_stocktake:
        print("\n❌ No sales linked to stocktake periods\n")
    else:
        print(f"\n✅ Found {len(sales_by_stocktake)} period(s):\n")
        
        for idx, period in enumerate(sales_by_stocktake, 1):
            start = period['stocktake__period_start']
            end = period['stocktake__period_end']
            count = period['count']
            revenue = period['total_revenue'] or Decimal('0.00')
            cost = period['total_cost'] or Decimal('0.00')
            profit = revenue - cost
            
            # Determine month name
            month_name = start.strftime('%B %Y') if start else "Unknown"
            
            print(f"{idx}. 📊 {month_name}")
            print(f"   Stocktake ID: {period['stocktake__id']}")
            print(f"   Date Range: {start} to {end}")
            print(f"   Sales Count: {count} items")
            print(f"   Total Revenue: €{revenue:,.2f}")
            print(f"   Total Cost: €{cost:,.2f}")
            print(f"   Gross Profit: €{profit:,.2f}")
            
            if revenue > 0:
                gp_percent = (profit / revenue) * 100
                print(f"   GP%: {gp_percent:.2f}%")
            print()
    
    # 2. Standalone sales (not linked to any stocktake)
    print("=" * 80)
    print("STANDALONE SALES (Not linked to stocktake)")
    print("=" * 80)
    
    standalone_sales = Sale.objects.filter(stocktake__isnull=True)
    standalone_count = standalone_sales.count()
    
    if standalone_count == 0:
        print("\n✅ No standalone sales\n")
    else:
        print(f"\n⚠️  Found {standalone_count} standalone sales\n")
        
        # Group by sale_date
        sales_by_date = standalone_sales.values('sale_date').annotate(
            count=Count('id'),
            total_revenue=Sum('total_revenue'),
            total_cost=Sum('total_cost')
        ).order_by('sale_date')
        
        for idx, date_group in enumerate(sales_by_date, 1):
            sale_date = date_group['sale_date']
            count = date_group['count']
            revenue = date_group['total_revenue'] or Decimal('0.00')
            cost = date_group['total_cost'] or Decimal('0.00')
            profit = revenue - cost
            
            print(f"{idx}. 📅 {sale_date}")
            print(f"   Sales Count: {count} items")
            print(f"   Total Revenue: €{revenue:,.2f}")
            print(f"   Total Cost: €{cost:,.2f}")
            print(f"   Gross Profit: €{profit:,.2f}")
            
            if revenue > 0:
                gp_percent = (profit / revenue) * 100
                print(f"   GP%: {gp_percent:.2f}%")
            print()

print("=" * 80)
print("💡 FRONTEND USAGE:")
print("=" * 80)
print("\n1. Fetch sales by stocktake period:")
print("   GET /api/stock-tracker/<hotel_identifier>/sales/?stocktake=<id>")

print("\n2. Fetch sales by date range:")
print("   GET /api/stock-tracker/<hotel_identifier>/sales/?start_date=2025-10-01"
      "&end_date=2025-10-31")

print("\n3. Fetch all sales (no filter):")
print("   GET /api/stock-tracker/<hotel_identifier>/sales/")

print("\n4. Get summary by category:")
print("   GET /api/stock-tracker/<hotel_identifier>/sales/summary/?stocktake=<id>")
print("=" * 80)