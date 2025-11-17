"""
Test BIB calculations for all 3 items with 2 full boxes
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB TEST: 2 FULL BOXES FOR ALL 3 ITEMS")
print("="*80)

bib_data = [
    ('M25', 'Splash Cola 18LTR', Decimal('171.16')),
    ('M24', 'Splash Energy18LTR', Decimal('182.64')),
    ('M23', 'Splash White18LTR', Decimal('173.06')),
]

for sku, name, unit_cost in bib_data:
    print(f"\n{'-'*80}")
    print(f"{sku} - {name}")
    print(f"{'-'*80}")
    
    item = StockItem.objects.filter(sku=sku, hotel_id=2).first()
    
    if item:
        # Set 2 full boxes
        item.current_full_units = Decimal('2')
        item.current_partial_units = Decimal('0.00')
        
        total_units = item.current_full_units + item.current_partial_units
        value = item.total_stock_value
        expected = Decimal('2') * unit_cost
        
        print(f"Unit cost per box: €{unit_cost}")
        print(f"Full boxes: {item.current_full_units}")
        print(f"Partial: {item.current_partial_units}")
        print(f"\nCalculation:")
        print(f"  {total_units} × €{unit_cost} = €{value:.2f}")
        print(f"Expected: €{expected:.2f}")
        
        if abs(value - expected) < Decimal('0.01'):
            print("✅ PASS")
        else:
            print(f"❌ FAIL (got €{value:.2f})")
    else:
        print(f"❌ Item not found")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("M25: 2 × €171.16 = €342.32")
print("M24: 2 × €182.64 = €365.28")
print("M23: 2 × €173.06 = €346.12")
print("="*80 + "\n")
