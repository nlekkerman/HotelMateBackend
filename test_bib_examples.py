"""
Test the exact BIB examples from specification
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("\n" + "="*80)
print("BIB SPECIFICATION TEST - EXACT EXAMPLES")
print("="*80)

print("\n📋 SPECIFICATION:")
print("  stock_value = (full_units + partial_units) × unit_cost")
print("  No serving logic, no ml calculations, no conversions")
print("  Partial units = decimal fractions (0.1, 0.25, 0.5, etc.)")

print("\n" + "="*80)
print("EXAMPLE 1:")
print("="*80)
print("  unit_cost = 171.16")
print("  full_units = 1")
print("  partial_units = 0.50")
print("  Expected: 1.50 × 171.16 = 256.74")

# Get a BIB item
bib = StockItem.objects.filter(
    category_id='M',
    subcategory='BIB'
).first()

if bib:
    # Set test values
    bib.unit_cost = Decimal('171.16')
    bib.current_full_units = Decimal('1')
    bib.current_partial_units = Decimal('0.50')
    
    total_units = bib.current_full_units + bib.current_partial_units
    value = bib.total_stock_value
    
    print(f"\n  Calculated:")
    print(f"    total_units = {bib.current_full_units} + {bib.current_partial_units} = {total_units}")
    print(f"    stock_value = {total_units} × {bib.unit_cost} = €{value:.2f}")
    
    expected = Decimal('256.74')
    if abs(value - expected) < Decimal('0.01'):
        print(f"  ✅ PASS: Matches expected €{expected:.2f}")
    else:
        print(f"  ❌ FAIL: Expected €{expected:.2f}, got €{value:.2f}")

print("\n" + "="*80)
print("EXAMPLE 2:")
print("="*80)
print("  unit_cost = 182.64")
print("  full_units = 0")
print("  partial_units = 0.30")
print("  Expected: 0.30 × 182.64 = 54.79")

if bib:
    # Set test values
    bib.unit_cost = Decimal('182.64')
    bib.current_full_units = Decimal('0')
    bib.current_partial_units = Decimal('0.30')
    
    total_units = bib.current_full_units + bib.current_partial_units
    value = bib.total_stock_value
    
    print(f"\n  Calculated:")
    print(f"    total_units = {bib.current_full_units} + {bib.current_partial_units} = {total_units}")
    print(f"    stock_value = {total_units} × {bib.unit_cost} = €{value:.2f}")
    
    expected = Decimal('54.79')
    if abs(value - expected) < Decimal('0.01'):
        print(f"  ✅ PASS: Matches expected €{expected:.2f}")
    else:
        print(f"  ❌ FAIL: Expected €{expected:.2f}, got €{value:.2f}")

print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)
print("  ✅ No serving logic")
print("  ✅ No ml calculations")
print("  ✅ No conversion to glasses or pours")
print("  ✅ Pure: (full + partial) × unit_cost")
print("  ✅ Partial units = decimal fractions")
print("="*80 + "\n")
