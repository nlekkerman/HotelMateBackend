"""
Fix Wine UOM from glasses per bottle to individual bottles (UOM = 1.0)

REASON:
-------
Wine is counted in BOTTLES during stocktake (e.g., 10.5 bottles)
Currently UOM = 5.0 (glasses) causes incorrect calculation:
  10.5 bottles × 5 = 52.5 glasses (WRONG!)
  
Should be:
  10.5 bottles × 1 = 10.5 bottles (CORRECT!)

Sales reporting can use separate pricing (bottle_price, menu_price) but
stocktake MUST count in bottles.
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 120)
print("FIXING WINE UOM: GLASSES → BOTTLES")
print("=" * 120)
print()

# Get all wine items
wines = StockItem.objects.filter(category_id='W', active=True).order_by('sku')

print(f"Total Wine Items: {wines.count()}")
print()

# Group by current UOM
uom_groups = {}
for wine in wines:
    uom_key = float(wine.uom)
    if uom_key not in uom_groups:
        uom_groups[uom_key] = []
    uom_groups[uom_key].append(wine)

print("CURRENT UOM DISTRIBUTION:")
print("-" * 120)
for uom, items in sorted(uom_groups.items()):
    print(f"  UOM = {uom}: {len(items)} items")
print()

print("=" * 120)
print("CHANGES TO BE MADE:")
print("=" * 120)
print()

changes_needed = 0
for wine in wines:
    if wine.uom != Decimal('1.00'):
        changes_needed += 1
        print(f"{wine.sku:15} {wine.name[:50]:50} UOM: {wine.uom} → 1.00")

print()
print(f"Total items to update: {changes_needed}")
print()

if changes_needed == 0:
    print("✅ All wine items already have UOM = 1.00")
    print("No changes needed!")
else:
    response = input(f"\nUpdate {changes_needed} wine items to UOM = 1.00? (yes/no): ")
    
    if response.lower() == 'yes':
        print()
        print("=" * 120)
        print("UPDATING WINE ITEMS...")
        print("=" * 120)
        print()
        
        updated_count = 0
        for wine in wines:
            if wine.uom != Decimal('1.00'):
                old_uom = wine.uom
                old_unit_cost = wine.unit_cost
                
                # Update UOM to 1.0 (individual bottles)
                wine.uom = Decimal('1.00')
                
                # IMPORTANT: unit_cost stays the same!
                # unit_cost = cost per BOTTLE (already correct)
                # We don't change unit_cost because it's already per bottle
                
                wine.save()
                updated_count += 1
                
                print(f"✓ {wine.sku}: UOM {old_uom} → 1.00 | Unit Cost: €{old_unit_cost} (unchanged)")
        
        print()
        print("=" * 120)
        print("SUMMARY:")
        print("=" * 120)
        print(f"✅ Updated {updated_count} wine items")
        print(f"✅ All wines now have UOM = 1.00 (individual bottles)")
        print()
        print("VERIFICATION:")
        print("  - Stocktake will now count: 10 bottles + 0.5 = 10.5 bottles")
        print("  - Calculation: 10.5 × 1.0 = 10.5 bottles ✓")
        print("  - Sales can still use bottle_price and menu_price for reporting")
        print()
    else:
        print("\n❌ Update cancelled")

print()
print("=" * 120)
print("DONE")
print("=" * 120)
