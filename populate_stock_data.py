"""
Populate stock items for HotelMate
Run: python populate_stock_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from decimal import Decimal
from stock_tracker.models import StockCategory, Location, StockItem
from hotel.models import Hotel


def populate_stock_items():
    """
    Populate stock categories, locations, and items from predefined data.
    """
    # Get first hotel (adjust as needed)
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found. Please create a hotel first.")
            return
        print(f"✅ Using hotel: {hotel.name}")
    except Exception as e:
        print(f"❌ Error getting hotel: {e}")
        return

    # Create Categories
    categories_data = [
        {'name': 'Spirits', 'sort_order': 1},
        {'name': 'Aperitif', 'sort_order': 2},
        {'name': 'Fortified', 'sort_order': 3},
        {'name': 'Liqueurs', 'sort_order': 4},
        {'name': 'Minerals', 'sort_order': 5},
        {'name': 'Wines', 'sort_order': 6},
        {'name': 'Beers', 'sort_order': 7},
        {'name': 'Cider', 'sort_order': 8},
        {'name': 'RTD', 'sort_order': 9},
    ]

    categories = {}
    for cat_data in categories_data:
        category, created = StockCategory.objects.get_or_create(
            hotel=hotel,
            name=cat_data['name'],
            defaults={'sort_order': cat_data['sort_order']}
        )
        categories[cat_data['name']] = category
        status = "✅ Created" if created else "⚠️  Already exists"
        print(f"{status} category: {cat_data['name']}")

    # Create Locations/Bins
    locations_data = ['Spirits', 'Liqueurs', 'Minerals', 'Whiskey', 'Wines', 'Keg Room', 'Fridge']
    locations = {}
    for loc_name in locations_data:
        location, created = Location.objects.get_or_create(
            hotel=hotel,
            name=loc_name,
            defaults={'active': True}
        )
        locations[loc_name] = location
        status = "✅ Created" if created else "⚠️  Already exists"
        print(f"{status} location: {loc_name}")

    # Stock Items Data
    items_data = [
        # Vodka
        {"sku":"S0001","name":"Dingle Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":1,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0002","name":"Smirnoff","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0003","name":"Absolut Flavour Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"Flavoured","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":1,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0004","name":"Ketel One","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0005","name":"Titos Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0006","name":"Grey Goose","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0007","name":"Belvedere","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0008","name":"Smirnoff Infusion","category_name":"Spirits","product_type":"Vodka","subtype":"Flavoured","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},

        # Gin
        {"sku":"S0009","name":"Dingle Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0010","name":"Muckross Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0011","name":"Gordons Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0012","name":"Tanqueray Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0013","name":"Beefeater 24","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0014","name":"Hendricks Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0015","name":"Method & Madness","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0016","name":"CDC Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0017","name":"Bombay Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0018","name":"Gunpowder Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0019","name":"Beefeater Pink","category_name":"Spirits","product_type":"Gin","subtype":"Pink","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0020","name":"Berthas Revenge","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0021","name":"Gin Special!","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","tag":"special","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0022","name":"Skellig Six18","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0023","name":"Silver Spear Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0024","name":"Glendalough","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0025","name":"Monkey 47","category_name":"Spirits","product_type":"Gin","subtype":"","size":"50cl","size_value":50,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},

        # Rum / Tequila
        {"sku":"S0026","name":"Bacardi","category_name":"Spirits","product_type":"Rum","subtype":"White","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0027","name":"Malibu","category_name":"Liqueurs","product_type":"Liqueur","subtype":"Coconut Rum Liqueur","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","bin_name":"Liqueurs","unit_cost":0},
        {"sku":"S0028","name":"Captain Morgan","category_name":"Spirits","product_type":"Rum","subtype":"Spiced","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0029","name":"Old Jamaican Rum","category_name":"Spirits","product_type":"Rum","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0030","name":"Havana 7yr","category_name":"Spirits","product_type":"Rum","subtype":"Añejo","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0031","name":"Kraken","category_name":"Spirits","product_type":"Rum","subtype":"Black Spiced","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0032","name":"Bacardi Gold","category_name":"Spirits","product_type":"Rum","subtype":"Gold","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0033","name":"Black of Kinsale","category_name":"Spirits","product_type":"Rum","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"S0034","name":"Tequila Gold","category_name":"Spirits","product_type":"Tequila","subtype":"Gold","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},

        # Aperitif / Fortified
        {"sku":"S0035","name":"Martini Dry","category_name":"Aperitif","product_type":"Vermouth","subtype":"Dry","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0036","name":"Martini Red","category_name":"Aperitif","product_type":"Vermouth","subtype":"Rosso","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0037","name":"Campari","category_name":"Aperitif","product_type":"Aperitif","subtype":"Bitter","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0038","name":"Pernod","category_name":"Aperitif","product_type":"Pastis","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0039","name":"Pimms","category_name":"Aperitif","product_type":"Aperitif","subtype":"No.1","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0040","name":"Bristol Cream","category_name":"Fortified","product_type":"Sherry","subtype":"Cream","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0041","name":"Winters Tale","category_name":"Fortified","product_type":"Sherry","subtype":"","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0042","name":"Sandeman Port","category_name":"Fortified","product_type":"Port","subtype":"","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0043","name":"Pedro X","category_name":"Fortified","product_type":"Sherry/Port","subtype":"PX","size":"75cl","size_value":75,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0044","name":"Limoncello","category_name":"Liqueurs","product_type":"Liqueur","subtype":"Citrus","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"S0045","name":"Ring of Kerry","category_name":"Spirits","product_type":"Spirit","subtype":"","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Spirits"},

        # Minerals / Mixers
        {"sku":"S0046","name":"Tonic Water","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0047","name":"Slimline Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0048","name":"Ginger Ale","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0049","name":"Soda Water","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0050","name":"Elderflower Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0051","name":"Fevere Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0052","name":"Coke","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0053","name":"Diet Coke","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0054","name":"Sprite Zero","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0055","name":"Cranberry Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0056","name":"Pineapple Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"S0057","name":"Orange Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},

        # Irish Whiskey
        {"sku":"S0058","name":"Dingle Whiskey","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":1,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0059","name":"Powers","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0060","name":"Jameson","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":2,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0061","name":"Paddy","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0062","name":"Crested Ten","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0063","name":"Red Bush","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0064","name":"Black Bush","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0065","name":"West Cork Bourbon","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Bourbon Cask","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0066","name":"West Cork Black","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Black Cask","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0067","name":"Powers 3 Swallow","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0068","name":"Powers Johns Lane","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0069","name":"Green Spot","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0070","name":"Yellow Spot","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0071","name":"Red Breast 12 yr Old","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0072","name":"Red Breast 15YR","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0073","name":"Midleton Vintage Release","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0074","name":"Jameson Caskmates Stout","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Finish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0075","name":"Jameson Cask IPA","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Finish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0076","name":"Jameson Black Barrel","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0077","name":"Roe & Co","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},

        # Blended Scotch
        {"sku":"S0078","name":"Teachers","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0079","name":"Famous Grouse","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0080","name":"JW Red","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":2,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0081","name":"JW Black","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0082","name":"Black & White","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},

        # Single Malt Scotch
        {"sku":"S0083","name":"Glenmorangie 10 Year Old","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Single Malt","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},

        # American / Canadian / Tennessee
        {"sku":"S0084","name":"Southern Comfort","category_name":"Spirits","product_type":"Whiskey","subtype":"American Liqueur","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0085","name":"Wild Turkey","category_name":"Spirits","product_type":"Whiskey","subtype":"Bourbon","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0086","name":"Buffalo Trace","category_name":"Spirits","product_type":"Whiskey","subtype":"Bourbon","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0087","name":"Canadian Club","category_name":"Spirits","product_type":"Whiskey","subtype":"Canadian","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0088","name":"Jack Daniels","category_name":"Spirits","product_type":"Whiskey","subtype":"Tennessee","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":1,"unit_cost":0,"bin_name":"Whiskey"},

        # Cognac / Brandy
        {"sku":"S0089","name":"Courvoisier XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0090","name":"Martell","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0091","name":"Martell XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0092","name":"Hennessy VS","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac VS","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","par_level":1,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0093","name":"Hennessy VSOP","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac VSOP","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0094","name":"Hennessy XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"S0095","name":"Remy Martin","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac","size":"70cl","size_value":70,"size_unit":"cl","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Whiskey"},

        # Draught Beers (Keg stock)
        {"sku":"S0096","name":"Heineken (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0097","name":"Coors (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0098","name":"Moretti (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0099","name":"Orchard Thieves (Draught)","category_name":"Cider","product_type":"Cider","subtype":"Apple Cider","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0100","name":"Orchard Thieves Blood Orange (Draught)","category_name":"Cider","product_type":"Cider","subtype":"Blood Orange","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0101","name":"Murphy's (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0102","name":"Murphy's Irish Red Ale (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Red Ale","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0103","name":"Beamish (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0104","name":"Guinness (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0105","name":"Cute Hoor (Draught)","category_name":"Beers","product_type":"Ale","subtype":"Irish Pale Ale","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0106","name":"Lagunitas IPA (Draught)","category_name":"Beers","product_type":"Beer","subtype":"IPA","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0107","name":"Killarney Blonde (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Blonde Ale","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"S0108","name":"Heineken 0.0 (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free","size":"30L Keg","size_value":30,"size_unit":"L","uom":1,"base_unit":"L","unit_cost":0,"bin_name":"Keg Room"},

        # Bottled Beers / Ciders
        {"sku":"S0109","name":"Btl Heineken 0.0","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0110","name":"Btl Killarney Blonde","category_name":"Beers","product_type":"Beer","subtype":"Blonde Ale","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0111","name":"Btl Killarney IPA","category_name":"Beers","product_type":"Beer","subtype":"IPA","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0112","name":"Btl Corona","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0113","name":"Btl Budweiser","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0114","name":"Btl Bulmers","category_name":"Cider","product_type":"Cider","subtype":"Apple Cider","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0115","name":"Btl Bulmers 0.0","category_name":"Cider","product_type":"Cider","subtype":"Alcohol-Free","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0116","name":"Btl Erdinger 0.0","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free Wheat Beer","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0117","name":"Btl Carlsberg Light","category_name":"Beers","product_type":"Beer","subtype":"Light Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0118","name":"Btl Smithwicks","category_name":"Beers","product_type":"Beer","subtype":"Red Ale","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0119","name":"WKD Blue","category_name":"RTD","product_type":"Alcopop","subtype":"RTD","size":"275ml Bottle","size_value":275,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"S0120","name":"Smirnoff Ice","category_name":"RTD","product_type":"Alcopop","subtype":"Vodka Mix","size":"275ml Bottle","size_value":275,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"}
    ]

    # Create Stock Items
    print(f"\n📦 Creating {len(items_data)} stock items...")
    created_count = 0
    existing_count = 0
    error_count = 0

    for item_data in items_data:
        try:
            category = categories.get(item_data['category_name'])
            bin_location = locations.get(item_data.get('bin_name'))

            item, created = StockItem.objects.get_or_create(
                hotel=hotel,
                sku=item_data['sku'],
                defaults={
                    'name': item_data['name'],
                    'category': category,
                    'product_type': item_data.get('product_type', ''),
                    'subtype': item_data.get('subtype', ''),
                    'tag': item_data.get('tag', ''),
                    'size': item_data['size'],
                    'size_value': Decimal(str(item_data['size_value'])),
                    'size_unit': item_data['size_unit'],
                    'uom': Decimal(str(item_data['uom'])),
                    'base_unit': item_data['base_unit'],
                    'unit_cost': Decimal(str(item_data['unit_cost'])),
                    'par_level': Decimal(str(item_data.get('par_level', 0))),
                    'bin': bin_location,
                    'active': True,
                }
            )

            if created:
                created_count += 1
                print(f"  ✅ Created: {item.sku} - {item.name}")
            else:
                existing_count += 1
                print(f"  ⚠️  Exists: {item.sku} - {item.name}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error creating {item_data.get('sku', 'unknown')}: {e}")

    print(f"\n" + "="*60)
    print(f"📊 Summary:")
    print(f"   ✅ Created: {created_count}")
    print(f"   ⚠️  Already existed: {existing_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📦 Total processed: {len(items_data)}")
    print("="*60)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🍾 HotelMate Stock Items Population Script")
    print("="*60 + "\n")
    populate_stock_items()
    print("\n✅ Script completed!\n")
