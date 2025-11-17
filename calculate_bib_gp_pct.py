"""
Calculate BIB GP% and find the correct menu prices
Expected GP% from Excel: 83.16%, 70.05%, 71.62%
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB GP% CALCULATION - REVERSE ENGINEER MENU PRICES")
print("="*80)

# Data: SKU, boxes, expected_gp_percentage
bib_data = {
    'M25': {
        'name': 'Splash Cola 18LTR',
        'boxes': Decimal('0.80'),
        'expected_gp_pct': Decimal('83.16')
    },
    'M24': {
        'name': 'Splash Energy18LTR',
        'boxes': Decimal('0.35'),
        'expected_gp_pct': Decimal('70.05')
    },
    'M23': {
        'name': 'Splash White18LTR',
        'boxes': Decimal('0.80'),
        'expected_gp_pct': Decimal('71.62')
    }
}

for sku, data in bib_data.items():
    print(f"\n{'-'*80}")
    print(f"{sku} - {data['name']}")
    print(f"{'-'*80}")
    
    item = StockItem.objects.filter(sku=sku, hotel_id=2).first()
    
    if item:
        print(f"\nConfiguration:")
        print(f"  Stock: {data['boxes']} boxes")
        print(f"  unit_cost: €{item.unit_cost} per box")
        print(f"  Target GP%: {data['expected_gp_pct']}%")
        
        # Calculate cost per serving
        servings_per_box = 500
        total_servings = float(data['boxes']) * servings_per_box
        cost_per_serving = float(item.unit_cost) / servings_per_box
        
        print(f"\nServings:")
        print(f"  Total servings: {total_servings:.0f}")
        print(f"  cost_per_serving: €{cost_per_serving:.4f}")
        
        # Calculate required menu price for target GP%
        # GP% = (menu_price - cost) / menu_price × 100
        # menu_price = cost / (1 - GP%/100)
        target_gp_decimal = float(data['expected_gp_pct']) / 100
        required_menu_price = cost_per_serving / (1 - target_gp_decimal)
        
        print(f"\nRequired Menu Price for {data['expected_gp_pct']}% GP:")
        print(f"  Formula: cost / (1 - GP%/100)")
        print(f"  = €{cost_per_serving:.4f} / (1 - {target_gp_decimal:.4f})")
        print(f"  = €{required_menu_price:.4f}")
        
        # Verify
        gp_per_serving = required_menu_price - cost_per_serving
        gp_pct_verify = (gp_per_serving / required_menu_price) * 100
        
        print(f"\nVerification:")
        print(f"  Menu price: €{required_menu_price:.4f}")
        print(f"  Cost: €{cost_per_serving:.4f}")
        print(f"  GP: €{gp_per_serving:.4f}")
        print(f"  GP%: {gp_pct_verify:.2f}%")
        
        if abs(gp_pct_verify - float(data['expected_gp_pct'])) < 0.01:
            print(f"  ✅ MATCHES {data['expected_gp_pct']}%")
        
        # Calculate total revenue and GP
        total_revenue = total_servings * required_menu_price
        total_cost = float(data['boxes']) * float(item.unit_cost)
        total_gp = total_revenue - total_cost
        
        print(f"\nTotal Values:")
        print(f"  Revenue: {total_servings:.0f} × €{required_menu_price:.4f} = €{total_revenue:.2f}")
        print(f"  Cost: {data['boxes']} × €{item.unit_cost} = €{total_cost:.2f}")
        print(f"  Total GP: €{total_gp:.2f}")
        print(f"  Total GP%: {(total_gp/total_revenue)*100:.2f}%")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("GP% = (menu_price - cost_per_serving) / menu_price × 100")
print("menu_price = cost_per_serving / (1 - GP%/100)")
print("="*80 + "\n")
