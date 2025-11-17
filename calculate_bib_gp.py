"""
Calculate GP for BIB items with actual stock and menu prices
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB GP CALCULATION WITH ACTUAL STOCK & MENU PRICES")
print("="*80)

# Data from Excel: SKU, boxes, menu_price, expected_gp
bib_data = {
    'M25': {
        'name': 'Splash Cola 18LTR',
        'boxes': Decimal('0.80'),
        'menu_price': Decimal('2.50'),
        'expected_gp': Decimal('83.16')
    },
    'M24': {
        'name': 'Splash Energy18LTR',
        'boxes': Decimal('0.35'),
        'menu_price': Decimal('1.50'),
        'expected_gp': Decimal('70.05')
    },
    'M23': {
        'name': 'Splash White18LTR',
        'boxes': Decimal('0.80'),
        'menu_price': Decimal('1.50'),
        'expected_gp': Decimal('71.62')
    }
}

for sku, data in bib_data.items():
    print(f"\n{'-'*80}")
    print(f"{sku} - {data['name']}")
    print(f"{'-'*80}")
    
    item = StockItem.objects.filter(sku=sku, hotel_id=2).first()
    
    if item:
        # Set menu price
        item.menu_price = data['menu_price']
        item.save()
        
        # Set stock
        item.current_full_units = Decimal('0')
        item.current_partial_units = data['boxes']
        
        print(f"\nStock Configuration:")
        print(f"  Total boxes: {data['boxes']}")
        print(f"  unit_cost: €{item.unit_cost} per box")
        print(f"  menu_price: €{data['menu_price']} per serving")
        
        # Calculate servings
        servings_per_box = 500  # 18000ml ÷ 36ml
        total_servings = float(data['boxes']) * servings_per_box
        
        print(f"\nServings Calculation:")
        print(f"  Servings per box: {servings_per_box}")
        print(f"  Total servings: {data['boxes']} × {servings_per_box} = {total_servings:.0f}")
        
        # Cost calculations
        cost_per_serving = item.cost_per_serving
        stock_value = item.total_stock_value
        
        print(f"\nCost Analysis:")
        print(f"  cost_per_serving: €{cost_per_serving:.4f}")
        print(f"  Stock value: €{stock_value:.2f}")
        
        # GP calculations
        gp_per_serving = item.gross_profit_per_serving
        gp_percentage = item.gross_profit_percentage
        
        total_revenue = total_servings * float(data['menu_price'])
        total_cost = float(stock_value)
        total_gp = total_revenue - total_cost
        gp_pct_manual = (total_gp / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"\nGP Calculation:")
        print(f"  GP per serving: €{data['menu_price']} - €{cost_per_serving:.4f} = €{gp_per_serving:.4f}")
        print(f"  GP percentage: {gp_percentage:.2f}%")
        
        print(f"\nTotal Revenue & GP:")
        print(f"  Revenue: {total_servings:.0f} × €{data['menu_price']} = €{total_revenue:.2f}")
        print(f"  Cost: €{total_cost:.2f}")
        print(f"  Total GP: €{total_gp:.2f}")
        print(f"  GP%: {gp_pct_manual:.2f}%")
        
        print(f"\nComparison:")
        print(f"  Expected GP: €{data['expected_gp']}")
        print(f"  Calculated GP: €{total_gp:.2f}")
        diff = total_gp - float(data['expected_gp'])
        print(f"  Difference: €{diff:.2f}")
        
        if abs(diff) < 0.10:
            print(f"  ✅ MATCH!")
        else:
            print(f"  ⚠️ DIFFERENCE")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("Formula: GP = (servings × menu_price) - (boxes × unit_cost)")
print("Where: 1 box = 500 servings (18L ÷ 36ml)")
print("="*80 + "\n")
