"""
Test BIB with 2 full boxes
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB TEST: 2 FULL BOXES")
print("="*80)

# Get a BIB item
bib = StockItem.objects.filter(
    category_id='M',
    subcategory='BIB'
).first()

if bib:
    print(f"\nItem: {bib.sku} - {bib.name}")
    
    # Test with 2 full boxes
    bib.unit_cost = Decimal('171.16')
    bib.current_full_units = Decimal('2')
    bib.current_partial_units = Decimal('0.00')
    
    total_units = bib.current_full_units + bib.current_partial_units
    value = bib.total_stock_value
    
    print(f"\nInput:")
    print(f"  unit_cost = €{bib.unit_cost}")
    print(f"  full_units = {bib.current_full_units}")
    print(f"  partial_units = {bib.current_partial_units}")
    
    print(f"\nCalculation:")
    print(f"  total_units = {bib.current_full_units} + {bib.current_partial_units} = {total_units}")
    print(f"  stock_value = {total_units} × €{bib.unit_cost} = €{value:.2f}")
    
    expected = Decimal('2') * Decimal('171.16')
    print(f"\nExpected: 2 × €171.16 = €{expected:.2f}")
    
    if abs(value - expected) < Decimal('0.01'):
        print(f"✅ PASS")
    else:
        print(f"❌ FAIL")

print("\n" + "="*80 + "\n")
