"""
Verify the syrup setup and identify any remaining issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

print("=" * 120)
print("VERIFYING SYRUP/INDIVIDUAL ITEMS SETUP")
print("=" * 120)

# Get all SYRUPS items
syrups = StockItem.objects.filter(
    category_id='M',
    subcategory='SYRUPS'
).order_by('sku')

print(f"\nTotal SYRUPS items: {syrups.count()}\n")

# Check for issues
issues = []

for item in syrups:
    print(f"{item.sku:10s} | {item.name:50s}")
    print(f"           | Size: {item.size:10s} | UOM: {item.uom:7.2f} ml")
    print(f"           | Stock: {item.current_full_units} + {item.current_partial_units}")
    
    # Check for potential issues
    if item.uom == Decimal('1.00') or item.uom < Decimal('100.00'):
        issues.append({
            'sku': item.sku,
            'name': item.name,
            'issue': f'UOM too small ({item.uom}), should be bottle size in ml',
            'suggested_fix': 'Check name/size to determine correct bottle size'
        })
        print(f"           | ⚠️ WARNING: UOM={item.uom} seems wrong!")
    
    print()

# Get all BULK_JUICES items
bulk_juices = StockItem.objects.filter(
    category_id='M',
    subcategory='BULK_JUICES'
).order_by('sku')

print("\n" + "=" * 120)
print(f"BULK_JUICES items: {bulk_juices.count()}\n")

for item in bulk_juices:
    print(f"{item.sku:10s} | {item.name:50s}")
    print(f"           | Size: {item.size:10s} | UOM: {item.uom:7.2f}")
    print(f"           | Stock: {item.current_full_units} + {item.current_partial_units}")
    print()

# Print issues summary
if issues:
    print("\n" + "=" * 120)
    print("ISSUES FOUND:")
    print("=" * 120)
    for issue in issues:
        print(f"\n{issue['sku']} - {issue['name']}")
        print(f"  Issue: {issue['issue']}")
        print(f"  Suggestion: {issue['suggested_fix']}")
else:
    print("\n" + "=" * 120)
    print("✓ NO ISSUES FOUND - All syrups have correct UOM values")
    print("=" * 120)
