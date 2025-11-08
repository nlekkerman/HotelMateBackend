"""
CORRECT wine prices from menu images
Wine prices in menu = BOTTLE prices (not glass prices)
Move menu_price to bottle_price for wines
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem
from decimal import Decimal

print("=" * 80)
print("CORRECTING WINE PRICES FROM MENU")
print("=" * 80)
print()

# Wine prices from menu images - these are ALL bottle prices
wine_bottle_prices = [
    # From menu images - BOTTLE column
    ("W0031", 34.00),   # La Chevaliere Chardonnay
    ("W0019", 50.00),   # Chablis Emeraude
    ("W0027", 35.00),   # Equino Malbec
    ("W0025", 55.00),   # Chateau de Domy
    ("W0018", 38.00),   # Chateau Pascaud
    ("W0033", 34.00),   # Les Jamelles Sauvignon Blanc
    ("W0021", 36.00),   # Pazo Albarino
    ("W0038", 38.50),   # Classic South Sauvignon Blanc
    ("W2102", 33.00),   # Les Petites Jamelles Rose
    ("W0032", 36.00),   # La Chevaliere Rose
    ("W2589", 31.00),   # Marques de Plata Sauvignon Blanc
    ("W0039", 31.00),   # Alvier Choro Chardonnay
    ("W1020", 31.00),   # Les Roucas Merlot
    ("W1004", 31.00),   # Marques Temp/Syrah/Cabernet
    ("W2104", 33.00),   # Santa Ana Malbec
    ("W0034", 34.00),   # Roquende Reserve Cabernet
    ("W0023", 36.00),   # El Somo Rioja Crianza
    ("W0029", 38.00),   # Serra di Conte Verdicchio
    ("W0030", 46.00),   # Tenuta Barbera d'Asti
    ("W0028", 50.00),   # Domaine Fleurie Poncie
    ("W0037", 50.00),   # Pouilly Fume Lucy
    ("W1", 35.00),      # Prosecco
]

fixed_count = 0
errors = []

print("Correcting wine prices (menu images show BOTTLE prices):")
print("-" * 80)

for sku, bottle_price in wine_bottle_prices:
    try:
        item = StockItem.objects.filter(sku=sku).first()
        
        if not item:
            errors.append(f"Wine {sku} not found")
            continue
        
        old_menu = item.menu_price
        old_bottle = item.bottle_price
        
        # Set correct bottle price
        item.bottle_price = Decimal(str(bottle_price))
        
        # Clear menu_price (wines don't sell by glass)
        item.menu_price = None
        
        item.save()
        
        print(f"✅ {sku} - {item.name}")
        if old_menu:
            print(f"   Cleared menu_price: €{old_menu}")
        print(f"   Set bottle_price: €{old_bottle or 0} → €{bottle_price}")
        
        fixed_count += 1
        
    except Exception as e:
        errors.append(f"{sku}: {str(e)}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total wines to fix:     {len(wine_bottle_prices)}")
print(f"Successfully fixed:     {fixed_count} ✅")
print(f"Errors:                 {len(errors)} ❌")
print()

if errors:
    print("Errors:")
    for error in errors:
        print(f"  - {error}")
    print()

# Verification
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

wines = StockItem.objects.filter(category_id='W')
wines_with_menu = wines.filter(menu_price__isnull=False, menu_price__gt=0)
wines_with_bottle = wines.filter(
    bottle_price__isnull=False,
    bottle_price__gt=0
)

print(f"\nTotal wines in database: {wines.count()}")
print(f"Wines with bottle_price: {wines_with_bottle.count()} ✅")
print(f"Wines with menu_price: {wines_with_menu.count()} "
      f"(should be 0)")

if wines_with_menu.count() > 0:
    print("\n⚠️ Wines still with menu_price:")
    for wine in wines_with_menu:
        print(f"  {wine.sku} - {wine.name}: €{wine.menu_price}")

print()
print("=" * 80)
print("✅ WINE PRICES CORRECTED!")
print()
print("KEY POINT:")
print("  • All wine prices from menu = BOTTLE prices")
print("  • menu_price cleared (wines don't sell by glass)")
print("  • bottle_price has the correct value")
print("=" * 80)
