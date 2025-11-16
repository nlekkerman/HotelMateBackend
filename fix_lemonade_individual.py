"""
Fix JUICES/Lemonade items - Move to Individual tracking

LOGIC:
- Lemonades and Kulana Litre Juices are NOT on the menu
- They're only counted in stocktakes (bulk inventory)
- Should be tracked as Individual bottles (Ind) not Dozens (Doz)
- Display as bottles only, ignore case/dozen tracking

ITEMS TO FIX:
- M0042: Lemonade Red Nashs → Size: Ind, UOM: 1000 (1L bottle)
- M0210: Lemonade WhiteNashes → Size: Ind, UOM: 1000 (1L bottle)
- M11: Kulana Litre Juices → Size: Ind, UOM: 1000 (already Ind, fix UOM)

SPLIT ITEMS (need clarification):
- M0070: Split Friuce Juices → ?
- M0312: Splits Britvic Juices → ?
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockItem

print("=" * 80)
print("FIX LEMONADE & KULANA - INDIVIDUAL TRACKING")
print("=" * 80)

# Items to change to Individual tracking (BULK_JUICES)
lemonade_items = {
    'M0042': {'name': 'Lemonade Red Nashs', 'size': 'Ind', 'uom': 1, 'subcategory': 'BULK_JUICES'},
    'M0210': {'name': 'Lemonade WhiteNashes', 'size': 'Ind', 'uom': 1, 'subcategory': 'BULK_JUICES'},
    'M11': {'name': 'Kulana Litre Juices', 'size': 'Ind', 'uom': 1, 'subcategory': 'BULK_JUICES'},
}

print("\nCURRENT vs NEW:")
print("-" * 80)
print(f"{'SKU':<8} {'Name':<35} {'Old Size':<10} {'New Size':<10} {'Old UOM':<10} {'New UOM'}")
print("-" * 80)

for sku, data in lemonade_items.items():
    try:
        item = StockItem.objects.get(sku=sku)
        print(f"{item.sku:<8} {item.name[:35]:<35} {item.size:<10} {data['size']:<10} {item.uom:<10} {data['uom']}")
    except StockItem.DoesNotExist:
        print(f"{sku:<8} NOT FOUND")

print("-" * 80)

response = input("\nProceed with update? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Cancelled.")
    exit()

print("\n" + "=" * 80)
print("UPDATING...")
print("=" * 80)

for sku, data in lemonade_items.items():
    try:
        item = StockItem.objects.get(sku=sku)
        old_size = item.size
        old_uom = item.uom
        
        item.size = data['size']
        item.uom = Decimal(str(data['uom']))
        item.subcategory = data['subcategory']  # BULK_JUICES
        item.save()
        
        print(f"✅ {item.sku} - {item.name[:30]}")
        print(f"   Size: {old_size} → {item.size}")
        print(f"   UOM: {old_uom} → {item.uom} ml")
    except Exception as e:
        print(f"❌ {sku} - ERROR: {e}")

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
print("\nThese items now:")
print("- Subcategory: BULK_JUICES")
print("- Display: BOTTLES only (no cases, no servings)")
print("- UOM = 1 (individual bottles)")
print("- NOT on menu - just inventory tracking")
