"""
Test Expected Quantity Calculations with Sales, Waste, and All Movements

Demonstrates the complete formula with real data:
expected = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine
from decimal import Decimal


def find_stocktake_with_data():
    """Find a stocktake with sales and movement data"""
    print("Searching for stocktakes with sales/waste data...")
    
    # Check all stocktakes
    stocktakes = Stocktake.objects.all().order_by('-period_end')
    
    for st in stocktakes:
        lines_with_sales = st.lines.exclude(sales=Decimal('0')).count()
        lines_with_waste = st.lines.exclude(waste=Decimal('0')).count()
        lines_with_purchases = st.lines.exclude(
            purchases=Decimal('0')
        ).count()
        
        print(f"\nStocktake {st.id} ({st.period_start} to {st.period_end}):")
        print(f"  Status: {st.status}")
        print(f"  Total lines: {st.lines.count()}")
        print(f"  Lines with sales: {lines_with_sales}")
        print(f"  Lines with waste: {lines_with_waste}")
        print(f"  Lines with purchases: {lines_with_purchases}")
        
        if lines_with_sales > 0 or lines_with_waste > 0:
            return st
    
    return stocktakes.first() if stocktakes.exists() else None


def test_single_item_with_movements():
    """Test a single item with sales, waste, and movements"""
    print("\n" + "=" * 80)
    print("TEST 1: SINGLE ITEM WITH MOVEMENTS")
    print("=" * 80)
    
    stocktake = find_stocktake_with_data()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    # Find line with the most movements
    best_line = None
    max_movements = 0
    
    for line in stocktake.lines.all():
        movement_count = sum([
            1 if line.sales != 0 else 0,
            1 if line.waste != 0 else 0,
            1 if line.purchases != 0 else 0,
            1 if line.transfers_in != 0 else 0,
            1 if line.transfers_out != 0 else 0,
            1 if line.adjustments != 0 else 0,
        ])
        if movement_count > max_movements:
            max_movements = movement_count
            best_line = line
    
    if not best_line:
        # Just use first line
        best_line = stocktake.lines.first()
    
    line = best_line
    print(f"\nItem: {line.item.sku} - {line.item.name}")
    print(f"Category: {line.item.category.code} - {line.item.category.name}")
    print(f"Period: {line.stocktake.period_start} to "
          f"{line.stocktake.period_end}")
    
    print("\n" + "-" * 80)
    print("EXPECTED QUANTITY CALCULATION (Complete Formula):")
    print("-" * 80)
    print(f"  Opening Stock:        {line.opening_qty:>15,.4f} servings")
    
    if line.purchases != 0:
        print(f"  + Purchases:          {line.purchases:>15,.4f} ✓")
    else:
        print(f"  + Purchases:          {line.purchases:>15,.4f}")
    
    if line.transfers_in != 0:
        print(f"  + Transfers In:       {line.transfers_in:>15,.4f} ✓")
    else:
        print(f"  + Transfers In:       {line.transfers_in:>15,.4f}")
    
    if line.sales != 0:
        print(f"  - Sales:              {line.sales:>15,.4f} ✓")
    else:
        print(f"  - Sales:              {line.sales:>15,.4f}")
    
    if line.waste != 0:
        print(f"  - Waste:              {line.waste:>15,.4f} ✓")
    else:
        print(f"  - Waste:              {line.waste:>15,.4f}")
    
    if line.transfers_out != 0:
        print(f"  - Transfers Out:      {line.transfers_out:>15,.4f} ✓")
    else:
        print(f"  - Transfers Out:      {line.transfers_out:>15,.4f}")
    
    if line.adjustments != 0:
        print(f"  + Adjustments:        {line.adjustments:>15,.4f} ✓")
    else:
        print(f"  + Adjustments:        {line.adjustments:>15,.4f}")
    
    print("-" * 80)
    print(f"  = EXPECTED:           {line.expected_qty:>15,.4f} servings")
    print(f"\n  Counted:              {line.counted_qty:>15,.4f} servings")
    print(f"  Variance:             {line.variance_qty:>15,.4f} servings")
    
    # Manual verification
    manual = (
        line.opening_qty +
        line.purchases +
        line.transfers_in -
        line.sales -
        line.waste -
        line.transfers_out +
        line.adjustments
    )
    print(f"\n✅ Formula verification: {manual:,.4f}")
    print(f"✅ Property value:       {line.expected_qty:,.4f}")
    print(f"✅ Match: {abs(manual - line.expected_qty) < 0.0001}")
    
    # Show monetary values
    print("\n" + "-" * 80)
    print("MONETARY VALUES:")
    print("-" * 80)
    print(f"  Expected Value:       €{line.expected_value:>14,.2f}")
    print(f"  Counted Value:        €{line.counted_value:>14,.2f}")
    print(f"  Variance Value:       €{line.variance_value:>14,.2f}")


def test_items_with_waste_and_sales():
    """Test multiple items focusing on waste and sales"""
    print("\n\n" + "=" * 80)
    print("TEST 2: ITEMS WITH SALES AND WASTE")
    print("=" * 80)
    
    stocktake = find_stocktake_with_data()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    # Find items with sales
    lines_with_sales = stocktake.lines.exclude(
        sales=Decimal('0')
    ).order_by('-sales')[:5]
    
    # Find items with waste
    lines_with_waste = stocktake.lines.exclude(
        waste=Decimal('0')
    ).order_by('-waste')[:5]
    
    if lines_with_sales.exists():
        print("\n" + "-" * 80)
        print("TOP 5 ITEMS BY SALES:")
        print("-" * 80)
        
        for i, line in enumerate(lines_with_sales, 1):
            print(f"\n{i}. {line.item.sku} - {line.item.name}")
            print(f"   Opening: {line.opening_qty:.2f} | "
                  f"Sales: {line.sales:.2f} | "
                  f"Waste: {line.waste:.2f}")
            print(f"   Expected: {line.expected_qty:.2f} | "
                  f"Counted: {line.counted_qty:.2f} | "
                  f"Variance: {line.variance_qty:.2f}")
            print(f"   Formula: {line.opening_qty:.2f} + "
                  f"{line.purchases:.2f} + {line.transfers_in:.2f} - "
                  f"{line.sales:.2f} - {line.waste:.2f} - "
                  f"{line.transfers_out:.2f} + {line.adjustments:.2f} "
                  f"= {line.expected_qty:.2f}")
    else:
        print("\n❌ No items with sales found")
    
    if lines_with_waste.exists():
        print("\n" + "-" * 80)
        print("TOP 5 ITEMS BY WASTE:")
        print("-" * 80)
        
        for i, line in enumerate(lines_with_waste, 1):
            print(f"\n{i}. {line.item.sku} - {line.item.name}")
            print(f"   Opening: {line.opening_qty:.2f} | "
                  f"Sales: {line.sales:.2f} | "
                  f"Waste: {line.waste:.2f}")
            print(f"   Expected: {line.expected_qty:.2f} | "
                  f"Counted: {line.counted_qty:.2f} | "
                  f"Variance: {line.variance_qty:.2f}")
            print(f"   Formula: {line.opening_qty:.2f} + "
                  f"{line.purchases:.2f} + {line.transfers_in:.2f} - "
                  f"{line.sales:.2f} - {line.waste:.2f} - "
                  f"{line.transfers_out:.2f} + {line.adjustments:.2f} "
                  f"= {line.expected_qty:.2f}")
    else:
        print("\n❌ No items with waste found")


def test_category_with_movements():
    """Test category totals including sales and waste"""
    print("\n\n" + "=" * 80)
    print("TEST 3: CATEGORY TOTALS WITH SALES & WASTE")
    print("=" * 80)
    
    stocktake = find_stocktake_with_data()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    print(f"\nStocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    
    # Test each category
    categories = ['D', 'B', 'S', 'W', 'M']
    category_names = {
        'D': 'Draught Beer',
        'B': 'Bottled Beer',
        'S': 'Spirits',
        'W': 'Wine',
        'M': 'Mixers & Syrups'
    }
    
    for cat_code in categories:
        totals = stocktake.get_category_totals(category_code=cat_code)
        
        if not totals or totals['item_count'] == 0:
            continue
        
        print(f"\n" + "=" * 80)
        print(f"CATEGORY: {cat_code} - {category_names.get(cat_code, 'Unknown')}")
        print(f"Items: {totals['item_count']}")
        print("=" * 80)
        
        opening = float(totals['opening_qty'])
        purchases = float(totals['purchases'])
        transfers_in = float(totals['transfers_in'])
        sales = float(totals['sales'])
        waste = float(totals['waste'])
        transfers_out = float(totals['transfers_out'])
        adjustments = float(totals['adjustments'])
        expected = float(totals['expected_qty'])
        counted = float(totals['counted_qty'])
        variance = float(totals['variance_qty'])
        
        print(f"\n  Opening Stock:        {opening:>15,.2f} servings")
        
        if purchases > 0:
            print(f"  + Purchases:          {purchases:>15,.2f} ✓")
        else:
            print(f"  + Purchases:          {purchases:>15,.2f}")
        
        if transfers_in > 0:
            print(f"  + Transfers In:       {transfers_in:>15,.2f} ✓")
        else:
            print(f"  + Transfers In:       {transfers_in:>15,.2f}")
        
        if sales > 0:
            print(f"  - Sales:              {sales:>15,.2f} ✓")
        else:
            print(f"  - Sales:              {sales:>15,.2f}")
        
        if waste > 0:
            print(f"  - Waste:              {waste:>15,.2f} ✓")
        else:
            print(f"  - Waste:              {waste:>15,.2f}")
        
        if transfers_out > 0:
            print(f"  - Transfers Out:      {transfers_out:>15,.2f} ✓")
        else:
            print(f"  - Transfers Out:      {transfers_out:>15,.2f}")
        
        if adjustments != 0:
            print(f"  + Adjustments:        {adjustments:>15,.2f} ✓")
        else:
            print(f"  + Adjustments:        {adjustments:>15,.2f}")
        
        print("-" * 80)
        print(f"  = EXPECTED:           {expected:>15,.2f} servings")
        print(f"\n  Counted:              {counted:>15,.2f} servings")
        print(f"  Variance:             {variance:>15,.2f} servings")
        
        # Calculate percentage
        if expected != 0:
            var_pct = (variance / expected) * 100
            print(f"\n  Variance %:           {var_pct:>15,.2f}%")
        
        # Verify formula
        manual_expected = opening + purchases + transfers_in - sales - waste - transfers_out + adjustments
        print(f"\n  ✅ Manual calc:        {manual_expected:>15,.2f}")
        print(f"  ✅ Method result:      {expected:>15,.2f}")
        print(f"  ✅ Match: {abs(manual_expected - expected) < 0.01}")


def test_all_categories_summary():
    """Summary showing impact of sales and waste across all categories"""
    print("\n\n" + "=" * 80)
    print("TEST 4: ALL CATEGORIES SUMMARY (With Sales & Waste Impact)")
    print("=" * 80)
    
    stocktake = find_stocktake_with_data()
    if not stocktake:
        print("❌ No stocktake found")
        return
    
    print(f"\nStocktake ID: {stocktake.id}")
    print(f"Period: {stocktake.period_start} to {stocktake.period_end}")
    
    all_totals = stocktake.get_category_totals()
    
    print("\n" + "=" * 80)
    print(f"{'Cat':<4} {'Name':<15} {'Opening':>10} {'Purch':>8} "
          f"{'Sales':>8} {'Waste':>8} {'Expected':>10} {'Counted':>10}")
    print("=" * 80)
    
    grand_opening = Decimal('0')
    grand_purchases = Decimal('0')
    grand_sales = Decimal('0')
    grand_waste = Decimal('0')
    grand_expected = Decimal('0')
    grand_counted = Decimal('0')
    
    for code in ['D', 'B', 'S', 'W', 'M']:
        if code in all_totals:
            cat = all_totals[code]
            opening = float(cat['opening_qty'])
            purchases = float(cat['purchases'])
            sales = float(cat['sales'])
            waste = float(cat['waste'])
            expected = float(cat['expected_qty'])
            counted = float(cat['counted_qty'])
            
            print(f"{cat['category_code']:<4} {cat['category_name']:<15} "
                  f"{opening:>10,.2f} {purchases:>8,.2f} "
                  f"{sales:>8,.2f} {waste:>8,.2f} "
                  f"{expected:>10,.2f} {counted:>10,.2f}")
            
            grand_opening += Decimal(str(opening))
            grand_purchases += Decimal(str(purchases))
            grand_sales += Decimal(str(sales))
            grand_waste += Decimal(str(waste))
            grand_expected += Decimal(str(expected))
            grand_counted += Decimal(str(counted))
    
    print("=" * 80)
    print(f"{'TOTAL':<20} {float(grand_opening):>10,.2f} "
          f"{float(grand_purchases):>8,.2f} "
          f"{float(grand_sales):>8,.2f} {float(grand_waste):>8,.2f} "
          f"{float(grand_expected):>10,.2f} {float(grand_counted):>10,.2f}")
    print("=" * 80)
    
    print(f"\n📊 Impact Analysis:")
    if float(grand_sales) > 0:
        print(f"   Sales reduced expected by: {float(grand_sales):,.2f} servings")
    if float(grand_waste) > 0:
        print(f"   Waste reduced expected by: {float(grand_waste):,.2f} servings")
    if float(grand_purchases) > 0:
        print(f"   Purchases increased by: {float(grand_purchases):,.2f} servings")
    
    print(f"\n   Formula: {float(grand_opening):,.2f} + "
          f"{float(grand_purchases):,.2f} - {float(grand_sales):,.2f} - "
          f"{float(grand_waste):,.2f} = {float(grand_expected):,.2f}")


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("EXPECTED QUANTITY TESTS - WITH SALES & WASTE")
    print("Formula: expected = opening + purchases + transfers_in - "
          "sales - waste - transfers_out + adjustments")
    print("*" * 80)
    
    test_single_item_with_movements()
    test_items_with_waste_and_sales()
    test_category_with_movements()
    test_all_categories_summary()
    
    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print()
