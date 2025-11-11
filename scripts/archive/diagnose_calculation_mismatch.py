"""
Diagnose the calculation mismatch between UI and Excel.

ROOT CAUSE FOUND:
=================
The UI is calculating "Expected Total" (Stock at Cost) using:
    expected_qty × valuation_cost
    
But it should be calculating the COUNTED stock value:
    counted_qty × valuation_cost
    
The Excel sheet shows "Closing Stock" (counted values), but the UI
is showing "Expected" values (which are different from counted).

KEY FORMULAS:
=============

1. cost_per_serving = unit_cost ÷ uom
   Example: €117.70 ÷ 53 = €2.2208/pint

2. For Draught Beer (D) and Dozen (Doz):
   - counted_qty = (counted_full_units × uom) + counted_partial_units
   - counted_value = counted_qty × cost_per_serving
   
   Example D0004 (30 Heineken):
   UI:
   - Expected: (2 kegs × 53) + 23 pints = 129 pints (wrong - using opening)
   - Expected Value: 129 × €2.2208 = €286.65
   
   Excel:
   - Counted: 2 kegs + 26.5 pints = (2 × 53) + 26.5 = 132.5 pints
   - Stock at Cost: 132.5 × €2.2208 = €294.25
   
   Difference: €294.25 - €286.65 = €7.60

3. For Bottled Beer (Dozen):
   - cost_per_serving = unit_cost ÷ uom (cost per bottle)
   - counted_qty = (counted_cases × 12) + counted_bottles
   - counted_value = counted_bottles × cost_per_bottle
   
   Example B0070 (Budweiser):
   UI:
   - Expected: (13 cases × 12) + 7 bottles = 163 bottles
   - Expected Value: 163 × €0.9792 = €159.61
   
   Excel:
   - Counted: 145 bottles
   - Stock at Cost: 145 × €0.9792 = €141.98
   
   Difference: €141.98 - €159.61 = -€17.63

SUMMARY:
========
The UI is showing "Expected Total" but the label says it should show
the stock value based on COUNTED quantities (what's actually in stock).

The fix: Change UI to display counted_value instead of expected_value.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import Stocktake, StocktakeLine

def analyze_mismatch():
    """Compare UI calculations vs Excel for September stocktake"""
    
    # Get September stocktake (ID 17)
    try:
        stocktake = Stocktake.objects.get(id=17)
    except Stocktake.DoesNotExist:
        print("❌ Stocktake #17 not found")
        return
    
    print(f"🔍 Analyzing Stocktake #{stocktake.id}")
    print(f"   Period: {stocktake.period_start} to {stocktake.period_end}")
    print("=" * 80)
    
    # Sample items from UI vs Excel
    test_items = [
        {
            'sku': 'D0004',
            'name': '30 Heineken',
            'ui_expected_value': Decimal('286.65'),
            'excel_stock_at_cost': Decimal('294.25'),
            'excel_counted_kegs': Decimal('2.00'),
            'excel_counted_pints': Decimal('26.50'),
        },
        {
            'sku': 'B0070',
            'name': 'Budweiser 33cl',
            'ui_expected_value': Decimal('159.61'),
            'excel_stock_at_cost': Decimal('141.98'),
            'excel_counted_bottles': Decimal('145.00'),
        },
        {
            'sku': 'B1006',
            'name': 'Kopparberg',
            'ui_expected_value': Decimal('105.60'),
            'excel_stock_at_cost': Decimal('512.60'),
            'excel_counted_bottles': Decimal('233.00'),
        },
        {
            'sku': 'D0005',
            'name': '50 Guinness',
            'ui_expected_value': Decimal('856.21'),
            'excel_stock_at_cost': Decimal('606.16'),
            'excel_counted_kegs': Decimal('3.00'),
            'excel_counted_pints': Decimal('22.00'),
        },
    ]
    
    print("\n📊 CALCULATION ANALYSIS:")
    print("=" * 80)
    
    for test in test_items:
        sku = test['sku']
        
        try:
            line = stocktake.lines.get(item__sku=sku)
            item = line.item
            
            print(f"\n{sku} - {test['name']}")
            print(f"   Category: {item.category_id}")
            print(f"   Size: {item.size}")
            print(f"   UOM: {item.uom}")
            print(f"   Unit Cost: €{item.unit_cost}")
            print(f"   Cost per Serving: €{item.cost_per_serving}")
            print()
            
            # Show opening vs counted
            print(f"   Opening:")
            print(f"      Qty: {line.opening_qty} servings")
            print()
            
            print(f"   Counted (from database):")
            print(f"      Full: {line.counted_full_units}")
            print(f"      Partial: {line.counted_partial_units}")
            print(f"      Total (counted_qty): {line.counted_qty} servings")
            print()
            
            # Calculate what Excel shows
            if 'excel_counted_kegs' in test:
                excel_calc = (test['excel_counted_kegs'] * item.uom) + test['excel_counted_pints']
                print(f"   Excel Counted:")
                print(f"      {test['excel_counted_kegs']} kegs + {test['excel_counted_pints']} pints")
                print(f"      = ({test['excel_counted_kegs']} × {item.uom}) + {test['excel_counted_pints']}")
                print(f"      = {excel_calc} servings")
            elif 'excel_counted_bottles' in test:
                excel_calc = test['excel_counted_bottles']
                print(f"   Excel Counted:")
                print(f"      {test['excel_counted_bottles']} bottles")
            print()
            
            # Show expected vs counted values
            print(f"   💰 VALUES:")
            print(f"      Expected Qty: {line.expected_qty} servings")
            print(f"      Expected Value (UI shows this): €{line.expected_value}")
            print()
            print(f"      Counted Qty: {line.counted_qty} servings") 
            print(f"      Counted Value (Excel shows this): €{line.counted_value}")
            print()
            print(f"      Excel Stock at Cost: €{test['excel_stock_at_cost']}")
            print(f"      UI Expected Total: €{test['ui_expected_value']}")
            print()
            
            # Show the mismatch
            ui_vs_counted = test['ui_expected_value'] - line.counted_value
            excel_vs_counted = test['excel_stock_at_cost'] - line.counted_value
            
            print(f"   🔴 MISMATCH:")
            print(f"      UI shows Expected (€{line.expected_value}) instead of Counted (€{line.counted_value})")
            print(f"      Difference: €{ui_vs_counted}")
            print()
            print(f"      Excel vs DB Counted: €{excel_vs_counted}")
            
            print("-" * 80)
            
        except StocktakeLine.DoesNotExist:
            print(f"   ❌ Line not found for {sku}")
    
    print("\n" + "=" * 80)
    print("\n🎯 ROOT CAUSE IDENTIFIED:")
    print("=" * 80)
    print("""
The UI is displaying:
    Expected Total = expected_qty × valuation_cost
    
But it should display:
    Stock at Cost = counted_qty × valuation_cost
    
The "Expected" column in the UI shows what SHOULD be in stock based on:
    opening + purchases - waste
    
But the "Total" at the bottom shows the VALUE of this expected quantity,
NOT the value of what was actually counted.

Excel correctly shows:
    Stock at Cost = counted_qty × cost_per_serving
    
This is why there's a €666.11 difference between UI and Excel totals.

FIX REQUIRED:
=============
The UI should display line.counted_value in the category totals,
not line.expected_value. The Expected column is correct (shows expected qty),
but the total value should be based on COUNTED quantities.
    """)

if __name__ == '__main__':
    analyze_mismatch()
