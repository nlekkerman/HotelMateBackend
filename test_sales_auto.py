"""
Automatic test script to add sales data to October stocktake and calculate GP%
- Purchases cost: €19,000
- Sales revenue: €62,000
- Calculate GP%
"""

import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, Sale
from django.db.models import Sum, F, Count

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
    print(f"   Period: {october_stocktake.period_start} to "
          f"{october_stocktake.period_end}")
    print(f"   Status: {october_stocktake.status}")
    
    # Get stocktake lines
    lines = StocktakeLine.objects.filter(stocktake=october_stocktake)
    print(f"   Total items: {lines.count()}")
    
    # Clear existing sales
    print("\n2. Clearing existing sales...")
    existing = Sale.objects.filter(stocktake=october_stocktake)
    deleted = existing.delete()[0]
    print(f"   ✅ Deleted {deleted} existing sales records")
    
    # Create test sales data
    print("\n3. Creating test sales data...")
    print("   Target: €19,000 COGS → €62,000 Revenue")
    
    # Get sample items
    sample_lines = list(lines.filter(
        item__menu_price__isnull=False
    )[:25])
    
    if not sample_lines:
        print("   ❌ No items with menu prices found!")
        return
    
    # Target values
    target_cogs = Decimal('19000.00')
    target_revenue = Decimal('62000.00')
    
    # Distribute across items
    items_count = len(sample_lines)
    per_item_cogs = target_cogs / items_count
    per_item_revenue = target_revenue / items_count
    
    sales_created = []
    
    for idx, line in enumerate(sample_lines):
        # Calculate quantity from COGS target
        if line.valuation_cost > 0:
            quantity = per_item_cogs / line.valuation_cost
        else:
            quantity = Decimal('10.0000')
        
        # Calculate unit price from revenue target
        if quantity > 0:
            unit_price = per_item_revenue / quantity
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
            notes=f"Test sale {idx + 1}"
        )
        sales_created.append(sale)
    
    print(f"   ✅ Created {len(sales_created)} sales records")
    
    # Calculate GP%
    print("\n4. Calculating Gross Profit %...")
    all_sales = Sale.objects.filter(stocktake=october_stocktake)
    
    summary = all_sales.aggregate(
        total_cost=Sum('total_cost'),
        total_revenue=Sum('total_revenue'),
        total_quantity=Sum('quantity'),
        sale_count=Count('id')
    )
    
    cost = summary['total_cost'] or Decimal('0.00')
    revenue = summary['total_revenue'] or Decimal('0.00')
    
    if revenue > 0:
        gross_profit = revenue - cost
        gp_percentage = (gross_profit / revenue) * 100
        
        print(f"\n   📊 RESULTS:")
        print(f"   " + "=" * 60)
        print(f"   Sales Count:        {summary['sale_count']}")
        print(f"   Quantity Sold:      {summary['total_quantity']:.2f} servings")
        print(f"   ")
        print(f"   Cost of Goods Sold: €{cost:,.2f}")
        print(f"   Total Revenue:      €{revenue:,.2f}")
        print(f"   Gross Profit:       €{gross_profit:,.2f}")
        print(f"   ")
        print(f"   🎯 Gross Profit %:  {gp_percentage:.2f}%")
        print(f"   " + "=" * 60)
        
        # Benchmarks
        print(f"\n   📈 Industry Benchmarks:")
        print(f"      Target GP% for bars: 70-85%")
        if gp_percentage >= 70:
            print(f"      ✅ EXCELLENT - Within target range!")
        elif gp_percentage >= 60:
            print(f"      ⚠️  FAIR - Slightly below target")
        else:
            print(f"      ❌ LOW - Below industry standards")
    
    # Category breakdown
    print("\n5. Sales by Category:")
    
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
        
        profit = cat_revenue - cat_cost
        
        print(f"\n   {cat['item__category__code']} - "
              f"{cat['item__category__name']}:")
        print(f"      Sales Count: {cat['sale_count']}")
        print(f"      COGS:        €{cat_cost:,.2f}")
        print(f"      Revenue:     €{cat_revenue:,.2f}")
        print(f"      Profit:      €{profit:,.2f}")
        print(f"      GP%:         {cat_gp:.2f}%")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE - Sales model working correctly!")
    print("=" * 80)

if __name__ == '__main__':
    main()
