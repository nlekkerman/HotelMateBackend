"""
Fix syrups that have wrong UOM values (1.00 instead of bottle size in ml)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

print("=" * 120)
print("FIXING WRONG SYRUP UOM VALUES")
print("=" * 120)

# Items with wrong UOM that need fixing
fixes = [
    ('M0014', 'Monin Ginger Syrup', 700),  # Should be 700ml
    ('M0320', 'Grenadine Syrup', 700),     # Should be 700ml (70cl)
    ('M0012', 'Teisseire Bubble Gum', 700), # Should be 700ml
]

for sku, name, correct_uom_ml in fixes:
    try:
        item = StockItem.objects.get(sku=sku, category_id='M')
        old_uom = item.uom
        item.uom = Decimal(str(correct_uom_ml))
        item.save()
        
        print(f"\n{sku} - {name}")
        print(f"  Changed UOM: {old_uom} → {item.uom} ml")
        print(f"  ✓ FIXED")
        
    except StockItem.DoesNotExist:
        print(f"\n⚠ {sku} - NOT FOUND")

# Also revert Kulana Juices back to BULK_JUICES if needed
try:
    kulana = StockItem.objects.get(sku='M11', category_id='M')
    if kulana.subcategory == 'SYRUPS':
        kulana.subcategory = 'BULK_JUICES'
        kulana.uom = Decimal('1.00')  # Individual bottles
        kulana.save()
        print(f"\n{kulana.sku} - {kulana.name}")
        print(f"  Reverted to: BULK_JUICES with UOM=1.00")
        print(f"  ✓ FIXED")
except StockItem.DoesNotExist:
    print(f"\n⚠ M11 - NOT FOUND")

print("\n" + "=" * 120)
print("VERIFICATION:")
print("=" * 120)

# Verify all SYRUPS now have correct UOM
syrups = StockItem.objects.filter(
    category_id='M',
    subcategory='SYRUPS'
).order_by('sku')

print(f"\nAll SYRUPS items (Total: {syrups.count()}):\n")

for item in syrups:
    uom_status = "✓" if item.uom >= Decimal('100.00') else "⚠"
    print(f"{uom_status} {item.sku:10s} | {item.name:45s} | UOM: {item.uom:7.2f} ml")

print("\n" + "=" * 120)
print("✓ COMPLETE - All syrups should now have correct UOM values")
print("=" * 120)
