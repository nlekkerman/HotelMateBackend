"""
Update ALL selling prices from menu images
IMPORTANT: 
- Draught beer prices are PER PINT (menu_price)
- Bottled beer prices are PER BOTTLE (menu_price)
- Spirits prices are PER SHOT (menu_price)
- Wine prices: bottle_price AND menu_price (glass)
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

# Complete price data from menu images
# Format: (sku, menu_price, bottle_price, glass_price)
menu_prices = [
    # Already in JSON - Spirits (per shot)
    ("S0074", 6.00, None, None),  # Baileys
    ("S3214", 6.10, None, None),  # Absolut Vanilla
    ("S0006", 6.50, None, None),  # Absolut Raspberry - CORRECTED
    ("S2055", 9.90, None, None),  # Belvedere
    ("S2058", 6.40, None, None),  # Beefeater 24 Gin
    ("S2033", 6.10, None, None),  # Beefeater Gin
    ("S2148", 7.50, None, None),  # Bertha's Revenge Gin
    ("S0002", 6.00, None, None),  # Aperol
    ("S0135", 6.00, None, None),  # Campari
    ("S1203", 6.00, None, None),  # Chambord
    ("S0630", 6.10, None, None),  # Teachers
    ("S0245", 6.50, None, None),  # Famous Grouse
    ("S2314", 6.50, None, None),  # Buffalo Trace
    ("S0080", 6.50, None, None),  # Black Bush
    ("S2369", 8.50, None, None),  # Dingle Single Malt
    ("S2034", 7.20, None, None),  # Dingle Vodka
    ("S1587", 6.00, None, None),  # Disaronno
    ("S0100", 6.40, None, None),  # Bombay Sapphire
    ("S0625", 6.20, None, None),  # Southern Comfort
    ("S0610", 6.10, None, None),  # Smirnoff Vodka
    ("S0271", 9.90, None, None),  # Glenfiddich 12 YO
    ("S0010", 9.90, None, None),  # Talisker 10 YO
    
    # Minerals
    ("M0170", 4.90, None, None),  # Red Bull
    ("M0011", 3.60, None, None),  # Three Cents Pink Grapefruit
    
    # Wines (bottle_price, glass_price)
    ("W0031", 8.50, 34.00, 8.50),  # La Chevaliere Chardonnay
    ("W0019", None, 50.00, None),  # Chablis Emeraude
    ("W0027", None, 35.00, None),  # Equino Malbec
    ("W0025", None, 55.00, None),  # Chateau de Domy
    ("W0018", None, 38.00, None),  # Chateau Pascaud
    ("W0033", None, 34.00, None),  # Les Jamelles Sauvignon Blanc
    ("W0021", None, 36.00, None),  # Pazo Albarino
    ("W0038", None, 38.50, None),  # Classic South Sauvignon Blanc
    ("W2102", 9.00, 33.00, 9.00),  # Les Petites Jamelles Rose
    ("W0032", None, 36.00, None),  # La Chevaliere Rose
    
    # Bottled Beer (per bottle)
    ("B0140", 5.70, None, None),  # Heineken
    ("B0095", 5.70, None, None),  # Coors
    ("B0070", 5.70, None, None),  # Budweiser
    ("B0101", 5.80, None, None),  # Corona
    ("B2308", 6.10, None, None),  # Peroni Gluten Free
    ("B0085", 7.40, None, None),  # Bulmers Pint Bottle
    ("B0075", 6.00, None, None),  # Bulmers Long Neck
    ("B1036", 6.00, None, None),  # Cronins Cider
    ("B1006", 7.40, None, None),  # Kopparberg
    ("B0235", 7.50, None, None),  # West Coast Cooler
    ("B2036", 7.50, None, None),  # West Coast Cooler Rose
    ("B0205", 6.70, None, None),  # Smirnoff Ice
    ("B0254", 6.70, None, None),  # WKD Blue
    ("B2055", 5.50, None, None),  # Heineken 0.0
    ("B0012", 6.20, None, None),  # Cronins 0.0
    ("B1022", 5.90, None, None),  # Erdinger 0.0
    
    # Draught Beer (per PINT)
    ("D0030", 6.30, None, None),  # Heineken Pint
    ("D1258", 6.30, None, None),  # Coors Pint
    ("D2354", 6.30, None, None),  # Moretti Pint
    ("D1022", 6.40, None, None),  # Orchard Thieves Pint
    ("D0006", 6.40, None, None),  # Orchard Thieves Orange Pint
    ("D1003", 6.40, None, None),  # Murphy's Pint
    ("D0007", 6.30, None, None),  # Beamish Pint
    ("D0005", 6.30, None, None),  # Guinness Pint
    ("D0012", 5.90, None, None),  # Killarney Blonde Ale Pint
    
    # Additional items from menu images NOT in JSON
    # Irish Whiskey
    ("S0205", 6.00, None, None),  # Crested Ten
    ("S2186", 8.10, None, None),  # Jameson Caskmates Stout
    ("S2189", 8.10, None, None),  # Jameson Caskmates IPA
    ("S0255", 9.80, None, None),  # Jameson Black Barrel
    ("S2302", 7.20, None, None),  # Roe & Coe
    ("S1412", 9.90, None, None),  # Green Spot
    ("S1411", 12.70, None, None),  # Yellow Spot
    ("S2241", 12.90, None, None),  # Powers John Lane
    ("S0575", 12.10, None, None),  # Redbreast 12YO
    ("S1210", 18.90, None, None),  # Redbreast 15YO
    
    # American Whiskey
    ("S0380", 6.20, None, None),  # Jack Daniels
    
    # Scottish Whiskey
    ("S1002", 7.00, None, None),  # Johnnie Walker Red
    ("S0370", 8.00, None, None),  # Johnnie Walker Black
    ("S0327", 9.90, None, None),  # Glenmorangie 10YO
    ("S1101", 10.50, None, None),  # Laphroaig 10YO
    
    # Rum
    ("S0045", 6.10, None, None),  # Bacardi
    ("S0455", 6.10, None, None),  # Malibu
    ("S0140", 6.10, None, None),  # Captain Morgan
    ("S0029", 6.30, None, None),  # Havana 3YR / Havana Club Anejo
    ("S2354", 7.00, None, None),  # Havana Club 7YO
    ("S9987", 7.30, None, None),  # Kraken Rum
    ("S29", 7.50, None, None),  # Bacardi Oro Gold
    
    # Tequila
    ("S0635", 6.10, None, None),  # Olmeca Reposado
    ("S0007", 7.20, None, None),  # Corazon Anejo Tequila
    ("S24", 11.20, None, None),  # Patron Silver
    
    # Liqueurs
    ("S0420", 6.00, None, None),  # Kahlua
    ("S0365", 6.00, None, None),  # Irish Mist
    ("S0640", 6.00, None, None),  # Tia Maria
    ("S0310", 6.00, None, None),  # Grand Marnier
    ("S0170", 6.00, None, None),  # Cointreau
    ("S0065", 6.00, None, None),  # Benedictine
    ("S0195", 6.00, None, None),  # Creme de Menthe
    
    # Vodka
    ("S1258", 9.10, None, None),  # Grey Goose
    
    # Brandy/Port/Sherry
    ("S0335", 6.90, None, None),  # Hennessy VS
    ("S0585", 9.80, None, None),  # Remi Martin VSOP
    ("S0325", 8.50, None, None),  # Harvey's Bristol Cream
    ("S0071", 6.20, None, None),  # Winters Tale
    ("S0653", 6.00, None, None),  # Tio Pepe
    ("S0605", 5.80, None, None),  # Sandeman Port
    
    # Gin
    ("S3145", 7.40, None, None),  # Dingle Gin
    ("S0064", 7.90, None, None),  # Muckross Gin
    ("S0022", 7.90, None, None),  # Ring of Kerry Gin
    ("S0306", 6.10, None, None),  # Gordons Gin
    ("S0638", 6.40, None, None),  # Tanqueray Gin
    ("S2349", 8.60, None, None),  # Method & Madness
    ("S0147", 6.90, None, None),  # Bombay Sapphire (Ltr)
    
    # Aperitifs
    ("S0699", 6.00, None, None),  # Dry Martini
    
    # After Dinner
    ("S0385", 6.00, None, None),  # Jagermeister
    ("S1019", 6.00, None, None),  # Sambuca
    ("S1205", 6.00, None, None),  # Limoncello
    
    # Draught Beer - Additional
    ("D0011", 6.80, None, None),  # Lagunitas IPA
    
    # Wines - Additional from menu
    ("W2589", 8.50, 31.00, 8.50),  # Marques de Plata Sauvignon
    ("W0039", 8.50, 31.00, 8.50),  # Alvier Choro Chardonnay
    ("W1020", 8.50, 31.00, 8.50),  # Les Roucas Merlot
    ("W1004", 8.50, 31.00, 8.50),  # Marques Temp/Syrah/Cabernet
    ("W2104", 9.00, 33.00, 9.00),  # Santa Ana Malbec
    ("W0034", None, 34.00, None),  # Roquende Reserve Cabernet
    ("W0023", None, 36.00, None),  # El Somo Rioja Crianza
    ("W0029", None, 38.00, None),  # Serra di Conte Verdicchio
    ("W0030", None, 46.00, None),  # Tenuta Barbera d'Asti
    ("W0028", None, 50.00, None),  # Domaine Fleurie Poncie
    ("W0037", None, 50.00, None),  # Pouilly Fume Lucy
    ("W1", None, 35.00, None),  # Prosecco
]

print("=" * 80)
print("UPDATING ALL SELLING PRICES FROM MENU")
print("=" * 80)
print()

updated_count = 0
not_found = []
errors = []

for price_data in menu_prices:
    sku = price_data[0]
    menu_price = price_data[1]
    bottle_price = price_data[2]
    glass_price = price_data[3]
    
    try:
        item = StockItem.objects.filter(sku=sku).first()
        
        if not item:
            not_found.append(sku)
            continue
        
        updates = []
        
        # Update menu_price (pint/shot/bottle/glass)
        if menu_price is not None:
            old_menu = item.menu_price
            item.menu_price = Decimal(str(menu_price))
            updates.append(f"menu_price: Ôé¼{old_menu or 0} ÔåÆ Ôé¼{menu_price}")
        
        # Update bottle_price (for wines)
        if bottle_price is not None:
            old_bottle = item.bottle_price
            item.bottle_price = Decimal(str(bottle_price))
            updates.append(
                f"bottle_price: Ôé¼{old_bottle or 0} ÔåÆ Ôé¼{bottle_price}"
            )
        
        if updates:
            item.save()
            category = item.category_id
            cat_name = {
                'D': 'Draught (Pint)',
                'B': 'Bottle',
                'S': 'Spirit (Shot)',
                'W': 'Wine',
                'M': 'Mineral'
            }.get(category, category)
            
            print(f"Ô£à [{cat_name}] {sku} - {item.name}")
            for update in updates:
                print(f"   {update}")
            updated_count += 1
    
    except Exception as e:
        errors.append(f"{sku}: {str(e)}")
        print(f"ÔØî Error with {sku}: {str(e)}")

print()
print("=" * 80)
print("UPDATE SUMMARY")
print("=" * 80)
print(f"Total items to update:      {len(menu_prices)}")
print(f"Successfully updated:       {updated_count} Ô£à")
print(f"Not found in database:      {len(not_found)} ÔÜá´©Å")
print(f"Errors:                     {len(errors)} ÔØî")
print()

if not_found:
    print("ÔÜá´©Å  SKUs not found in database:")
    for sku in not_found:
        print(f"  - {sku}")
    print()

if errors:
    print("ÔØî Errors:")
    for error in errors:
        print(f"  - {error}")
    print()

print("­ƒÄë All menu prices have been updated!")
print()
print("KEY POINTS:")
print("  ÔÇó Draught beer prices = PER PINT")
print("  ÔÇó Bottled beer prices = PER BOTTLE")
print("  ÔÇó Spirit prices = PER SHOT (25ml/35ml)")
print("  ÔÇó Wine: bottle_price + menu_price (glass)")
print("=" * 80)
