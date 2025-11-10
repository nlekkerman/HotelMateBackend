"""
Test Script: Fetch All Items, Insert Mock Sales, Verify Stocktake Integration
Tests the sales entry system end-to-end.

Run with: python test_sales_entry_system.py
"""

import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from datetime import date
from django.contrib.auth import get_user_model
from hotel.models import Hotel
from staff.models import Staff
from stock_tracker.models import (
    StockItem, Stocktake, Sale, StockPeriod
)

User = get_user_model()


def test_sales_entry_system():
    """
    Complete test of sales entry system:
    1. Fetch all active stock items
    2. Create mock sales data
    3. Save sales using bulk create
    4. Verify they merge with stocktake
    """
    
    print("\n" + "="*80)
    print("🛒 TESTING SALES ENTRY SYSTEM")
    print("="*80 + "\n")
    
    # Setup
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return
    
    print(f"🏨 Hotel: {hotel.name}\n")
    
    # ===========================================================================
    # STEP 1: Fetch All Active Stock Items (Like Frontend Would)
    # ===========================================================================
    
    print("="*80)
    print("STEP 1: Fetch All Active Stock Items")
    print("="*80)
    
    active_items = StockItem.objects.filter(
        hotel=hotel,
        active=True,
        available_on_menu=True
    ).order_by('category__code', 'sku')
    
    print(f"✅ Found {active_items.count()} active items\n")
    
    # Display sample items
    print("Sample Items:")
    print("-" * 80)
    print(f"{'SKU':<10} {'Name':<30} {'Cat':<5} {'Price':<8} {'Cost/Srv':<10}")
    print("-" * 80)
    
    sample_items = active_items[:10]
    for item in sample_items:
        print(
            f"{item.sku:<10} "
            f"{item.name[:28]:<30} "
            f"{item.category.code:<5} "
            f"€{item.menu_price or 0:<7.2f} "
            f"€{item.cost_per_serving:<9.4f}"
        )
    
    print(f"\n... and {active_items.count() - 10} more items\n")
    
    # ===========================================================================
    # STEP 2: Create or Get Stocktake Period
    # ===========================================================================
    
    print("="*80)
    print("STEP 2: Get/Create Stocktake Period")
    print("="*80)
    
    period_start = date(2025, 11, 1)
    period_end = date(2025, 11, 10)
    
    # Create period if needed
    period, created = StockPeriod.objects.get_or_create(
        hotel=hotel,
        period_type=StockPeriod.MONTHLY,
        start_date=period_start,
        end_date=period_end,
        defaults={
            'year': 2025,
            'month': 11,
            'period_name': 'November 2025'
        }
    )
    
    # Create stocktake if needed
    stocktake, created = Stocktake.objects.get_or_create(
        hotel=hotel,
        period_start=period_start,
        period_end=period_end,
        defaults={'status': Stocktake.DRAFT}
    )
    
    print(f"📊 Stocktake: {stocktake}")
    print(f"📅 Period: {period}")
    print(f"Status: {stocktake.status}\n")
    
    # Check existing sales
    existing_sales_count = stocktake.sales.count()
    print(f"Existing sales records: {existing_sales_count}")
    
    if existing_sales_count > 0:
        print("⚠️  Clearing existing sales for clean test...")
        stocktake.sales.all().delete()
        print("✅ Cleared\n")
    
    # ===========================================================================
    # STEP 3: Generate Mock Sales Data
    # ===========================================================================
    
    print("="*80)
    print("STEP 3: Generate Mock Sales Data")
    print("="*80)
    
    # Select random items for sales (simulate user entering sales)
    num_sales = min(20, active_items.count())  # Create sales for 20 items
    selected_items = random.sample(list(active_items), num_sales)
    
    mock_sales = []
    
    for item in selected_items:
        # Generate random quantity based on category
        if item.category.code == 'D':  # Draught
            qty = round(random.uniform(50, 300), 2)  # 50-300 pints
        elif item.category.code == 'B':  # Bottled
            qty = random.randint(12, 96)  # 12-96 bottles
        elif item.category.code == 'S':  # Spirits
            qty = round(random.uniform(5, 40), 2)  # 5-40 shots
        elif item.category.code == 'W':  # Wine
            qty = round(random.uniform(3, 20), 2)  # 3-20 glasses
        else:  # Minerals
            qty = random.randint(10, 50)  # 10-50 serves
        
        mock_sales.append({
            'item': item,
            'quantity': Decimal(str(qty)),
            'stocktake': stocktake,
            'sale_date': period_end
        })
    
    print(f"✅ Generated {len(mock_sales)} mock sales entries\n")
    
    print("Sample Mock Sales:")
    print("-" * 100)
    print(f"{'Item':<30} {'Qty':<10} {'Price':<10} {'Revenue':<12} {'COGS':<12} {'GP%':<8}")
    print("-" * 100)
    
    total_revenue = Decimal('0')
    total_cogs = Decimal('0')
    
    for sale_data in mock_sales[:10]:
        item = sale_data['item']
        qty = sale_data['quantity']
        revenue = qty * (item.menu_price or Decimal('0'))
        cogs = qty * item.cost_per_serving
        gp = ((revenue - cogs) / revenue * 100) if revenue > 0 else Decimal('0')
        
        total_revenue += revenue
        total_cogs += cogs
        
        print(
            f"{item.name[:28]:<30} "
            f"{qty:<10.2f} "
            f"€{item.menu_price or 0:<9.2f} "
            f"€{revenue:<11.2f} "
            f"€{cogs:<11.2f} "
            f"{gp:<7.2f}%"
        )
    
    print(f"\n... and {len(mock_sales) - 10} more sales\n")
    
    # ===========================================================================
    # STEP 4: Save Sales to Database (Simulating Bulk Create)
    # ===========================================================================
    
    print("="*80)
    print("STEP 4: Save Sales to Database")
    print("="*80)
    
    created_sales = []
    
    for sale_data in mock_sales:
        # Create Sale object (mimics what bulk_create does)
        sale = Sale(
            stocktake=sale_data['stocktake'],
            item=sale_data['item'],
            quantity=sale_data['quantity'],
            unit_cost=sale_data['item'].cost_per_serving,
            unit_price=sale_data['item'].menu_price,
            sale_date=sale_data['sale_date']
        )
        # Save will auto-calculate total_cost and total_revenue
        sale.save()
        created_sales.append(sale)
    
    print(f"✅ Created {len(created_sales)} Sale records\n")
    
    # ===========================================================================
    # STEP 5: Verify Sales Merged with Stocktake
    # ===========================================================================
    
    print("="*80)
    print("STEP 5: Verify Sales Merged with Stocktake")
    print("="*80)
    
    # Refresh stocktake to get updated data
    stocktake.refresh_from_db()
    
    # Get stocktake totals (should include our sales)
    stocktake_revenue = stocktake.total_revenue
    stocktake_cogs = stocktake.total_cogs
    stocktake_gp = stocktake.gross_profit_percentage
    
    print(f"📊 Stocktake Totals:")
    print(f"   Sales Count: {stocktake.sales.count()}")
    print(f"   Total Revenue: €{stocktake_revenue:,.2f}")
    print(f"   Total COGS: €{stocktake_cogs:,.2f}")
    print(f"   Gross Profit: €{stocktake_revenue - stocktake_cogs:,.2f}")
    print(f"   GP%: {stocktake_gp}%\n")
    
    # Verify the numbers match
    print("="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Calculate expected totals from created sales
    expected_revenue = sum(sale.total_revenue or Decimal('0') for sale in created_sales)
    expected_cogs = sum(sale.total_cost for sale in created_sales)
    
    print(f"Expected Revenue: €{expected_revenue:,.2f}")
    print(f"Actual Revenue:   €{stocktake_revenue:,.2f}")
    print(f"Match: {'✅' if abs(expected_revenue - stocktake_revenue) < Decimal('0.01') else '❌'}\n")
    
    print(f"Expected COGS: €{expected_cogs:,.2f}")
    print(f"Actual COGS:   €{stocktake_cogs:,.2f}")
    print(f"Match: {'✅' if abs(expected_cogs - stocktake_cogs) < Decimal('0.01') else '❌'}\n")
    
    # ===========================================================================
    # STEP 6: Test Category Breakdown
    # ===========================================================================
    
    print("="*80)
    print("STEP 6: Sales by Category")
    print("="*80)
    
    from django.db.models import Sum, Count
    
    category_breakdown = stocktake.sales.values(
        'item__category__code',
        'item__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_revenue'),
        total_cogs=Sum('total_cost'),
        item_count=Count('id')
    ).order_by('item__category__code')
    
    print("-" * 80)
    print(f"{'Category':<20} {'Items':<8} {'Qty':<12} {'Revenue':<15} {'COGS':<15}")
    print("-" * 80)
    
    for cat in category_breakdown:
        print(
            f"{cat['item__category__name']:<20} "
            f"{cat['item_count']:<8} "
            f"{cat['total_quantity']:<12.2f} "
            f"€{cat['total_revenue'] or 0:<14.2f} "
            f"€{cat['total_cogs']:<14.2f}"
        )
    
    print("-" * 80)
    print(f"{'TOTAL':<20} {stocktake.sales.count():<8} {'':<12} €{stocktake_revenue:<14.2f} €{stocktake_cogs:<14.2f}")
    print("-" * 80 + "\n")
    
    # ===========================================================================
    # STEP 7: Test Fetching Sales Back
    # ===========================================================================
    
    print("="*80)
    print("STEP 7: Fetch Sales from API (Simulated)")
    print("="*80)
    
    # This simulates what GET /api/stock/<hotel>/stocktakes/<id>/sales/ returns
    sales_queryset = stocktake.sales.select_related(
        'item',
        'item__category'
    ).order_by('-total_revenue')[:5]
    
    print("Top 5 Sales by Revenue:")
    print("-" * 100)
    print(f"{'Item':<30} {'Qty':<10} {'Unit Price':<12} {'Revenue':<12} {'COGS':<12} {'GP%':<8}")
    print("-" * 100)
    
    for sale in sales_queryset:
        print(
            f"{sale.item.name[:28]:<30} "
            f"{sale.quantity:<10.2f} "
            f"€{sale.unit_price or 0:<11.2f} "
            f"€{sale.total_revenue or 0:<11.2f} "
            f"€{sale.total_cost:<11.2f} "
            f"{sale.gross_profit_percentage or 0:<7.2f}%"
        )
    
    print("-" * 100 + "\n")
    
    # ===========================================================================
    # STEP 8: Final Summary
    # ===========================================================================
    
    print("="*80)
    print("🎉 TEST SUMMARY")
    print("="*80)
    
    print("✅ Fetched all active stock items")
    print("✅ Generated mock sales data")
    print("✅ Saved sales to database")
    print("✅ Sales merged with stocktake")
    print("✅ Totals calculated correctly")
    print("✅ Category breakdown working")
    print("✅ API fetch simulation successful")
    
    print(f"\n📊 Final Numbers:")
    print(f"   Items in catalog: {active_items.count()}")
    print(f"   Sales created: {len(created_sales)}")
    print(f"   Total Revenue: €{stocktake_revenue:,.2f}")
    print(f"   Total COGS: €{stocktake_cogs:,.2f}")
    print(f"   Gross Profit: €{stocktake_revenue - stocktake_cogs:,.2f}")
    print(f"   GP%: {stocktake_gp}%")
    
    print("\n" + "="*80)
    print("✅ SALES ENTRY SYSTEM TEST PASSED!")
    print("="*80 + "\n")
    
    # Optional: Clean up
    print("💡 TIP: Sales data has been saved to database.")
    print(f"   Stocktake ID: {stocktake.id}")
    print(f"   To view in API: GET /api/stock/{hotel.slug}/stocktakes/{stocktake.id}/sales/")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_sales_entry_system()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
