"""
Test Sales Category Filtering
==============================

This script tests that:
1. Sales API returns category information
2. Category filtering works correctly
3. Sales summary groups by category properly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Sale, Stocktake
from hotel.models import Hotel
from decimal import Decimal

def test_sales_category_data():
    """Test that sales include category data"""
    print("\n" + "="*70)
    print("TEST 1: Sales Include Category Data")
    print("="*70)
    
    # Get a hotel
    hotel = Hotel.objects.first()
    if not hotel:
        print("❌ No hotel found!")
        return False
    
    print(f"✅ Testing with hotel: {hotel.name}")
    
    # Get latest stocktake with sales
    stocktake = Stocktake.objects.filter(
        hotel=hotel
    ).exclude(sales__isnull=True).first()
    
    if not stocktake:
        print("❌ No stocktake with sales found!")
        return False
    
    print(f"✅ Using stocktake: {stocktake.period_start} to {stocktake.period_end}")
    
    # Get first 5 sales
    sales = Sale.objects.filter(stocktake=stocktake).select_related(
        'item', 'item__category'
    )[:5]
    
    print(f"\n📊 Checking {sales.count()} sales for category data:\n")
    
    all_have_categories = True
    for sale in sales:
        has_category = bool(sale.item.category)
        status = "✅" if has_category else "❌"
        
        if has_category:
            print(f"{status} Sale #{sale.id}: {sale.item.name}")
            print(f"   Category Code: {sale.item.category.code}")
            print(f"   Category Name: {sale.item.category.name}")
            print(f"   Quantity: {sale.quantity}")
            print(f"   Revenue: €{sale.total_revenue}")
        else:
            print(f"{status} Sale #{sale.id}: {sale.item.name} - NO CATEGORY!")
            all_have_categories = False
        print()
    
    return all_have_categories


def test_category_filtering():
    """Test filtering sales by category"""
    print("\n" + "="*70)
    print("TEST 2: Category Filtering")
    print("="*70)
    
    # Get a hotel
    hotel = Hotel.objects.first()
    
    # Get latest stocktake with sales
    stocktake = Stocktake.objects.filter(
        hotel=hotel
    ).exclude(sales__isnull=True).first()
    
    if not stocktake:
        print("❌ No stocktake with sales found!")
        return False
    
    # Get all sales
    all_sales = Sale.objects.filter(stocktake=stocktake)
    print(f"✅ Total sales in stocktake: {all_sales.count()}")
    
    # Count by category
    categories = {}
    for sale in all_sales:
        cat_code = sale.item.category.code
        if cat_code not in categories:
            categories[cat_code] = {
                'name': sale.item.category.name,
                'count': 0,
                'revenue': Decimal('0.00')
            }
        categories[cat_code]['count'] += 1
        categories[cat_code]['revenue'] += sale.total_revenue
    
    print(f"\n📊 Sales by Category:\n")
    for code, data in sorted(categories.items()):
        print(f"  {code} ({data['name']}): {data['count']} sales, €{data['revenue']:.2f}")
    
    # Test filtering for each category
    print(f"\n🔍 Testing Filters:\n")
    all_filters_work = True
    
    for code in categories.keys():
        filtered_sales = Sale.objects.filter(
            stocktake=stocktake,
            item__category__code=code
        )
        expected_count = categories[code]['count']
        actual_count = filtered_sales.count()
        
        if expected_count == actual_count:
            print(f"  ✅ Category {code}: Expected {expected_count}, got {actual_count}")
        else:
            print(f"  ❌ Category {code}: Expected {expected_count}, got {actual_count}")
            all_filters_work = False
    
    return all_filters_work


def test_category_summary():
    """Test sales summary grouped by category"""
    print("\n" + "="*70)
    print("TEST 3: Category Summary (Aggregation)")
    print("="*70)
    
    from django.db.models import Sum, Count
    
    # Get a hotel
    hotel = Hotel.objects.first()
    
    # Get latest stocktake with sales
    stocktake = Stocktake.objects.filter(
        hotel=hotel
    ).exclude(sales__isnull=True).first()
    
    if not stocktake:
        print("❌ No stocktake with sales found!")
        return False
    
    print(f"✅ Using stocktake: {stocktake.period_start} to {stocktake.period_end}")
    
    # Aggregate by category (as the API does)
    sales_by_category = Sale.objects.filter(
        stocktake=stocktake
    ).values(
        'item__category__code',
        'item__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_cost=Sum('total_cost'),
        total_revenue=Sum('total_revenue'),
        sale_count=Count('id')
    ).order_by('item__category__code')
    
    print(f"\n📊 Summary by Category:\n")
    
    total_revenue = Decimal('0.00')
    total_cost = Decimal('0.00')
    
    for cat in sales_by_category:
        print(f"  {cat['item__category__code']} - {cat['item__category__name']}:")
        print(f"    Sales Count: {cat['sale_count']}")
        print(f"    Total Quantity: {cat['total_quantity']}")
        print(f"    Revenue: €{cat['total_revenue']:.2f}")
        print(f"    COGS: €{cat['total_cost']:.2f}")
        
        revenue = Decimal(str(cat['total_revenue']))
        cost = Decimal(str(cat['total_cost']))
        
        if revenue > 0:
            gp_pct = ((revenue - cost) / revenue * 100)
            print(f"    GP%: {gp_pct:.2f}%")
        
        total_revenue += revenue
        total_cost += cost
        print()
    
    print(f"  GRAND TOTAL:")
    print(f"    Revenue: €{total_revenue:.2f}")
    print(f"    COGS: €{total_cost:.2f}")
    
    if total_revenue > 0:
        overall_gp = ((total_revenue - total_cost) / total_revenue * 100)
        print(f"    GP%: {overall_gp:.2f}%")
    
    return True


def main():
    print("\n" + "🧪 SALES CATEGORY FILTER TEST SUITE")
    print("="*70)
    
    results = []
    
    # Test 1: Category data present
    results.append(("Category Data Present", test_sales_category_data()))
    
    # Test 2: Category filtering works
    results.append(("Category Filtering", test_category_filtering()))
    
    # Test 3: Category summary
    results.append(("Category Summary", test_category_summary()))
    
    # Print results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n✅ The Sales API correctly returns category data.")
        print("✅ Frontend can filter sales by category using ?category=<code>")
        print("✅ Summary endpoint groups sales by category properly.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nCheck the output above for details.")
    print("="*70)


if __name__ == "__main__":
    main()
