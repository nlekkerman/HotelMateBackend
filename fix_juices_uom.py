"""
Fix JUICES items UOM to represent bottle size in ML instead of bottles per case.

PROBLEM:
- JUICES items currently have UOM=12 (bottles per case)
- But JUICES 3-level tracking needs UOM=bottle size in ML
- This causes incorrect display calculations (800 cases instead of 9 cases)

SOLUTION:
- Update all JUICES items to have UOM=bottle size in ML
- For 1L juices: UOM=1000
- For split bottles: UOM=330 or 275 (depending on actual size)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockItem

print("=" * 80)
print("FIX JUICES UOM VALUES")
print("=" * 80)

# Get all JUICES items
juices = StockItem.objects.filter(subcategory='JUICES')

print(f"\nFound {juices.count()} JUICES items\n")

# Manual mapping based on item names and sizes
# You'll need to verify these values based on actual bottle sizes
juice_uom_mapping = {
    'M0042': {'name': 'Lemonade Red Nashs', 'bottle_ml': 1000, 'reason': '1L bottle'},
    'M0070': {'name': 'Split Friuce Juices', 'bottle_ml': 275, 'reason': 'Split bottle (assumed 275ml)'},
    'M0210': {'name': 'Lemonade WhiteNashes', 'bottle_ml': 1000, 'reason': '1L bottle'},
    'M0312': {'name': 'Splits Britvic Juices', 'bottle_ml': 275, 'reason': 'Split bottle (assumed 275ml)'},
    'M11': {'name': 'Kulana Litre Juices', 'bottle_ml': 1000, 'reason': '1L bottle (name says "Litre")'},
}

print("CURRENT vs PROPOSED UOM VALUES:")
print("-" * 80)
print(f"{'SKU':<8} {'Name':<30} {'Current UOM':<15} {'New UOM':<15} {'Reason'}")
print("-" * 80)

for item in juices:
    if item.sku in juice_uom_mapping:
        mapping = juice_uom_mapping[item.sku]
        print(f"{item.sku:<8} {item.name[:30]:<30} {item.uom:<15} {mapping['bottle_ml']:<15} {mapping['reason']}")
    else:
        print(f"{item.sku:<8} {item.name[:30]:<30} {item.uom:<15} {'???':<15} UNKNOWN - needs manual check")

print("-" * 80)

# Ask for confirmation
response = input("\n⚠️  Do you want to proceed with the update? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Update cancelled.")
    exit()

print("\n" + "=" * 80)
print("UPDATING UOM VALUES...")
print("=" * 80)

updated_count = 0
for item in juices:
    if item.sku in juice_uom_mapping:
        mapping = juice_uom_mapping[item.sku]
        old_uom = item.uom
        new_uom = Decimal(str(mapping['bottle_ml']))
        
        item.uom = new_uom
        item.save()
        
        print(f"✅ {item.sku} - {item.name[:30]}: {old_uom} → {new_uom} ml")
        updated_count += 1
    else:
        print(f"⚠️  {item.sku} - {item.name[:30]}: SKIPPED (needs manual review)")

print("\n" + "=" * 80)
print(f"✅ Updated {updated_count} items")
print("=" * 80)

print("\n📝 NEXT STEPS:")
print("1. Verify the bottle sizes are correct")
print("2. For 'Split' items, confirm if they're 275ml or 330ml")
print("3. Re-populate stocktake lines to recalculate opening_qty with new UOM")
print("4. Check display values are now correct (e.g., 9 cases instead of 800)")
