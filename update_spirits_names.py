"""
Update all Spirits product names to remove sizes, fix typos, and handle duplicates.
Based on actual stocktake data SKUs.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from stock_tracker.models import StockItem

# All spirits updates - removing sizes, fixing typos, handling duplicates
spirits_updates = [
    # Absolut - Keep flavors
    ("S0006", "Absolut Raspberry"),
    ("S3214", "Absolut Vanilla"),
    
    # Antica
    ("S1019", "Antica Sambuca"),
    
    # Aperol
    ("S0002", "Aperol"),
    
    # Apple Sourz
    ("S1401", "Apple Sourz"),
    
    # Bacardi - Distinguish variations
    ("S0045", "Bacardi White"),  # Was "Bacardi 1ltr"
    ("S29", "Bacardi Gold"),  # Was "Bacardi Oro Gold"
    
    # Baileys
    ("S0074", "Baileys"),  # Was "Baileys 1 litre"
    
    # Beefeater - Fix typo
    ("S2058", "Beefeater 24 Gin"),
    ("S2033", "Beefeater Gin"),  # Was "Beefeeter Gin"
    
    # Belvedere
    ("S2055", "Belvedere Vodka"),
    
    # Benedictine
    ("S0065", "Benedictine"),
    
    # Berthas Revenge
    ("S2148", "Berthas Revenge Gin"),
    
    # Black & White
    ("S1400", "Black and White"),  # Was "Black & White 70cl"
    
    # Black Bush
    ("S0080", "Black Bush"),
    
    # Boatyard
    ("S100", "Boatyard Sloe Gin"),
    
    # Bols - Expand abbreviations
    ("S0215", "Bols Blue Curacao"),
    ("S0162", "Bols Cherry Liqueur"),  # Fix spelling
    ("S1024", "Bols Coconut"),
    ("S0180", "Bols Creme de Cacao Brown"),  # Was "Bols Creme De Cacao B"
    ("S0190", "Bols Creme de Cassis"),
    ("S0195", "Bols Creme de Menthe Green"),  # Was "Bols Creme Menthe G"
    ("S5555", "Bols Peppermint White"),
    ("S0009", "Bols Strawberry"),
    
    # Bombay - Fix typo, add descriptor
    ("S0147", "Bombay Dry"),  # Was "Bombay LTR"
    ("S0100", "Bombay Sapphire"),  # Was "Bombay Saphire 700 ML"
    
    # Buffalo Trace
    ("S2314", "Buffalo Trace"),  # Was "Buffalo Trace 700ml"
    
    # Bulleit
    ("S2065", "Bulleit Bourbon"),  # Was "Bullet Bourbon"
    
    # Bushmills - Your naming
    ("S0105", "Bushmills"),  # Was "Bushmills 10 YO"
    ("S0027", "Bushmills Rum"),  # Was "Bushmills Caribben Rum"
    ("S0120", "Bushmills Red"),  # Was "Bushmills Red 70cl"
    
    # Campari
    ("S0130", "Campari"),  # Was "Campari 70Cl"
    
    # Canadian Club
    ("S0135", "Canadian Club"),
    
    # Captain Morgan
    ("S0140", "Captain Morgan"),  # Was "Captain Morgans LTR"
    
    # Courvoisier
    ("S0150", "Courvoisier"),  # Was "CDC LTR"
    
    # Chambord
    ("S1203", "Chambord"),
    
    # Cointreau
    ("S0170", "Cointreau"),
    
    # Corazon
    ("S0007", "Corazon Tequila Anejo"),
    
    # Crested
    ("S0205", "Crested 10"),
    
    # Dark Rum
    ("S0220", "Dark Rum"),
    
    # Dingle - Spirit type makes unique
    ("S3145", "Dingle Gin"),  # Was "Dingle Gin 70cl"
    ("S2369", "Dingle Single Malt"),
    ("S2034", "Dingle Vodka"),  # Was "Dingle Vodka 70cl"
    ("S_DINGLE_WHISKEY", "Dingle Whiskey"),
    
    # Disaronno
    ("S1587", "Disaronno Amaretto"),
    
    # Drambuie
    ("S0230", "Drambuie"),
    
    # El Jimador
    ("S0026", "El Jimador Blanco"),
    
    # Famous Grouse
    ("S0245", "Famous Grouse"),  # Was "Famous Grouse 70Cl"
    
    # Galliano
    ("S0265", "Galliano"),
    
    # Ghost
    ("S0014", "Ghost Spicy Tequila"),
    
    # Glenfiddich
    ("S0271", "Glenfiddich 12 Year Old"),  # Was "Glenfiddich 12 YO"
    
    # Glenmorangie
    ("S0327", "Glenmorangie"),
    
    # Gordons - Fix typo, simplify zero
    ("S002", "Gordons Pink"),  # Was "Gordans Pink Litre"
    ("S0019", "Gordons Zero"),  # Was "Gordons 0.0% 700ML"
    ("S0306", "Gordons Gin"),  # Was "Gordons Gin LTR"
    
    # Grand Marnier
    ("S0310", "Grand Marnier"),  # Was "Grand Marnier 70Cl"
    
    # Green Spot
    ("S1412", "Green Spot"),
    
    # Grey Goose
    ("S1258", "Grey Goose"),
    
    # Harveys
    ("S0325", "Harveys Bristol Cream"),
    
    # Havana - Your naming
    ("S0029", "Havana"),  # Was "Havana 3YR"
    ("S2156", "Havana Anejo"),  # Was "Havana Anejo"
    ("S2354", "Havana Club"),  # Was "Havana Club 7 YO"
    
    # Hendricks
    ("S1302", "Hendricks Gin"),
    
    # Hennessy
    ("S0335", "Hennessy"),  # Was "Hennessy 1Ltr"
    
    # Irish Mist
    ("S0365", "Irish Mist"),  # Was "Irish Mist 70Cl"
    
    # Jack Daniels
    ("S0380", "Jack Daniels"),
    
    # Jagermeister
    ("S0385", "Jagermeister"),  # Was "Jagermeister 70Cl"
    
    # Jameson - Your naming
    ("S2186", "Jameson Stout"),  # Was "Jamesom Caskmate Stout"
    ("S0405", "Jameson"),  # Was "Jameson 1Ltr"
    ("S0255", "Jameson Black Barrel"),
    ("S2189", "Jameson IPA"),  # Was "Jameson Caskmate IPA"
    
    # Johnnie Walker - Consistent spelling
    ("S0370", "Johnnie Walker Black"),
    ("S1002", "Johnnie Walker Red"),  # Was "Johnny Walker Red"
    
    # Kahlua
    ("S0420", "Kahlua"),
    
    # Ketel One
    ("S1299", "Ketel One"),  # Was "Kettle One"
    
    # Killarney
    ("S0021", "Killarney Whiskey"),
    
    # Kraken
    ("S9987", "Kraken"),  # Was "Krackan"
    
    # Laphroaig
    ("S1101", "Laphroaig 10 Year Old"),
    
    # Luxardo
    ("S1205", "Luxardo Limoncello"),
    
    # Malibu
    ("S0455", "Malibu"),
    
    # Martell
    ("S2155", "Martell VS"),  # Was "Martel VS"
    
    # Martini
    ("S0699", "Martini Dry"),
    ("S0485", "Martini Rosso"),  # Was "Martini Rosso 75Cl"
    
    # Matusalem
    ("S2365", "Matusalem Solera 7 Year"),  # Was "Matusalem Solera 7YO"
    
    # Method & Madness
    ("S2349", "Method and Madness Gin"),
    
    # Midori
    ("S1047", "Midori Green"),
    
    # Muckross
    ("S0064", "Muckross Wild Gin"),
    
    # Paddy
    ("S0530", "Paddy"),
    
    # Passoa
    ("S0041", "Passoa Passionfruit Liqueur"),
    
    # Patron
    ("S24", "Patron Tequila Silver"),
    
    # Peach Schnapps
    ("S0543", "Peach Schnapps"),  # Was "Peach Schnapps 70cl"
    
    # Pernod
    ("S0545", "Pernod"),  # Was "Pernod 70Cl"
    
    # Pimms
    ("S0550", "Pimms No 1"),  # Was "Pimms No.1"
    
    # Port
    ("S0008", "Osborne Port"),  # Was "1827 Osborne Port"
    
    # Powers - Your naming
    ("S0555", "Powers"),  # Was "Powers 1ltr"
    ("S2359", "Powers 3 Swallows"),
    ("S2241", "Powers John Lane"),
    
    # Redbreast - Your naming
    ("S0575", "Redbreast 12"),  # Was "Redbreast 12Yr"
    ("S1210", "Redbreast 15"),  # Was "Redbreast 15 Years Old"
    
    # Remy Martin
    ("S0585", "Remy Martin VSOP"),  # Was "Remy Martin Vsop"
    
    # Ring of Kerry
    ("S0022", "Ring of Kerry Gin"),
    
    # Roe & Co
    ("S2302", "Roe and Co"),
    
    # Sandeman
    ("S0605", "Sandeman Port"),
    
    # Sarti
    ("S0018", "Sarti Rosa Spritz"),
    
    # Sea Dog
    ("S_SEADOG", "Sea Dog Rum"),
    
    # Silver Spear
    ("S2217", "Silver Spear Gin"),
    
    # Skellig
    ("S0001", "Skellig Six18 Pot Still"),  # Was "Skellig Six18Pot Still"
    
    # Smirnoff
    ("S0610", "Smirnoff"),  # Was "Smirnoff 1Ltr"
    
    # Southern Comfort
    ("S0625", "Southern Comfort"),
    
    # Talisker
    ("S0010", "Talisker 10 Year"),  # Was "Talisker 10 YR"
    
    # Tanqueray - Fix typo, simplify zero
    ("S0638", "Tanqueray"),  # Was "Tanquery 70cl"
    ("S0638_00", "Tanqueray Zero"),  # Was "Tanquery 70cl 0.0%"
    
    # Teachers
    ("S0630", "Teachers"),  # Was "Teachers 70Cl"
    
    # Tequila
    ("S2159", "Tequila Bianca"),
    ("S0012", "Tequila Jose Cuervo Gold"),  # Was "Tequila J.C Gold"
    ("S0635", "Tequila Olmeca Gold"),
    ("S1022", "Tequila Rose"),
    
    # Tia Maria
    ("S0640", "Tia Maria"),  # Was "Tia Maria 70Cl"
    
    # Tio Pepe
    ("S0653", "Tio Pepe"),
    
    # Titos
    ("S3147", "Titos Vodka"),  # Was "Tito s Vodka"
    
    # Tullamore Dew
    ("S0647", "Tullamore Dew"),  # Was "Tullamore Dew 70cl"
    
    # Volare
    ("S0023", "Volare Butterscotch"),
    ("S0028", "Volare Limoncello"),  # Was "Volare Limoncello 700ML"
    ("S0017", "Volare Passionfruit"),  # Was "Volare Passionfruit 700ML"
    ("S0005", "Volare Triple Sec"),  # Was "Volare Triple sec"
    
    # West Cork
    ("S2378", "West Cork Irish Whiskey"),
    
    # Winters Tale
    ("S0071", "Winters Tale"),  # Was "Winters Tale 75cl"
    
    # Yellow Spot
    ("S1411", "Yellow Spot"),
]

print("=" * 60)
print("UPDATING ALL SPIRITS NAMES")
print("=" * 60)

success_count = 0
error_count = 0

for sku, new_name in spirits_updates:
    try:
        item = StockItem.objects.get(sku=sku)
        old_name = item.name
        item.name = new_name
        item.save()
        print(f"✓ {sku}: '{old_name}' → '{new_name}'")
        success_count += 1
    except StockItem.DoesNotExist:
        print(f"✗ {sku}: NOT FOUND - {new_name}")
        error_count += 1
    except Exception as e:
        print(f"✗ {sku}: ERROR - {e}")
        error_count += 1

print("\n" + "=" * 60)
print(f"COMPLETE: {success_count} updated, {error_count} errors")
print("=" * 60)
