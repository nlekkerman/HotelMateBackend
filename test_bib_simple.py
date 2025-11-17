"""
Simple test: Set BIB stock to known values and verify calculation
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB SIMPLE VALUATION TEST")
print("="*80)

item = StockItem.objects.filter(sku='M25', hotel_id=2).first()

if item:
    print(f"\n{item.sku} - {item.name}")
    print(f"unit_cost: €{item.unit_cost}")
    
    # Test 1: 2 boxes
    item.current_full_units = Decimal('2')
    item.current_partial_units = Decimal('0')
    
    value = item.total_stock_value
    expected = Decimal('2') * item.unit_cost
    
    print(f"\nTest 1: 2.00 boxes")
    print(f"  Expected: 2 × €{item.unit_cost} = €{expected:.2f}")
    print(f"  Actual:   €{value:.2f}")
    print(f"  {'✅ PASS' if abs(value - expected) < Decimal('0.01') else '❌ FAIL'}")
    
    # Test 2: 2.5 boxes
    item.current_full_units = Decimal('2')
    item.current_partial_units = Decimal('0.5')
    
    value = item.total_stock_value
    expected = Decimal('2.5') * item.unit_cost
    
    print(f"\nTest 2: 2.50 boxes")
    print(f"  Expected: 2.5 × €{item.unit_cost} = €{expected:.2f}")
    print(f"  Actual:   €{value:.2f}")
    print(f"  {'✅ PASS' if abs(value - expected) < Decimal('0.01') else '❌ FAIL'}")

print("\n" + "="*80 + "\n")
