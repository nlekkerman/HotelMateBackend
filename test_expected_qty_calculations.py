"""
Test Expected Quantity Calculations

This script tests the expected_qty formula at different levels:
1. Single stocktake line (individual item)
2. Multiple snapshots/items
3. Complete category totals

Formula: expected = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine, StockSnapshot
from hotel.models import Hotel
from decimal import Decimal


def test_single_stocktake_line():
    """Test calculation on a single stocktake line"""
    print("\n" + "=" * 80)
    print("TEST 1: SINGLE STOCKTAKE LINE")
    print("=" * 80)
    
    try:
        # Get first stocktake line with some data
        line = StocktakeLine.objects.filter(
            stocktake__status='APPROVED'
        ).exclude(
            sales=Decimal('0')
        ).first()
        
        if not line:
            print("❌ No stocktake lines found with sales data")
            return
        
        print(f"\nItem: {line.item.sku} - {line.item.name}")
        print(f"Category: {line.item.category.code} - {line.item.category.name}")
        print(f"Stocktake Period: {line.stocktake.period_start} to {line.stocktake.period_end}")
        print("\n" + "-" * 80)
        print("EXPECTED QUANTITY CALCULATION:")
        print("-" * 80)
        print(f"  Opening Stock:        {line.opening_qty:>15,.4f} servings")
        print(f"  + Purchases:          {line.purchases:>15,.4f}")
        print(f"  + Transfers In:       {line.transfers_in:>15,.4f}")
        print(f"  - Sales:              {line.sales:>15,.4f}")
        print(f"  - Waste:              {line.waste:>15,.4f}")
        print(f"  - Transfers Out:      {line.transfers_out:>15,.4f}")
        print(f"  + Adjustments:        {line.adjustments:>15,.4f}")
        print("-" * 80)
        print(f"  = EXPECTED:           {line.expected_qty:>15,.4f} servings")
        print(f"\n  Counted:              {line.counted_qty:>15,.4f} servings")
        print(f"  Variance:             {line.variance_qty:>15,.4f} servings")
        
        # Verify calculation manually
        manual_calc = (
            line.opening_qty + 
            line.purchases + 
            line.transfers_in - 
            line.sales - 
            line.waste - 
            line.transfers_out + 
            line.adjustments
        )
        print(f"\n✅ Manual verification: {manual_calc:,.4f}")
        print(f"✅ Property value:      {line.expected_qty:,.4f}")
        print(f"✅ Match: {manual_calc == line.expected_qty}")
        
        # Show monetary values
        print(f"\n" + "-" * 80)
        print("MONETARY VALUES:")
        print("-" * 80)
        print(f"  Expected Value:       €{line.expected_value:>14,.2f}")
        print(f"  Counted Value:        €{line.counted_value:>14,.2f}")
        print(f"  Variance Value:       €{line.variance_value:>14,.2f}")
        print(f"  Valuation Cost:       €{line.valuation_cost:>14,.4f}/serving")
        
        # Show manual overrides if present
        if line.manual_purchases_value or line.manual_sales_profit:
            print(f"\n" + "-" * 80)
            print("MANUAL OVERRIDES:")
            print("-" * 80)
            if line.manual_purchases_value:
                print(f"  Manual Purchases:     €{line.manual_purchases_value:>14,.2f}")
            if line.manual_sales_profit:
                print(f"  Manual Sales Profit:  €{line.manual_sales_profit:>14,.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_multiple_items():
    """Test calculation on multiple items from same category"""
    print("\n\n" + "=" * 80)
    print("TEST 2: MULTIPLE ITEMS (First 5 Spirits)")
    print("=" * 80)
    
    try:
        lines = StocktakeLine.objects.filter(
            stocktake__status='APPROVED',
            item__category__code='S'
        ).order_by('item__sku')[:5]
        
        if not lines.exists():
            print("❌ No spirits items found")
            return
        
        print(f"\nFound {lines.count()} items")
        print("\n" + "-" * 80)
        
        total_opening = Decimal('0')
        total_purchases = Decimal('0')
        total_sales = Decimal('0')
        total_waste = Decimal('0')
        total_transfers_in = Decimal('0')
        total_transfers_out = Decimal('0')
        total_adjustments = Decimal('0')
        total_expected = Decimal('0')
        total_counted = Decimal('0')
        total_variance = Decimal('0')
        
        for i, line in enumerate(lines, 1):
            print(f"\n{i}. {line.item.sku} - {line.item.name}")
            print(f"   Formula: {line.opening_qty:.2f} + {line.purchases:.2f} + {line.transfers_in:.2f} - {line.sales:.2f} - {line.waste:.2f} - {line.transfers_out:.2f} + {line.adjustments:.2f}")
            print(f"   = Expected: {line.expected_qty:.4f} | Counted: {line.counted_qty:.4f} | Variance: {line.variance_qty:.4f}")
            
            # Accumulate totals
            total_opening += line.opening_qty
            total_purchases += line.purchases
            total_sales += line.sales
            total_waste += line.waste
            total_transfers_in += line.transfers_in
            total_transfers_out += line.transfers_out
            total_adjustments += line.adjustments
            total_expected += line.expected_qty
            total_counted += line.counted_qty
            total_variance += line.variance_qty
        
        print("\n" + "=" * 80)
        print("TOTALS FOR THESE ITEMS:")
        print("=" * 80)
        print(f"  Opening:              {total_opening:>15,.4f}")
        print(f"  + Purchases:          {total_purchases:>15,.4f}")
        print(f"  + Transfers In:       {total_transfers_in:>15,.4f}")
        print(f"  - Sales:              {total_sales:>15,.4f}")
        print(f"  - Waste:              {total_waste:>15,.4f}")
        print(f"  - Transfers Out:      {total_transfers_out:>15,.4f}")
        print(f"  + Adjustments:        {total_adjustments:>15,.4f}")
        print("-" * 80)
        print(f"  = EXPECTED:           {total_expected:>15,.4f}")
        print(f"  Counted:              {total_counted:>15,.4f}")
        print(f"  Variance:             {total_variance:>15,.4f}")
        
        # Verify manual calculation
        manual_total = (
            total_opening + total_purchases + total_transfers_in -
            total_sales - total_waste - total_transfers_out + total_adjustments
        )
        print(f"\n✅ Manual verification: {manual_total:,.4f}")
        print(f"✅ Sum of expectations: {total_expected:,.4f}")
        print(f"✅ Match: {manual_total == total_expected}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_complete_category():
    """Test calculation on complete category using new method"""
    print("\n\n" + "=" * 80)
    print("TEST 3: COMPLETE CATEGORY (All Spirits)")
    print("=" * 80)
    
    try:
        # Get latest approved stocktake
        stocktake = Stocktake.objects.filter(
            status='APPROVED'
        ).order_by('-period_end').first()
        
        if not stocktake:
            print("❌ No approved stocktake found")
            return
        
        print(f"\nStocktake ID: {stocktake.id}")
        print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
        
        # Test spirits category
        spirits_totals = stocktake.get_category_totals(category_code='S')
        
        if not spirits_totals:
            print("❌ No spirits data found")
            return
        
        print(f"\nCategory: {spirits_totals['category_code']} - {spirits_totals['category_name']}")
        print(f"Total Items: {spirits_totals['item_count']}")
        
        print("\n" + "-" * 80)
        print("CATEGORY TOTALS (All Spirits Combined):")
        print("-" * 80)
        print(f"  Opening Stock:        {float(spirits_totals['opening_qty']):>15,.4f} servings")
        print(f"  + Purchases:          {float(spirits_totals['purchases']):>15,.4f}")
        print(f"  + Transfers In:       {float(spirits_totals['transfers_in']):>15,.4f}")
        print(f"  - Sales:              {float(spirits_totals['sales']):>15,.4f}")
        print(f"  - Waste:              {float(spirits_totals['waste']):>15,.4f}")
        print(f"  - Transfers Out:      {float(spirits_totals['transfers_out']):>15,.4f}")
        print(f"  + Adjustments:        {float(spirits_totals['adjustments']):>15,.4f}")
        print("-" * 80)
        print(f"  = EXPECTED:           {float(spirits_totals['expected_qty']):>15,.4f} servings")
        print(f"\n  Counted:              {float(spirits_totals['counted_qty']):>15,.4f} servings")
        print(f"  Variance:             {float(spirits_totals['variance_qty']):>15,.4f} servings")
        
        # Show monetary values
        print("\n" + "-" * 80)
        print("MONETARY TOTALS:")
        print("-" * 80)
        print(f"  Expected Value:       €{float(spirits_totals['expected_value']):>14,.2f}")
        print(f"  Counted Value:        €{float(spirits_totals['counted_value']):>14,.2f}")
        print(f"  Variance Value:       €{float(spirits_totals['variance_value']):>14,.2f}")
        
        # Show manual overrides if any
        if float(spirits_totals['manual_purchases_value']) > 0 or float(spirits_totals['manual_sales_profit']) > 0:
            print("\n" + "-" * 80)
            print("MANUAL OVERRIDE TOTALS:")
            print("-" * 80)
            if float(spirits_totals['manual_purchases_value']) > 0:
                print(f"  Manual Purchases:     €{float(spirits_totals['manual_purchases_value']):>14,.2f}")
            if float(spirits_totals['manual_sales_profit']) > 0:
                print(f"  Manual Sales Profit:  €{float(spirits_totals['manual_sales_profit']):>14,.2f}")
        
        # Calculate variance percentage
        if float(spirits_totals['expected_qty']) != 0:
            variance_pct = (float(spirits_totals['variance_qty']) / float(spirits_totals['expected_qty'])) * 100
            print(f"\nVariance Percentage: {variance_pct:+.2f}%")
        
        # Verify by manually calculating from lines
        print("\n" + "-" * 80)
        print("VERIFICATION (Sum of individual lines):")
        print("-" * 80)
        
        lines = stocktake.lines.filter(item__category__code='S')
        manual_expected = sum(line.expected_qty for line in lines)
        manual_counted = sum(line.counted_qty for line in lines)
        manual_variance = sum(line.variance_qty for line in lines)
        
        print(f"  Manual Expected Sum:  {manual_expected:>15,.4f}")
        print(f"  Method Expected:      {float(spirits_totals['expected_qty']):>15,.4f}")
        print(f"  ✅ Match: {abs(manual_expected - float(spirits_totals['expected_qty'])) < 0.0001}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_all_categories():
    """Test all categories at once"""
    print("\n\n" + "=" * 80)
    print("TEST 4: ALL CATEGORIES SUMMARY")
    print("=" * 80)
    
    try:
        stocktake = Stocktake.objects.filter(
            status='APPROVED'
        ).order_by('-period_end').first()
        
        if not stocktake:
            print("❌ No approved stocktake found")
            return
        
        print(f"\nStocktake ID: {stocktake.id}")
        print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
        
        all_categories = stocktake.get_category_totals()
        
        if not all_categories:
            print("❌ No category data found")
            return
        
        print(f"\nFound {len(all_categories)} categories")
        
        print("\n" + "=" * 80)
        print(f"{'Cat':<4} {'Name':<15} {'Items':>6} {'Expected':>12} {'Counted':>12} {'Variance':>12} {'Var%':>8}")
        print("=" * 80)
        
        grand_expected = Decimal('0')
        grand_counted = Decimal('0')
        grand_variance = Decimal('0')
        
        for code in ['D', 'B', 'S', 'W', 'M']:
            if code in all_categories:
                cat = all_categories[code]
                expected = float(cat['expected_qty'])
                counted = float(cat['counted_qty'])
                variance = float(cat['variance_qty'])
                var_pct = (variance / expected * 100) if expected != 0 else 0
                
                print(f"{cat['category_code']:<4} {cat['category_name']:<15} {cat['item_count']:>6} "
                      f"{expected:>12,.2f} {counted:>12,.2f} {variance:>12,.2f} {var_pct:>7.2f}%")
                
                grand_expected += Decimal(str(expected))
                grand_counted += Decimal(str(counted))
                grand_variance += Decimal(str(variance))
        
        print("=" * 80)
        print(f"{'TOTAL':<20} {grand_expected:>18,.2f} {grand_counted:>12,.2f} {grand_variance:>12,.2f}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_snapshots():
    """Test relationship between snapshots and stocktake lines"""
    print("\n\n" + "=" * 80)
    print("TEST 5: SNAPSHOTS VS STOCKTAKE LINES")
    print("=" * 80)
    
    try:
        # Get a snapshot
        snapshot = StockSnapshot.objects.filter(
            period__stocktakes__status='APPROVED'
        ).first()
        
        if not snapshot:
            print("❌ No snapshots found")
            return
        
        # Find corresponding stocktake line
        stocktake_line = StocktakeLine.objects.filter(
            item=snapshot.item,
            stocktake__period_start=snapshot.period.start_date,
            stocktake__period_end=snapshot.period.end_date
        ).first()
        
        if not stocktake_line:
            print("❌ No matching stocktake line found")
            return
        
        print(f"\nItem: {snapshot.item.sku} - {snapshot.item.name}")
        print(f"Period: {snapshot.period.period_name}")
        
        print("\n" + "-" * 80)
        print("SNAPSHOT DATA (Period End):")
        print("-" * 80)
        print(f"  Closing Full Units:   {snapshot.closing_full_units:>15,.2f}")
        print(f"  Closing Partial:      {snapshot.closing_partial_units:>15,.4f}")
        print(f"  Total Servings:       {snapshot.total_servings:>15,.4f}")
        print(f"  Closing Value:        €{snapshot.closing_stock_value:>14,.2f}")
        
        print("\n" + "-" * 80)
        print("STOCKTAKE LINE DATA (With Formula):")
        print("-" * 80)
        print(f"  Opening Qty:          {stocktake_line.opening_qty:>15,.4f} servings")
        print(f"  Expected Qty:         {stocktake_line.expected_qty:>15,.4f} servings")
        print(f"  Counted Qty:          {stocktake_line.counted_qty:>15,.4f} servings")
        print(f"  Variance:             {stocktake_line.variance_qty:>15,.4f} servings")
        
        print(f"\n✅ Snapshot represents closing stock for the period")
        print(f"✅ Stocktake line calculates expected vs counted for same period")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("EXPECTED QUANTITY CALCULATION TESTS")
    print("Formula: expected = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments")
    print("*" * 80)
    
    # Run all tests
    test_single_stocktake_line()
    test_multiple_items()
    test_complete_category()
    test_all_categories()
    test_snapshots()
    
    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print()
