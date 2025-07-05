
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")

import django
django.setup()

from stock_tracker.models import StockCategory, StockItem, StockItemType
from hotel.models import Hotel
from django.utils.text import slugify


def generate_sku(prefix, index):
    return f"{prefix}-{str(index).zfill(3)}"  # e.g., SPI-001


def upload_stock_items(hotel_id=2):
    hotel = Hotel.objects.get(id=hotel_id)

    # 🏷️ Create a single StockCategory (e.g., Bar Stock)
    stock_category, _ = StockCategory.objects.get_or_create(
        hotel=hotel,
        name="Bar Stock",
        defaults={"slug": slugify("Bar Stock")}
    )

    # 📦 Define item types and their items
    category_items = {
        "Spirits": sorted([
            "Dingle Vodka", "Smirnoff", "Absolut Flavour Vod", "Ketel One", "Titos Vodka",
            "Grey Goose", "Belvedere", "Smirnoff Infusion",
            "Dingle Gin", "Muckross Gin", "Gordons Gin", "Tanqueray Gin", "Beefeater 24",
            "Hendricks Gin", "Method & Madness", "CDC Gin", "Bombay Gin", "Gunpowder",
            "Beefeater Pink", "Berthas Revenge", "Gin Special !", "Skellig Six18",
            "Silver Spear Gin", "Glendalough", "Monkey 47",
            "Bacardi", "Malibu", "Captain Morgan", "Old Jamaican Rum", "Havana Anejo Club",
            "Havana 7yr", "Kraken", "Bacardi Gold", "Black of Kinsale", "Ring of Kerry",
            "Martini Dry", "Martini Red", "Campari", "Pernod", "Pimms",
            "Bristol Cream", "Sandeman Port"
        ]),
        "Liqueurs": sorted([
            "Advocaat", "Amaretto", "Benedictine", "Blackhause", "Blue Curacao",
            "Cherry Brandy", "Cointreau", "Creme de Menthe", "Disaronno", "Drambuie",
            "Galliano", "Grand Marnier", "Irish Mist", "Pedro X", "Rumple Minz",
            "Tequila Gold", "Triple Sec", "Aftershock", "Baileys", "Butterscotch",
            "Creme de Banane", "Creme de Cacao", "Creme de Cassis", "Kahlua",
            "Limoncello", "Tia Maria"
        ]),
        "Whiskey": sorted([
            "Black & White", "Black Bush", "Buffalo Trace", "Canadian Club", "Crested Ten",
            "Dingle Whiskey", "Famous Grouse", "Glenmorangie 10 Year Old", "Green Spot",
            "Jack Daniels", "Jameson", "Jameson Black Barrel", "Jameson Cask IPA",
            "Jameson Caskmates Stout", "JW Red", "Killamey Whiskey", "Midleton Vintage Release",
            "Paddy", "Powers", "Powers 3 Swallow", "Powers Johns Lane", "Red Breast 12 yr Old",
            "Red Breast 15YR", "Red Bush", "Roe & Coe", "Southern Comfort", "Teachers",
            "West Cork Black", "West Cork Burbon", "Wild Turkey", "Yellow Spot"
        ]),
        "Red Wines": sorted([
            "BT Chateau de Dommy", "Bt Chateau Pascaud", "Bt Domaine du Vissoux",
            "Bt El Somo Rioja", "Bt Equino Malbec", "Bt Marques Cabernet",
            "Bt Plantamura Primitivo", "Bt Roquende Cab", "Bt Roucas Merlot",
            "Bt Santa Ana Malbec", "Bt Tenuta Garetti"
        ]),
        "White Wines": sorted([
            "Bt Alvier Chard", "Bt Chablis Emeraude", "Bt Cheval Imperial",
            "Bt Chevaliere Chardonnay", "Bt Classic Nelson Blanc", "Bt Les Jamelles Sauv B",
            "Bt Marques Sauv Blanc", "Bt Moillard Macon Villages", "Bt Pazo Albarino",
            "Bt Pouilly Fume", "Bt Sonetti Pinot", "Bt Verdicchio"
        ]),
        "Rosé & Sparkling": sorted([
            "1/4 Bt Prosecco", "BT Les Petits J Rose", "Bottle Perrisecco",
            "Bt Killamey B", "Bt La Chevaliere Rose", "Btl Prosecco"
        ]),
        "Beers": sorted([
            "BT Peroni GF", "Btl Bud", "Btl Bulmers", "Btl Bulmers LIGHT", "Btl Corona",
            "Btl Heineken", "Btl Smifwicks", "Cronins 0.0", "Kopparberg S/L", "LN Bulmers",
            "Smirnoff Ice", "West Coast Cooler", "WKD"
        ]),
        "Minerals": sorted([
            "Coke", "Cranberry Juice", "Diet Coke", "Elderflower Tonic", "Fanta Orange",
            "Feever Tonic", "Ginger Ale", "Orange Juice", "Pineapple Juice", "Slimline Tonic",
            "Soda Water", "Sprite Zero", "Tonic Water"
        ])
    }

    count = 0
    for type_name, item_list in category_items.items():
        type_slug = slugify(type_name)

        # Get or create the type
        item_type, _ = StockItemType.objects.get_or_create(
            name=type_name,
            defaults={"slug": type_slug}
        )

        prefix = ''.join([c for c in type_name if c.isalnum()])[:3].upper()

        for idx, item_name in enumerate(item_list, start=1):
            # Generate unique SKU
            attempt = 1
            while True:
                sku = generate_sku(prefix, attempt)
                if not StockItem.objects.filter(hotel=hotel, sku=sku).exists():
                    break
                attempt += 1

            # Upload the stock item
            _, created = StockItem.objects.get_or_create(
                hotel=hotel,
                name=item_name,
                defaults={
                    "sku": sku,
                    "active_stock_item": True,
                    "quantity": 100,
                    "alert_quantity": 20,
                    "volume_per_unit": None,
                    "unit": None,
                    "type": item_type
                }
            )

            if created:
                print(f"✔️ Created: {item_name} → Type: {type_name} | SKU: {sku}")
                count += 1

    print(f"\n✅ Done. {count} new StockItems created.")


if __name__ == "__main__":
    upload_stock_items(hotel_id=2)
