"""
Recategorize wrongly classified JUICES items to SOFT_DRINKS.

PROBLEM:
- Several items are classified as JUICES but are actually small bottles (splits)
- These should be SOFT_DRINKS (cases + bottles dozen tracking)
- Only 1L bottles should be JUICES (cases + bottles + ml tracking)

ITEMS TO MOVE:
- M0042: Lemonade Red Nashs (Doz) → SOFT_DRINKS
- M0070: Split Friuce Juices (Doz) → SOFT_DRINKS  
- M0210: Lemonade WhiteNashes (Doz) → SOFT_DRINKS
- M0312: Splits Britvic Juices (Doz) → SOFT_DRINKS

ITEMS TO KEEP:
- M11: Kulana Litre Juices (Ind) → JUICES (correct)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 80)
print("RECATEGORIZE JUICES → SOFT_DRINKS")
print("=" * 80)

# Items to move from JUICES to SOFT_DRINKS
items_to_move = ['M0042', 'M0070', 'M0210', 'M0312']

print("\nITEMS TO RECATEGORIZE:")
print("-" * 80)

for sku in items_to_move:
    try:
        item = StockItem.objects.get(sku=sku)
        print(f"{item.sku:<8} {item.name[:40]:<40} {item.subcategory} → SOFT_DRINKS")
    except StockItem.DoesNotExist:
        print(f"{sku:<8} NOT FOUND")

print("-" * 80)

response = input("\nProceed with recategorization? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Cancelled.")
    exit()

print("\n" + "=" * 80)
print("UPDATING...")
print("=" * 80)

updated_count = 0
for sku in items_to_move:
    try:
        item = StockItem.objects.get(sku=sku)
        old_subcat = item.subcategory
        item.subcategory = 'SOFT_DRINKS'
        item.save()
        print(f"✅ {item.sku} - {item.name[:35]:<35} {old_subcat} → SOFT_DRINKS")
        updated_count += 1
    except StockItem.DoesNotExist:
        print(f"⚠️  {sku} - NOT FOUND")
    except Exception as e:
        print(f"❌ {sku} - ERROR: {e}")

print("\n" + "=" * 80)
print(f"✅ Updated {updated_count} items")
print("=" * 80)

print("\n📝 NEXT STEPS:")
print("1. Re-populate stocktake lines for October")
print("2. Check that opening stock now displays correctly as cases + bottles")
print("3. Verify the remaining JUICES item (M11) still works with ml tracking")
