"""
1. Mark mixers/syrups as not saleable
2. Add missing prices from menu image
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from django.db import models
from decimal import Decimal

print("=" * 80)
print("FIXING MIXERS & ADDING MISSING PRICES")
print("=" * 80)
print()

# =========================================================================
# PART 1: Mark mixers/syrups as NOT saleable (available_on_menu=False)
# =========================================================================
print("PART 1: Marking Mixers/Syrups as Not Saleable")
print("-" * 80)

mixer_keywords = [
    'monin', 'syrup', 'puree', 'mixer', 'juice', 'cordial',
    'splash', 'grenadine', 'agave', 'teisseire', 'volare',
    'split', 'lemonade', 'tonic', 'schweppes', 'fever',
    'riverrock', 'miwadi', 'kulana', 'britvic'
]

minerals = StockItem.objects.filter(category_id='M')
marked_count = 0

for item in minerals:
    name_lower = item.name.lower()
    
    # Check if it's a mixer/syrup
    is_mixer = any(keyword in name_lower for keyword in mixer_keywords)
    
    # Keep Red Bull and similar saleable items
    saleable_items = ['red bull', 'three cents']
    is_saleable = any(s in name_lower for s in saleable_items)
    
    if is_mixer and not is_saleable:
        if item.available_on_menu:
            item.available_on_menu = False
            item.menu_price = None
            item.save()
            print(f"✅ {item.sku} - {item.name} → Not saleable")
            marked_count += 1

print(f"\nMarked {marked_count} mixers/syrups as not saleable")
print()

# =========================================================================
# PART 2: Mark cocktail mixers in spirits as NOT saleable
# =========================================================================
print("PART 2: Marking Cocktail Mixers (Spirits) as Not Saleable")
print("-" * 80)

# These are spirits used only for cocktail making, not sold individually
cocktail_mixer_keywords = [
    'bols', 'volare', 'triple sec', 'schnapps', 'curacao', 
    'creme de', 'grenadine', 'blue curacao'
]

spirits = StockItem.objects.filter(category_id='S')
spirit_mixer_count = 0

for item in spirits:
    name_lower = item.name.lower()
    
    # Check if it's a cocktail mixer
    is_cocktail_mixer = any(keyword in name_lower for keyword in cocktail_mixer_keywords)
    
    if is_cocktail_mixer:
        if item.available_on_menu:
            item.available_on_menu = False
            item.menu_price = None
            item.save()
            print(f"✅ {item.sku} - {item.name} → Not saleable (cocktail mixer)")
            spirit_mixer_count += 1

print(f"\nMarked {spirit_mixer_count} spirit cocktail mixers as not saleable")
print()

# =========================================================================
# PART 3: Add missing prices from menu image
# =========================================================================
print("PART 3: Adding Missing Prices from Menu")
print("-" * 80)

# Prices from the new menu image
missing_prices = [
    # Draught Beer (per pint)
    ("D0004", 6.30, "30 Heineken - same as 50 Heineken"),
    ("D1004", 6.30, "30 Coors - same as 50 Coors"),
    ("D0008", 5.90, "Murphy's Ale - shown as €5.90"),
    ("D2133", 5.60, "Heineken 0.0 Pint - shown as €5.60"),
    
    # Wines (bottle prices)
    ("W0022", 29.00, "Rioja Crianza - bottle price"),
    ("W0024", 29.00, "Malbec Catena - bottle price"),
    ("W45", 29.00, "Standard wine bottle price"),
]

added_count = 0
not_found = []

for sku, price, note in missing_prices:
    try:
        item = StockItem.objects.filter(sku=sku).first()
        
        if not item:
            not_found.append(sku)
            continue
        
        # Handle wines vs other categories
        if item.category_id == 'W':
            old_price = item.bottle_price
            item.bottle_price = Decimal(str(price))
            item.save()
            print(f"✅ {sku} - {item.name}")
            print(f"   bottle_price: €{old_price or 0} → €{price}")
        else:
            old_price = item.menu_price
            item.menu_price = Decimal(str(price))
            item.save()
            print(f"✅ {sku} - {item.name}")
            print(f"   menu_price: €{old_price or 0} → €{price}")
        
        print(f"   Note: {note}")
        print()
        added_count += 1
        
    except Exception as e:
        print(f"❌ Error with {sku}: {str(e)}")

print(f"Added prices for {added_count} items")
print()

if not_found:
    print("⚠️ SKUs not found:")
    for sku in not_found:
        print(f"  - {sku}")
    print()

# =========================================================================
# PART 3: Summary Report
# =========================================================================
print("=" * 80)
print("SUMMARY REPORT")
print("=" * 80)

# Count saleable items
saleable = StockItem.objects.filter(available_on_menu=True)
non_saleable = StockItem.objects.filter(available_on_menu=False)

print(f"\nTotal items: {StockItem.objects.count()}")
print(f"Saleable items: {saleable.count()}")
print(f"Non-saleable items: {non_saleable.count()}")
print()

# Items still without prices
print("Items still missing prices:")
print("-" * 80)

# Draught
d_no_price = saleable.filter(category_id='D').filter(
    models.Q(menu_price__isnull=True) | models.Q(menu_price=0)
).count()

# Bottled
b_no_price = saleable.filter(category_id='B').filter(
    models.Q(menu_price__isnull=True) | models.Q(menu_price=0)
).count()

# Spirits
s_no_price = saleable.filter(category_id='S').filter(
    models.Q(menu_price__isnull=True) | models.Q(menu_price=0)
).count()

# Wines
w_no_price = saleable.filter(category_id='W').filter(
    models.Q(bottle_price__isnull=True) | models.Q(bottle_price=0)
).count()

# Minerals (saleable only)
m_no_price = saleable.filter(category_id='M').filter(
    models.Q(menu_price__isnull=True) | models.Q(menu_price=0)
).count()

print(f"Draught Beer (D): {d_no_price}")
print(f"Bottled Beer (B): {b_no_price}")
print(f"Spirits (S): {s_no_price}")
print(f"Wines (W): {w_no_price}")
print(f"Minerals (M): {m_no_price}")
print()

total_missing = d_no_price + b_no_price + s_no_price + w_no_price + m_no_price
print(f"Total saleable items without prices: {total_missing}")

print()
print("=" * 80)
print("✅ COMPLETE!")
print()
print("KEY ACTIONS:")
print(f"  • {marked_count} mixers/syrups marked as NOT saleable")
print(f"  • {spirit_mixer_count} spirit cocktail mixers marked as NOT saleable")
print(f"  • {added_count} missing prices added (draught beers + wines)")
print("  • Stock take will now only calculate saleable items")
print("=" * 80)
