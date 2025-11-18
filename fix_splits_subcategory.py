"""
Fix M0070 and M0312 - Move from JUICES to SOFT_DRINKS subcategory

These are split bottles (small individual bottles) sold by the dozen,
not large juice bottles. They should be in SOFT_DRINKS category.

Current (WRONG):
- M0070: Split Friuce Juices - Subcategory: JUICES
- M0312: Splits Britvic Juices - Subcategory: JUICES

Target (CORRECT):
- M0070: Split Friuce Juices - Subcategory: SOFT_DRINKS
- M0312: Splits Britvic Juices - Subcategory: SOFT_DRINKS

Logic:
- Size: Doz (dozen) - means sold in cases of 12 individual bottles
- These are small 275ml bottles (splits), NOT large 1L juice bottles
- Should be counted as: cases + bottles (like other soft drinks)
- Should NOT use juice serving logic (200ml servings)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

def fix_splits_subcategory():
    """Move split bottle items from JUICES to SOFT_DRINKS"""
    
    items_to_fix = ['M0070', 'M0312']
    
    print("=" * 70)
    print("FIX SPLITS SUBCATEGORY")
    print("=" * 70)
    print("\nMoving split bottle items from JUICES to SOFT_DRINKS\n")
    
    for sku in items_to_fix:
        try:
            item = StockItem.objects.get(sku=sku)
            
            print(f"\n{'='*70}")
            print(f"SKU: {sku}")
            print(f"Name: {item.name}")
            print(f"{'='*70}")
            
            # Show current state
            print(f"\n📋 CURRENT STATE:")
            print(f"   Category: {item.category_id}")
            print(f"   Subcategory: {item.subcategory}")
            print(f"   Size: {item.size}")
            print(f"   UOM: {item.uom} (bottles per case)")
            print(f"   Current Stock: {item.current_full_units} cases + {item.current_partial_units} bottles")
            
            # Verify it's in JUICES
            if item.subcategory != 'JUICES':
                print(f"\n⚠️  Item is already in {item.subcategory} subcategory")
                continue
            
            # Update subcategory
            print(f"\n🔧 FIXING:")
            print(f"   Changing subcategory from JUICES → SOFT_DRINKS")
            
            item.subcategory = 'SOFT_DRINKS'
            item.save()
            
            print(f"\n✅ FIXED!")
            print(f"   New Subcategory: {item.subcategory}")
            
            # Verify serving calculation
            print(f"\n📊 SERVING CALCULATION (SOFT_DRINKS logic):")
            print(f"   Cases: {item.current_full_units}")
            print(f"   Bottles: {item.current_partial_units}")
            print(f"   Total servings: {item.total_stock_in_servings}")
            print(f"   Formula: ({item.current_full_units} cases × {item.uom}) + {item.current_partial_units} bottles")
            
        except StockItem.DoesNotExist:
            print(f"\n❌ Item {sku} not found!")
        except Exception as e:
            print(f"\n❌ Error fixing {sku}: {e}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    # Show final state
    for sku in items_to_fix:
        try:
            item = StockItem.objects.get(sku=sku)
            status = "✅" if item.subcategory == 'SOFT_DRINKS' else "❌"
            print(f"{status} {sku}: {item.name}")
            print(f"   Subcategory: {item.subcategory}")
        except:
            pass
    
    print("\n" + "="*70)
    print("\n✅ All split bottles moved to SOFT_DRINKS!")
    print("\nThese items will now:")
    print("  - Be counted as: cases + bottles (not servings)")
    print("  - Use SOFT_DRINKS display logic")
    print("  - Show correct stock values")
    print("\n" + "="*70)

if __name__ == '__main__':
    fix_splits_subcategory()
