"""
Fix syrups and certain minerals items that should be counted as INDIVIDUAL bottles,
not as cases/dozen.

Items like syrups (Monin), mixer juices (lemon/lime), etc. cannot be sold individually
so they should be counted as individual bottles (UOM = 1), not as cases (UOM = 12).

Based on your spreadsheet:
- All syrups (Monin, Teisseire, etc.) with "Ind" size → UOM = 1
- Mixer juices (Lemon Juice, Lime Juice) with "Ind" size → UOM = 1
- Grenadine Syrup with size "70cl" → UOM = 1

Items that REMAIN as dozen (UOM = 12):
- All splits (Sprite, Coke, 7UP, etc.) - sold per bottle
- Appletiser, Red Bull, Schweppes, etc. - sold per bottle
- These should stay as "Doz" with UOM = 12
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem, StockPeriod, StockSnapshot
from decimal import Decimal

print("=" * 120)
print("FIXING SYRUP/INDIVIDUAL ITEMS UOM AND SUBCATEGORY")
print("=" * 120)

# Find all items that should be INDIVIDUAL (not cases)
items_to_fix = [
    # Mixer Juices (currently showing as Ind but might have wrong UOM)
    'M0008',  # Mixer Lemon Juice 700ML
    'M0009',  # Mixer Lime Juice 700ML
    
    # Monin Syrups (all individual bottles)
    'M3',     # Monin Agave Syrup 700ml
    'M0006',  # Monin Chocolate Cookie LTR
    'M13',    # Monin Coconut Syrup 700ML
    'M04',    # Monin Elderflower Syrup 700M
    'M0014',  # Monin Ginger Syrup
    'M2',     # Monin Passionfruit Puree Ltr
    'M03',    # Monin Passionfruit Syrup 700M70cl
    'M05',    # Monin Pink Grapefruit 700ML
    'M06',    # Monin Puree Coconut LTR
    'M1',     # Monin Strawberry Puree Ltr
    'M5',     # Monin Strawberry Syrup 700ml
    'M9',     # Monin Vanilla Syrup Ltr
    'M02',    # Monin Watermelon Syrup 700M
    
    # Grenadine
    'M0320',  # Grenadine Syrup 70cl
    
    # Teisseire
    'M0012',  # Teisseire Bubble Gum
    
    # Kulana Juices (already individual based on your data)
    'M11',    # Kulana Litre Juices
]

print(f"\nSearching for {len(items_to_fix)} items to convert to INDIVIDUAL...")

# Get all items
for sku in items_to_fix:
    try:
        item = StockItem.objects.get(sku=sku, category_id='M')
        
        print(f"\n{item.sku} - {item.name}")
        print(f"  Current: Size={item.size} | UOM={item.uom} | Subcategory={item.subcategory}")
        print(f"  Current Stock: {item.current_full_units} full + {item.current_partial_units} partial")
        
        # Determine new UOM based on size
        new_uom = Decimal('1.00')  # Default to 1 (individual)
        new_subcategory = 'SYRUPS'  # Most are syrups
        
        # Check bottle size from name/size to set correct UOM for SYRUPS subcategory
        size_upper = item.size.upper()
        name_upper = item.name.upper()
        
        if '700' in name_upper or '70CL' in name_upper or '70CL' in size_upper:
            new_uom = Decimal('700.00')  # 700ml bottle
        elif '1L' in size_upper or 'LTR' in name_upper or 'LITRE' in name_upper:
            new_uom = Decimal('1000.00')  # 1L = 1000ml bottle
        elif 'JUICE' in name_upper and 'MIX' not in name_upper:
            # Kulana juices might be different
            new_subcategory = 'BULK_JUICES'
            new_uom = Decimal('1.00')  # Individual bottles
        
        # Special handling for mixer juices
        if 'MIXER' in name_upper and 'JUICE' in name_upper:
            new_uom = Decimal('700.00')  # 700ML bottles
            new_subcategory = 'SYRUPS'
        
        print(f"  NEW: UOM={new_uom} | Subcategory={new_subcategory}")
        
        # Convert stock if needed
        # Current stock is in the OLD format, need to check how it's stored
        old_full = item.current_full_units
        old_partial = item.current_partial_units
        
        # If this was stored as dozen before (UOM = 12):
        # full_units = cases, partial_units = bottles
        # We need to convert to: full_units + partial_units (as bottles)
        
        if item.uom == Decimal('12.00'):
            # Was stored as cases + bottles
            # Convert to total bottles
            total_bottles = (old_full * item.uom) + old_partial
            
            # For SYRUPS: store as bottles (decimal)
            # full_units = whole bottles, partial_units = fractional
            new_full = int(total_bottles)
            new_partial = total_bottles - new_full
            
            print(f"  Converting stock: {old_full} cases + {old_partial} bottles = {total_bottles} bottles")
            print(f"  New stock format: {new_full} bottles + {new_partial:.3f} fractional")
        
        elif item.uom == Decimal('1.00'):
            # Already individual, no conversion needed
            new_full = old_full
            new_partial = old_partial
            print(f"  Stock unchanged (already individual): {new_full} + {new_partial}")
        
        else:
            # Unknown previous format, keep as is
            new_full = old_full
            new_partial = old_partial
            print(f"  Stock unchanged (unknown format): {new_full} + {new_partial}")
        
        # Update the item
        item.subcategory = new_subcategory
        item.uom = new_uom
        item.current_full_units = Decimal(str(new_full))
        item.current_partial_units = Decimal(str(new_partial))
        item.save()
        
        print(f"  ✓ UPDATED")
        
    except StockItem.DoesNotExist:
        print(f"\n⚠ {sku} - NOT FOUND")
        continue

print("\n" + "=" * 120)
print("VERIFICATION - Check updated items:")
print("=" * 120)

for sku in items_to_fix[:5]:  # Show first 5 as sample
    try:
        item = StockItem.objects.get(sku=sku, category_id='M')
        print(f"\n{item.sku} - {item.name}")
        print(f"  Size: {item.size} | UOM: {item.uom} | Subcategory: {item.subcategory}")
        print(f"  Stock: {item.current_full_units} + {item.current_partial_units}")
        print(f"  Total servings: {item.total_stock_in_servings:.2f}")
    except StockItem.DoesNotExist:
        continue

print("\n" + "=" * 120)
print("SUMMARY OF CHANGES:")
print("=" * 120)
print("""
ITEMS CHANGED TO INDIVIDUAL (UOM per bottle size):
- All Monin Syrups: UOM = 700ml or 1000ml (depending on bottle size)
- Mixer Juices: UOM = 700ml
- Grenadine: UOM = 700ml
- Teisseire: UOM = appropriate bottle size
- Kulana Juices: UOM = 1 (if BULK_JUICES subcategory)

COUNTING METHOD:
- SYRUPS: Enter as decimal bottles (e.g., 10.5 bottles)
- BULK_JUICES: Enter as decimal bottles (e.g., 43.5 bottles)

ITEMS THAT REMAIN AS DOZEN (UOM = 12):
- All Splits (Sprite, Coke, 7UP, etc.)
- Schweppes, Red Bull, Lucozade, etc.
- Any item with "Split" or "Doz" in size
- Items that ARE sold individually per bottle

NOTE: Snapshots in previous periods may need recalculation if this changes
the stock tracking method significantly.
""")
