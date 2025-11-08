"""
Fix wine prices and mark non-saleable items
1. Wines: move menu_price to bottle_price, clear menu_price
2. Mark mixers/syrups as not available_on_menu
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

print("=" * 80)
print("FIXING WINE PRICES & MARKING NON-SALEABLE ITEMS")
print("=" * 80)
print()

# ============================================================================
# PART 1: FIX WINE PRICES
# All wines sell by bottle only, not by glass
# ============================================================================
print("PART 1: Fixing Wine Prices")
print("-" * 80)

wines = StockItem.objects.filter(category_id='W')
wine_fixed = 0

for wine in wines:
    changes = []
    
    # If menu_price has a value but bottle_price doesn't, move it
    if wine.menu_price and wine.menu_price > 0:
        if not wine.bottle_price or wine.bottle_price == 0:
            # Move menu_price to bottle_price
            wine.bottle_price = wine.menu_price
            changes.append(
                f"Moved menu_price €{wine.menu_price} → bottle_price"
            )
        
        # Clear menu_price (wines don't sell by glass in your system)
        wine.menu_price = None
        changes.append("Cleared menu_price (sell by bottle only)")
    
    if changes:
        wine.save()
        print(f"✅ {wine.sku} - {wine.name}")
        for change in changes:
            print(f"   {change}")
        wine_fixed += 1

print(f"\nWines fixed: {wine_fixed}")
print()

# ============================================================================
# PART 2: MARK NON-SALEABLE ITEMS
# Mixers, syrups, ingredients - not sold directly to customers
# ============================================================================
print("PART 2: Marking Non-Saleable Items")
print("-" * 80)

# Keywords for non-saleable items
non_saleable_keywords = [
    'mixer', 'mix', 'syrup', 'monin', 'puree', 'cordial',
    'splash', 'split', 'juice', 'tonic', 'soda',
    'ginger beer', 'lemonade', 'schweppes', 'fever-tree',
    'grenadine', 'agave', 'teisseire', 'volare'
]

# Get all mineral items
minerals = StockItem.objects.filter(category_id='M')
marked_not_saleable = 0
already_marked = 0

print("\nChecking Mineral items (M category):")
for item in minerals:
    name_lower = item.name.lower()
    
    # Check if item name contains non-saleable keywords
    is_non_saleable = any(
        keyword in name_lower for keyword in non_saleable_keywords
    )
    
    if is_non_saleable:
        if item.available_on_menu:
            # Mark as not available on menu
            item.available_on_menu = False
            # Clear menu price
            if item.menu_price:
                old_price = item.menu_price
                item.menu_price = None
                item.save()
                print(
                    f"✅ {item.sku} - {item.name} "
                    f"(was €{old_price}) → Not saleable"
                )
                marked_not_saleable += 1
            else:
                item.save()
                print(f"✅ {item.sku} - {item.name} → Not saleable")
                marked_not_saleable += 1
        else:
            print(f"ℹ️  {item.sku} - {item.name} (already marked)")
            already_marked += 1
    else:
        # This IS saleable (like Red Bull)
        if not item.available_on_menu:
            print(
                f"⚠️  {item.sku} - {item.name} "
                f"(marked not saleable but seems saleable)"
            )

print(f"\nMarked as not saleable: {marked_not_saleable}")
print(f"Already marked: {already_marked}")
print()

# ============================================================================
# PART 3: VERIFICATION REPORT
# ============================================================================
print("=" * 80)
print("VERIFICATION REPORT")
print("=" * 80)

# Check wines
wines_with_menu_price = StockItem.objects.filter(
    category_id='W',
    menu_price__gt=0
).count()
wines_with_bottle_price = StockItem.objects.filter(
    category_id='W',
    bottle_price__gt=0
).count()

print(f"\nWINES (W):")
print(f"  With bottle_price: {wines_with_bottle_price}")
print(f"  With menu_price: {wines_with_menu_price} "
      f"(should be 0 - wines sell by bottle)")

# Check minerals
saleable_minerals = StockItem.objects.filter(
    category_id='M',
    available_on_menu=True
).count()
non_saleable_minerals = StockItem.objects.filter(
    category_id='M',
    available_on_menu=False
).count()

print(f"\nMINERALS (M):")
print(f"  Saleable (available_on_menu=True): {saleable_minerals}")
print(f"  Non-saleable (mixers/syrups): {non_saleable_minerals}")

# Check all saleable items
saleable_items = StockItem.objects.filter(available_on_menu=True)
print(f"\nTOTAL SALEABLE ITEMS: {saleable_items.count()}")
print(f"  Draught (D): {saleable_items.filter(category_id='D').count()}")
print(f"  Bottled (B): {saleable_items.filter(category_id='B').count()}")
print(f"  Spirits (S): {saleable_items.filter(category_id='S').count()}")
print(f"  Wines (W): {saleable_items.filter(category_id='W').count()}")
print(f"  Minerals (M): {saleable_items.filter(category_id='M').count()}")

print()
print("=" * 80)
print("✅ COMPLETE!")
print()
print("KEY POINTS:")
print("  • Wines now sell by BOTTLE ONLY (bottle_price)")
print("  • Mixers/syrups marked as NOT saleable")
print("  • Stock take calculations will only include saleable items")
print("=" * 80)
