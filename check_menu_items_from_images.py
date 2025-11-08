"""
Check menu items from images against database
Extracted from physical menu photos
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# Comprehensive menu data extracted from images
menu_items = [
    # IRISH WHISKEY SELECTION
    {"name": "Dingle Single Malt", "price": 8.50, "type": "S"},
    {"name": "Jameson/Powers/Paddy", "price": 6.00, "type": "S"},
    {"name": "Crested Ten", "price": 6.00, "type": "S"},
    {"name": "Bushmills", "price": 6.00, "type": "S"},
    {"name": "West Cork", "price": 6.00, "type": "S"},
    {"name": "Blackmills Black Bush", "price": 6.50, "type": "S"},
    {"name": "Jameson Caskmates Stout", "price": 8.10, "type": "S"},
    {"name": "Killarney Whiskey", "price": 7.20, "type": "S"},
    {"name": "Jameson Caskmates IPA", "price": 8.10, "type": "S"},
    {"name": "Jameson Black Barrel", "price": 9.80, "type": "S"},
    {"name": "Roe & Coe", "price": 7.20, "type": "S"},
    {"name": "Green Spot", "price": 9.90, "type": "S"},
    {"name": "Yellow Spot", "price": 12.70, "type": "S"},
    {"name": "Powers John Lane Release", "price": 12.90, "type": "S"},
    {"name": "Redbreast 12YO", "price": 12.10, "type": "S"},
    {"name": "Redbreast 15YO", "price": 18.90, "type": "S"},
    {"name": "Middleton Rare", "price": 38.50, "type": "S"},
    
    # AMERICAN WHISKEY
    {"name": "Canadian Club", "price": 6.20, "type": "S"},
    {"name": "Jack Daniels", "price": 6.20, "type": "S"},
    {"name": "Southern Comfort", "price": 6.20, "type": "S"},
    {"name": "Buffalo Trace", "price": 6.50, "type": "S"},
    {"name": "Bulleit Bourbon", "price": 6.70, "type": "S"},
    
    # SCOTTISH WHISKEY
    {"name": "Teachers", "price": 6.10, "type": "S"},
    {"name": "Famous Grouse", "price": 6.50, "type": "S"},
    {"name": "Johnnie Walker Red", "price": 7.00, "type": "S"},
    {"name": "Johnnie Walker Black", "price": 8.00, "type": "S"},
    {"name": "Glenfiddich Single Malt", "price": 9.00, "type": "S"},
    {"name": "Talisker 10YO", "price": 9.50, "type": "S"},
    {"name": "Glenmorangie 10YO", "price": 9.90, "type": "S"},
    {"name": "Laphroaig 10YO", "price": 10.50, "type": "S"},
    
    # HOT ALCOHOLIC DRINKS
    {"name": "Hot Whiskey", "price": 7.20, "type": "S"},
    {"name": "Hot Brandy", "price": 7.90, "type": "S"},
    {"name": "Hot Port", "price": 7.10, "type": "S"},
    {"name": "Irish Coffee", "price": 7.90, "type": "S"},
    {"name": "Baileys Coffee", "price": 7.80, "type": "S"},
    {"name": "Calypso Coffee", "price": 7.80, "type": "S"},
    {"name": "French Coffee", "price": 8.00, "type": "S"},
    {"name": "Kahlua Coffee", "price": 7.80, "type": "S"},
    
    # RUM SELECTION
    {"name": "Bacardi", "price": 6.10, "type": "S"},
    {"name": "Malibu", "price": 6.10, "type": "S"},
    {"name": "Captain Morgan", "price": 6.10, "type": "S"},
    {"name": "Sadog Dark Rum", "price": 6.30, "type": "S"},
    {"name": "Havana Club Anejo", "price": 6.30, "type": "S"},
    {"name": "Havana Club 7YO", "price": 7.00, "type": "S"},
    {"name": "The Kraken Rum", "price": 7.30, "type": "S"},
    {"name": "Bacardi Oro Gold", "price": 7.50, "type": "S"},
    
    # TEQUILA SELECTION
    {"name": "Olmeca Reposado", "price": 6.10, "type": "S"},
    {"name": "Corazon Anejo Tequila", "price": 7.20, "type": "S"},
    {"name": "Patron Silver", "price": 11.20, "type": "S"},
    
    # LIQUEURS
    {"name": "Baileys", "price": 6.00, "type": "S"},
    {"name": "Kahlua", "price": 6.00, "type": "S"},
    {"name": "Irish Mist", "price": 6.00, "type": "S"},
    {"name": "Tia Maria", "price": 6.00, "type": "S"},
    {"name": "Grand Marnier", "price": 6.00, "type": "S"},
    {"name": "Cointreau", "price": 6.00, "type": "S"},
    {"name": "Benedictine", "price": 6.00, "type": "S"},
    {"name": "Creme de Menthe", "price": 6.00, "type": "S"},
    {"name": "Disaronno", "price": 6.00, "type": "S"},
    {"name": "Chambord", "price": 6.00, "type": "S"},
    
    # VODKA SELECTION
    {"name": "Dingle Vodka", "price": 7.20, "type": "S"},
    {"name": "Smirnoff Vodka", "price": 6.10, "type": "S"},
    {"name": "Absolut Vanilla", "price": 6.10, "type": "S"},
    {"name": "Absolut Raspberry", "price": 6.10, "type": "S"},
    {"name": "Ketel One", "price": 8.60, "type": "S"},
    {"name": "Tito's Handmade Vodka", "price": 8.80, "type": "S"},
    {"name": "Grey Goose", "price": 9.10, "type": "S"},
    {"name": "Belvedere", "price": 9.90, "type": "S"},
    
    # BRANDY PORT SHERRY
    {"name": "Hennessy VS", "price": 6.90, "type": "S"},
    {"name": "Maartel VS", "price": 6.90, "type": "S"},
    {"name": "Remi Martin VSOP", "price": 9.80, "type": "S"},
    {"name": "Brandy and Port", "price": 7.80, "type": "S"},
    
    # GIN SELECTION
    {"name": "Dingle Gin", "price": 7.40, "type": "S"},
    {"name": "Muckross Gin", "price": 7.90, "type": "S"},
    {"name": "Ring of Kerry Gin", "price": 7.90, "type": "S"},
    {"name": "Gordon's", "price": 6.10, "type": "S"},
    {"name": "Tanqueray Gin", "price": 6.40, "type": "S"},
    {"name": "Beefeater 24 Gin", "price": 7.90, "type": "S"},
    {"name": "Hendrick's Gin", "price": 8.00, "type": "S"},
    {"name": "Method & Madness", "price": 8.60, "type": "S"},
    {"name": "Cork Dry Gin", "price": 6.10, "type": "S"},
    {"name": "Bombay Sapphire", "price": 6.90, "type": "S"},
    {"name": "Skellig Star Gin", "price": 7.90, "type": "S"},
    
    # SHERRY
    {"name": "Harvey's Bristol Cream", "price": 8.50, "type": "S"},
    {"name": "Winters Tale", "price": 6.20, "type": "S"},
    {"name": "Tio Pepe", "price": 6.00, "type": "S"},
    {"name": "Sandeman Port", "price": 5.80, "type": "S"},
    
    # APERITIFS
    {"name": "Dry Martini", "price": 6.00, "type": "S"},
    {"name": "Sweet Martini", "price": 6.00, "type": "S"},
    {"name": "Aperol", "price": 6.00, "type": "S"},
    {"name": "Campari", "price": 6.00, "type": "S"},
    
    # AFTER DINNER DIGESTIF
    {"name": "Creme de Menthe", "price": 6.00, "type": "S"},
    {"name": "Jagermeister", "price": 6.00, "type": "S"},
    {"name": "Sambuca", "price": 6.00, "type": "S"},
    {"name": "Limoncello", "price": 6.00, "type": "S"},
    {"name": "Pedro Ximenze", "price": 7.50, "type": "S"},
    
    # DRAUGHT BEER
    {"name": "Heineken", "price": 6.30, "type": "D"},
    {"name": "Coors Light", "price": 6.30, "type": "D"},
    {"name": "Moretti", "price": 6.30, "type": "D"},
    {"name": "Orchard Thieves", "price": 6.80, "type": "D"},
    {"name": "Orchard Thieves Orange", "price": 6.40, "type": "D"},
    {"name": "Murphy's", "price": 6.40, "type": "D"},
    {"name": "Murphy's Ale", "price": 5.90, "type": "D"},
    {"name": "Beamish", "price": 6.30, "type": "D"},
    {"name": "Guinness", "price": 5.90, "type": "D"},
    {"name": "Killarney Blonde Ale", "price": 5.90, "type": "D"},
    {"name": "Lagunitas IPA", "price": 6.80, "type": "D"},
    
    # BOTTLE BEER
    {"name": "Heineken", "price": 5.70, "type": "B"},
    {"name": "Coors", "price": 5.70, "type": "B"},
    {"name": "Budweiser", "price": 5.70, "type": "B"},
    {"name": "Corona", "price": 5.80, "type": "B"},
    {"name": "Peroni Gluten Free", "price": 6.10, "type": "B"},
    {"name": "Bulmers Original Long Neck", "price": 6.00, "type": "B"},
    {"name": "Bulmers Original Pint Bottle", "price": 7.40, "type": "B"},
    {"name": "Cronins", "price": 6.70, "type": "B"},
    {"name": "Kopparberg Strawberry & Lime", "price": 7.40, "type": "B"},
    {"name": "West Coast Cooler Original or Rose", "price": 7.50, "type": "B"},
    {"name": "Smirnoff Ice", "price": 6.70, "type": "B"},
    {"name": "WKD Blue", "price": 6.70, "type": "B"},
    
    # NON-ALCOHOL
    {"name": "Heineken 0.0 Pint", "price": 5.60, "type": "D"},
    {"name": "Heineken 0.0 Glass", "price": 3.20, "type": "D"},
    {"name": "Heineken 0.0 Bottle", "price": 5.90, "type": "B"},
    {"name": "Cronins Cider 0.0 Bottle", "price": 6.20, "type": "B"},
    {"name": "Erdinger 0.0", "price": 5.90, "type": "B"},
    
    # WHITE WINE
    {"name": "Marques de Plata Sauvignon Blanc", "bottle": 31.00, "glass": 8.50, "type": "W"},
    {"name": "Sonetti Pinot Grigio", "bottle": 31.00, "glass": 8.50, "type": "W"},
    {"name": "Alvier Choro Chardonnay", "bottle": 31.00, "glass": 8.50, "type": "W"},
    {"name": "Les Jamelles Sauvignon Blanc", "bottle": 34.00, "type": "W"},
    {"name": "La Chevaliere Chardonnay", "bottle": 34.00, "type": "W"},
    {"name": "Classic South Nelson Sauvignon Blanc", "bottle": 38.50, "type": "W"},
    {"name": "Pazo Cilleiro Albarino", "bottle": 36.00, "type": "W"},
    {"name": "Serra di Conte Verdicchio", "bottle": 38.00, "type": "W"},
    {"name": "Moillard Grivot Macon Villages", "bottle": 45.00, "type": "W"},
    {"name": "Pouilly Fume Lucy", "bottle": 50.00, "type": "W"},
    {"name": "Chablis Emeraude", "bottle": 54.00, "type": "W"},
    
    # ROSE WINE
    {"name": "Les Petites Jamelles Grenache Carignan", "bottle": 33.00, "glass": 9.00, "type": "W"},
    {"name": "La Chevaliere Rose", "bottle": 36.00, "type": "W"},
    
    # RED WINE
    {"name": "Marques de Plata Tempranillo Syrah Cabernet", "bottle": 31.00, "glass": 8.50, "type": "W"},
    {"name": "Les Roucas Merlot", "bottle": 31.00, "glass": 8.50, "type": "W"},
    {"name": "Santa Ana Malbec", "bottle": 33.00, "glass": 9.00, "type": "W"},
    {"name": "Roquende Reserve Cabernet Sauvignon", "bottle": 34.00, "type": "W"},
    {"name": "Equino Malbec", "bottle": 35.00, "type": "W"},
    {"name": "El Somo Rioja Crianza", "bottle": 36.00, "type": "W"},
    {"name": "Chateau Pascaud", "bottle": 38.00, "type": "W"},
    {"name": "Plantamura Primitivo Giola del Colle", "bottle": 42.00, "type": "W"},
    {"name": "Tenuta Garetto Barbera d'Asti", "bottle": 46.00, "type": "W"},
    {"name": "Domaine du Vissoux Chermette Fleurie Poncie", "bottle": 50.00, "type": "W"},
    {"name": "Chateau de Domy", "bottle": 55.00, "type": "W"},
    
    # SPARKLING WINE
    {"name": "Snipe of Prosecco", "bottle": 11.50, "type": "W"},
    {"name": "Prosecco", "bottle": 35.00, "type": "W"},
    {"name": "La Chevaliere", "bottle": 78.00, "type": "W"},
]

print("=" * 80)
print("MENU ITEMS FROM IMAGES - DATABASE CHECK")
print("=" * 80)
print()

found_in_db = []
not_found_in_db = []
partial_matches = []

for menu_item in menu_items:
    name = menu_item['name']
    item_type = menu_item.get('type', '')
    
    # Try exact name match
    db_items = StockItem.objects.filter(name__iexact=name)
    
    if db_items.exists():
        found_in_db.append({
            'name': name,
            'type': item_type,
            'db_match': db_items.first().sku,
            'menu_price': menu_item.get('price') or menu_item.get('bottle')
        })
    else:
        # Try partial match (contains)
        partial = StockItem.objects.filter(name__icontains=name.split()[0])
        
        if partial.exists():
            partial_matches.append({
                'menu_name': name,
                'type': item_type,
                'possible_matches': [
                    f"{item.sku} - {item.name}" 
                    for item in partial[:3]
                ],
                'menu_price': menu_item.get('price') or menu_item.get('bottle')
            })
        else:
            not_found_in_db.append({
                'name': name,
                'type': item_type,
                'menu_price': menu_item.get('price') or menu_item.get('bottle')
            })

print(f"📊 SUMMARY")
print(f"-" * 80)
print(f"Total items on menu:          {len(menu_items)}")
print(f"Found exact matches in DB:    {len(found_in_db)} ✅")
print(f"Partial matches found:        {len(partial_matches)} ⚠️")
print(f"Not found in DB:              {len(not_found_in_db)} ❌")
print()

if not_found_in_db:
    print("=" * 80)
    print("❌ ITEMS ON MENU BUT NOT IN DATABASE")
    print("=" * 80)
    for item in not_found_in_db:
        price = f"€{item['menu_price']}" if item['menu_price'] else "N/A"
        print(f"  [{item['type']}] {item['name']} - {price}")

if partial_matches:
    print("\n" + "=" * 80)
    print("⚠️  ITEMS WITH PARTIAL MATCHES (may need review)")
    print("=" * 80)
    for item in partial_matches:
        price = f"€{item['menu_price']}" if item['menu_price'] else "N/A"
        print(f"\n  Menu: {item['menu_name']} [{item['type']}] - {price}")
        print(f"  Possible DB matches:")
        for match in item['possible_matches']:
            print(f"    - {match}")

if found_in_db:
    print("\n" + "=" * 80)
    print(f"✅ EXACT MATCHES FOUND ({len(found_in_db)} items)")
    print("=" * 80)
    for item in found_in_db[:20]:
        price = f"€{item['menu_price']}" if item['menu_price'] else "N/A"
        print(f"  {item['db_match']} - {item['name']} - {price}")
    if len(found_in_db) > 20:
        print(f"  ... and {len(found_in_db) - 20} more")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)
