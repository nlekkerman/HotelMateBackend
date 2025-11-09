"""
Test script to add sales data to October stocktake and calculate GP%
- Purchases cost: €19,000
- Sales revenue: €62,000
- Calculate GP%
"""

import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, Sale, StockItem
from django.db.models import Sum, F

def main():
    print("=" * 80)
    print("TESTING SALES MODEL & GP% CALCULATION")
    print("=" * 80)
    
    # Find October 2025 stocktake
    print("\n1. Finding October 2025 stocktake...")
    october_stocktake = Stocktake.objects.filter(
        period_start__year=2025,
        period_start__month=10
    ).first()
    
    if not october_stocktake:
        print("❌ No October 2025 stocktake found!")
        return
    
    print(f"✅ Found stocktake ID: {october_stocktake.id}")
    print(f"   Period: {october_stocktake.period_start} to {october_stocktake.period_end}")
    print(f"   Status: {october_stocktake.status}")
    
    # Get stocktake lines
    lines = StocktakeLine.objects.filter(stocktake=october_stocktake)
    print(f"   Total items: {lines.count()}")
    
    # Calculate purchases total
    print("\n2. Calculating purchases...")
    purchases_summary = lines.aggregate(
        total_purchases_qty=Sum('purchases'),
        total_purchases_value=Sum(F('purchases') * F('valuation_cost'))
    )
    
    print(f"   Total purchases quantity: {purchases_summary['total_purchases_qty']}")
    print(f"   Total purchases value: €{purchases_summary['total_purchases_value']:.2f}")
    
    # Check existing sales
    print("\n3. Checking existing sales...")
    existing_sales = Sale.objects.filter(stocktake=october_stocktake)
    print(f"   Existing sales records: {existing_sales.count()}")
    
    if existing_sales.exists():
        sales_summary = existing_sales.aggregate(
            total_cost=Sum('total_cost'),
            total_revenue=Sum('total_revenue')
        )
        print(f"   Total cost: €{sales_summary['total_cost']:.2f}")
        print(f"   Total revenue: €{sales_summary['total_revenue']:.2f}")
    
    # Create test sales data
    print("\n4. Creating test sales data...")
    print("   Target: €19,000 purchase cost → €62,000 revenue")
    
    # Clear any existing test sales first
    response = input("\n   Delete existing sales and create new test data? (y/n): ")
    if response.lower() != 'y':
        print("   Skipped. Using existing data.")
    else:
        print("   Deleting existing sales...")
        deleted_count = existing_sales.delete()[0]
        print(f"   ✅ Deleted {deleted_count} sales records")
        
        # Get a sample of items to create sales for
        sample_lines = list(lines[:20])  # Take first 20 items
        
        if not sample_lines:
            print("   ❌ No stocktake lines to create sales from!")
            return
        
        # Target values
        target_purchase_cost = Decimal('19000.00')
        target_revenue = Decimal('62000.00')
        
        # Calculate per-item targets
        items_count = len(sample_lines)
        
        sales_created = []
        total_cost = Decimal('0.00')
        total_revenue = Decimal('0.00')
        
        print(f"   Creating sales for {items_count} items...")
        
        for idx, line in enumerate(sample_lines):
            # Distribute the target values across items
            item_purchase_share = target_purchase_cost / items_count
            item_revenue_share = target_revenue / items_count
            
            # Calculate quantity based on cost
            if line.valuation_cost > 0:
                quantity = item_purchase_share / line.valuation_cost
            else:
                quantity = Decimal('10.0000')  # Default quantity
            
            # Calculate unit price from revenue target
            if quantity > 0:
                unit_price = item_revenue_share / quantity
            else:
                unit_price = line.item.menu_price or Decimal('10.00')
            
            # Create sale
            sale = Sale.objects.create(
                stocktake=october_stocktake,
                item=line.item,
                quantity=quantity,
                unit_cost=line.valuation_cost,
                unit_price=unit_price,
                sale_date=october_stocktake.period_end,
                notes=f"Test sale {idx + 1}/{items_count}"
            )
            
            sales_created.append(sale)
            total_cost += sale.total_cost
            total_revenue += sale.total_revenue
        
        print(f"   ✅ Created {len(sales_created)} sales records")
        print(f"   Total cost: €{total_cost:.2f}")
        print(f"   Total revenue: €{total_revenue:.2f}")
    
    # Calculate final GP%
    print("\n5. Calculating Gross Profit %...")
    all_sales = Sale.objects.filter(stocktake=october_stocktake)
    
    final_summary = all_sales.aggregate(
        total_cost=Sum('total_cost'),
        total_revenue=Sum('total_revenue'),
        total_quantity=Sum('quantity'),
        sale_count=Sum('id')
    )
    
    cost = final_summary['total_cost'] or Decimal('0.00')
    revenue = final_summary['total_revenue'] or Decimal('0.00')
    
    if revenue > 0:
        gross_profit = revenue - cost
        gp_percentage = (gross_profit / revenue) * 100
        
        print(f"\n   📊 FINAL RESULTS:")
        print(f"   " + "=" * 60)
        print(f"   Total Sales Count: {final_summary['sale_count']}")
        print(f"   Total Quantity Sold: {final_summary['total_quantity']:.2f} servings")
        print(f"   ")
        print(f"   Cost of Goods Sold: €{cost:,.2f}")
        print(f"   Total Revenue:      €{revenue:,.2f}")
        print(f"   Gross Profit:       €{gross_profit:,.2f}")
        print(f"   ")
        print(f"   🎯 Gross Profit %:  {gp_percentage:.2f}%")
        print(f"   " + "=" * 60)
        
        # Industry benchmarks
        print(f"\n   📈 Industry Benchmarks:")
        print(f"      Target GP% for bars: 70-85%")
        if gp_percentage >= 70:
            print(f"      ✅ GOOD - Your GP% is within target range!")
        elif gp_percentage >= 60:
            print(f"      ⚠️  FAIR - GP% is slightly below target")
        else:
            print(f"      ❌ LOW - GP% is below industry standards")
    else:
        print("   ❌ No revenue data to calculate GP%")
    
    # Show sales by category
    print("\n6. Sales by Category:")
    from django.db.models import Count
    
    category_sales = all_sales.values(
        'item__category__code',
        'item__category__name'
    ).annotate(
        total_cost=Sum('total_cost'),
        total_revenue=Sum('total_revenue'),
        sale_count=Count('id')
    ).order_by('item__category__code')
    
    for cat in category_sales:
        cat_cost = cat['total_cost'] or Decimal('0.00')
        cat_revenue = cat['total_revenue'] or Decimal('0.00')
        if cat_revenue > 0:
            cat_gp = ((cat_revenue - cat_cost) / cat_revenue) * 100
        else:
            cat_gp = 0
        
        print(f"   {cat['item__category__code']} - {cat['item__category__name']}:")
        print(f"      Sales: {cat['sale_count']}, Cost: €{cat_cost:,.2f}, "
              f"Revenue: €{cat_revenue:,.2f}, GP%: {cat_gp:.2f}%")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
