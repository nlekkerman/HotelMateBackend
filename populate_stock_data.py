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
        # Vodka (70cl = 700ml ÷ 35ml = 20 shots)
        {"sku":"SP0001","name":"Dingle Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":1,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0002","name":"Smirnoff","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0003","name":"Absolut Flavour Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"Flavoured","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":1,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0004","name":"Ketel One","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0005","name":"Titos Vodka","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0006","name":"Grey Goose","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0007","name":"Belvedere","category_name":"Spirits","product_type":"Vodka","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0008","name":"Smirnoff Infusion","category_name":"Spirits","product_type":"Vodka","subtype":"Flavoured","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},

        # Gin (70cl = 20 shots, 50cl = 14.29 shots)
        {"sku":"SP0009","name":"Dingle Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0010","name":"Muckross Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0011","name":"Gordons Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0012","name":"Tanqueray Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0013","name":"Beefeater 24","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0014","name":"Hendricks Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0015","name":"Method & Madness","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0016","name":"CDC Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0017","name":"Bombay Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":2,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0018","name":"Gunpowder Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0019","name":"Beefeater Pink","category_name":"Spirits","product_type":"Gin","subtype":"Pink","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0020","name":"Berthas Revenge","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0021","name":"Gin Special!","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"tag":"special","unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0022","name":"Skellig Six18","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0023","name":"Silver Spear Gin","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0024","name":"Glendalough","category_name":"Spirits","product_type":"Gin","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0025","name":"Monkey 47","category_name":"Spirits","product_type":"Gin","subtype":"","size":"50cl","size_value":500,"size_unit":"ml","uom":14.29,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},

        # Rum / Tequila (70cl = 20 shots)
        {"sku":"SP0026","name":"Bacardi","category_name":"Spirits","product_type":"Rum","subtype":"White","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"LI0002","name":"Malibu","category_name":"Liqueurs","product_type":"Liqueur","subtype":"Coconut Rum Liqueur","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"bin_name":"Liqueurs","unit_cost":0},
        {"sku":"SP0027","name":"Captain Morgan","category_name":"Spirits","product_type":"Rum","subtype":"Spiced","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0028","name":"Old Jamaican Rum","category_name":"Spirits","product_type":"Rum","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0029","name":"Havana 7yr","category_name":"Spirits","product_type":"Rum","subtype":"Añejo","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0030","name":"Kraken","category_name":"Spirits","product_type":"Rum","subtype":"Black Spiced","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0031","name":"Bacardi Gold","category_name":"Spirits","product_type":"Rum","subtype":"Gold","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0032","name":"Black of Kinsale","category_name":"Spirits","product_type":"Rum","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},
        {"sku":"SP0033","name":"Tequila Gold","category_name":"Spirits","product_type":"Tequila","subtype":"Gold","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},

        # Aperitif / Fortified (75cl = 21.43 shots, 70cl = 20 shots)
        {"sku":"AP0001","name":"Martini Dry","category_name":"Aperitif","product_type":"Vermouth","subtype":"Dry","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"AP0002","name":"Martini Red","category_name":"Aperitif","product_type":"Vermouth","subtype":"Rosso","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"AP0003","name":"Campari","category_name":"Aperitif","product_type":"Aperitif","subtype":"Bitter","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"AP0004","name":"Pernod","category_name":"Aperitif","product_type":"Pastis","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"AP0005","name":"Pimms","category_name":"Aperitif","product_type":"Aperitif","subtype":"No.1","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"FO0001","name":"Bristol Cream","category_name":"Fortified","product_type":"Sherry","subtype":"Cream","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"FO0002","name":"Winters Tale","category_name":"Fortified","product_type":"Sherry","subtype":"","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"FO0003","name":"Sandeman Port","category_name":"Fortified","product_type":"Port","subtype":"","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"FO0004","name":"Pedro X","category_name":"Fortified","product_type":"Sherry/Port","subtype":"PX","size":"75cl","size_value":750,"size_unit":"ml","uom":21.43,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"LI0001","name":"Limoncello","category_name":"Liqueurs","product_type":"Liqueur","subtype":"Citrus","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Liqueurs"},
        {"sku":"SP0034","name":"Ring of Kerry","category_name":"Spirits","product_type":"Spirit","subtype":"","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Spirits"},

        # Minerals / Mixers
        {"sku":"MI0001","name":"Tonic Water","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0002","name":"Slimline Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0003","name":"Ginger Ale","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0004","name":"Soda Water","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0005","name":"Elderflower Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0006","name":"Fevere Tonic","category_name":"Minerals","product_type":"Soft Drink","subtype":"Tonic","size":"200ml","size_value":200,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0007","name":"Coke","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0008","name":"Diet Coke","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0009","name":"Sprite Zero","category_name":"Minerals","product_type":"Soft Drink","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0010","name":"Cranberry Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0011","name":"Pineapple Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},
        {"sku":"MI0012","name":"Orange Juice","category_name":"Minerals","product_type":"Juice","subtype":"","size":"330ml","size_value":330,"size_unit":"ml","uom":1,"base_unit":"ml","unit_cost":0,"bin_name":"Minerals"},

        # Irish Whiskey (70cl = 700ml ÷ 35ml = 20 shots)
        {"sku":"SP0035","name":"Dingle Whiskey","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":1,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0036","name":"Powers","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0037","name":"Jameson","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":2,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0038","name":"Paddy","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0039","name":"Crested Ten","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0040","name":"Red Bush","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0041","name":"Black Bush","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0042","name":"West Cork Bourbon","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Bourbon Cask","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0043","name":"West Cork Black","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Black Cask","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0044","name":"Powers 3 Swallow","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0045","name":"Powers Johns Lane","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0046","name":"Green Spot","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0047","name":"Yellow Spot","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0048","name":"Red Breast 12 yr Old","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0049","name":"Red Breast 15YR","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish Single Pot Still","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0050","name":"Midleton Vintage Release","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0051","name":"Jameson Caskmates Stout","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Finish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0052","name":"Jameson Cask IPA","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish - Finish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0053","name":"Jameson Black Barrel","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0054","name":"Roe & Co","category_name":"Spirits","product_type":"Whiskey","subtype":"Irish","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},

        # Blended Scotch (70cl = 20 shots)
        {"sku":"SP0055","name":"Teachers","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0056","name":"Famous Grouse","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0057","name":"JW Red","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":2,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0058","name":"JW Black","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0059","name":"Black & White","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Blended","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},

        # Single Malt Scotch (70cl = 20 shots)
        {"sku":"SP0060","name":"Glenmorangie 10 Year Old","category_name":"Spirits","product_type":"Whiskey","subtype":"Scotch Single Malt","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},

        # American / Canadian / Tennessee (70cl = 20 shots)
        {"sku":"SP0061","name":"Southern Comfort","category_name":"Spirits","product_type":"Whiskey","subtype":"American Liqueur","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0062","name":"Wild Turkey","category_name":"Spirits","product_type":"Whiskey","subtype":"Bourbon","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0063","name":"Buffalo Trace","category_name":"Spirits","product_type":"Whiskey","subtype":"Bourbon","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0064","name":"Canadian Club","category_name":"Spirits","product_type":"Whiskey","subtype":"Canadian","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0065","name":"Jack Daniels","category_name":"Spirits","product_type":"Whiskey","subtype":"Tennessee","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":1,"unit_cost":0,"bin_name":"Whiskey"},

        # Cognac / Brandy (70cl = 20 shots)
        {"sku":"SP0066","name":"Courvoisier XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0067","name":"Martell","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0068","name":"Martell XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0069","name":"Hennessy VS","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac VS","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"par_level":1,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0070","name":"Hennessy VSOP","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac VSOP","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0071","name":"Hennessy XO","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac XO","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},
        {"sku":"SP0072","name":"Remy Martin","category_name":"Spirits","product_type":"Brandy","subtype":"Cognac","size":"70cl","size_value":700,"size_unit":"ml","uom":20,"base_unit":"ml","serving_size":35,"unit_cost":0,"bin_name":"Whiskey"},

        # Wines - Bottles (sold as bottles, UOM=1)
        # White Wines
        {"sku":"WI0001","name":"Bt Marques Sauv Blanc","category_name":"Wines","product_type":"Wine","subtype":"White - Sauvignon Blanc","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0002","name":"Bt Sonetti Pinot","category_name":"Wines","product_type":"Wine","subtype":"White - Pinot Grigio","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0003","name":"Bt Alvier Chard","category_name":"Wines","product_type":"Wine","subtype":"White - Chardonnay","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0004","name":"Bt Cheval Imperial","category_name":"Wines","product_type":"Wine","subtype":"White","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0005","name":"Bt Les Jamelles Sauv B","category_name":"Wines","product_type":"Wine","subtype":"White - Sauvignon Blanc","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0006","name":"Bt Chevaliere Chardonnay","category_name":"Wines","product_type":"Wine","subtype":"White - Chardonnay","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0007","name":"Bt Classic Nelson Blanc","category_name":"Wines","product_type":"Wine","subtype":"White","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0008","name":"Bt Pazo Albarino","category_name":"Wines","product_type":"Wine","subtype":"White - Albariño","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0009","name":"Bt Verocicchio","category_name":"Wines","product_type":"Wine","subtype":"White","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0010","name":"Bt Moillard Macon Villages","category_name":"Wines","product_type":"Wine","subtype":"White - Mâcon","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0011","name":"Bt Pouilly Fume","category_name":"Wines","product_type":"Wine","subtype":"White - Pouilly-Fumé","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0012","name":"Bt Chablis Emeraude","category_name":"Wines","product_type":"Wine","subtype":"White - Chablis","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        
        # Red Wines
        {"sku":"WI0013","name":"Bt Marques Cabernet","category_name":"Wines","product_type":"Wine","subtype":"Red - Cabernet Sauvignon","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0014","name":"Bt Roucas Merlot","category_name":"Wines","product_type":"Wine","subtype":"Red - Merlot","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0015","name":"Bt Santa Ana Malbec","category_name":"Wines","product_type":"Wine","subtype":"Red - Malbec","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0016","name":"Bt Equino Malbec","category_name":"Wines","product_type":"Wine","subtype":"Red - Malbec","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0017","name":"Bt Roquende Cab","category_name":"Wines","product_type":"Wine","subtype":"Red - Cabernet Sauvignon","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0018","name":"Bt El Somo Rioja","category_name":"Wines","product_type":"Wine","subtype":"Red - Rioja","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0019","name":"Bt Chateau Pascaud","category_name":"Wines","product_type":"Wine","subtype":"Red - Bordeaux","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0020","name":"Bt Plantamura Primitivo","category_name":"Wines","product_type":"Wine","subtype":"Red - Primitivo","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0021","name":"Bt Tenuta Garetti","category_name":"Wines","product_type":"Wine","subtype":"Red","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0022","name":"Bt Domaine du Vissoux Fleurie","category_name":"Wines","product_type":"Wine","subtype":"Red - Fleurie","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0023","name":"Bt Chateau de Dommy","category_name":"Wines","product_type":"Wine","subtype":"Red","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        
        # Rosé Wines
        {"sku":"WI0024","name":"Bt Les Petits J Rose","category_name":"Wines","product_type":"Wine","subtype":"Rosé","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0025","name":"Bt La Chevaliere Rose","category_name":"Wines","product_type":"Wine","subtype":"Rosé","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        
        # Sparkling Wines & Champagne
        {"sku":"WI0026","name":"Pannier Champ","category_name":"Wines","product_type":"Wine","subtype":"Champagne","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0027","name":"Btl Prosecco","category_name":"Wines","product_type":"Wine","subtype":"Prosecco","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0028","name":"Bottle Perrisecco","category_name":"Wines","product_type":"Wine","subtype":"Prosecco","size":"75cl","size_value":750,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},
        {"sku":"WI0029","name":"1/4 Bt Prosecco","category_name":"Wines","product_type":"Wine","subtype":"Prosecco","size":"18.75cl","size_value":187.5,"size_unit":"ml","uom":1,"base_unit":"ml","serving_size":150,"unit_cost":0,"bin_name":"Wines"},

        # Draught Beers (Keg stock) - Organized by brand then size
        # Beamish
        {"sku":"BE0001","name":"Beamish (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Coors
        {"sku":"BE0002","name":"Coors (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"BE0003","name":"Coors (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"50L Keg","size_value":50000,"size_unit":"ml","uom":88.0,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Cute Hoor
        {"sku":"BE0004","name":"Cute Hoor (Draught)","category_name":"Beers","product_type":"Ale","subtype":"Irish Pale Ale","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Guinness
        {"sku":"BE0005","name":"Guinness (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"BE0006","name":"Guinness (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"50L Keg","size_value":50000,"size_unit":"ml","uom":88.0,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Heineken
        {"sku":"BE0007","name":"Heineken (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"BE0008","name":"Heineken (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"50L Keg","size_value":50000,"size_unit":"ml","uom":88.0,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Heineken 0.0
        {"sku":"BE0009","name":"Heineken 0.0 (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free","size":"20L Keg","size_value":20000,"size_unit":"ml","uom":35.2,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        {"sku":"BE0010","name":"Heineken 0.0 (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Killarney Blonde
        {"sku":"BE0011","name":"Killarney Blonde (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Blonde Ale","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Lagunitas IPA
        {"sku":"BE0012","name":"Lagunitas IPA (Draught)","category_name":"Beers","product_type":"Beer","subtype":"IPA","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Moretti
        {"sku":"BE0013","name":"Moretti (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Murphy's
        {"sku":"BE0014","name":"Murphy's (Draught)","category_name":"Beers","product_type":"Stout","subtype":"Irish Stout","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Murphy's Irish Red Ale
        {"sku":"BE0015","name":"Murphy's Irish Red Ale (Draught)","category_name":"Beers","product_type":"Beer","subtype":"Red Ale","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Orchard Thieves
        {"sku":"CI0001","name":"Orchard Thieves (Draught)","category_name":"Cider","product_type":"Cider","subtype":"Apple Cider","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},
        
        # Orchard Thieves Blood Orange
        {"sku":"CI0002","name":"Orchard Thieves Blood Orange (Draught)","category_name":"Cider","product_type":"Cider","subtype":"Blood Orange","size":"30L Keg","size_value":30000,"size_unit":"ml","uom":52.8,"base_unit":"ml","serving_size":568,"unit_cost":0,"bin_name":"Keg Room"},

        # Bottled Beers / Ciders
        {"sku":"BE0016","name":"Btl Heineken 0.0","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0017","name":"Btl Killarney Blonde","category_name":"Beers","product_type":"Beer","subtype":"Blonde Ale","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0018","name":"Btl Killarney IPA","category_name":"Beers","product_type":"Beer","subtype":"IPA","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0019","name":"Btl Corona","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0020","name":"Btl Budweiser","category_name":"Beers","product_type":"Beer","subtype":"Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"CI0003","name":"Btl Bulmers","category_name":"Cider","product_type":"Cider","subtype":"Apple Cider","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"CI0004","name":"Btl Bulmers 0.0","category_name":"Cider","product_type":"Cider","subtype":"Alcohol-Free","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0021","name":"Btl Erdinger 0.0","category_name":"Beers","product_type":"Beer","subtype":"Alcohol-Free Wheat Beer","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0022","name":"Btl Carlsberg Light","category_name":"Beers","product_type":"Beer","subtype":"Light Lager","size":"330ml Bottle","size_value":330,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"BE0023","name":"Btl Smithwicks","category_name":"Beers","product_type":"Beer","subtype":"Red Ale","size":"500ml Bottle","size_value":500,"size_unit":"ml","uom":12,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"RT0001","name":"WKD Blue","category_name":"RTD","product_type":"Alcopop","subtype":"RTD","size":"275ml Bottle","size_value":275,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"},
        {"sku":"RT0002","name":"Smirnoff Ice","category_name":"RTD","product_type":"Alcopop","subtype":"Vodka Mix","size":"275ml Bottle","size_value":275,"size_unit":"ml","uom":24,"base_unit":"ml","unit_cost":0,"bin_name":"Fridge"}
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

            # Try to get existing item or create new one
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
                    'serving_size': Decimal(str(item_data.get('serving_size', 0))) if item_data.get('serving_size') else None,
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
                # Update existing item with new values (including serving_size)
                item.name = item_data['name']
                item.category = category
                item.product_type = item_data.get('product_type', '')
                item.subtype = item_data.get('subtype', '')
                item.tag = item_data.get('tag', '')
                item.size = item_data['size']
                item.size_value = Decimal(str(item_data['size_value']))
                item.size_unit = item_data['size_unit']
                item.uom = Decimal(str(item_data['uom']))
                item.base_unit = item_data['base_unit']
                item.serving_size = Decimal(str(item_data.get('serving_size', 0))) if item_data.get('serving_size') else None
                item.unit_cost = Decimal(str(item_data['unit_cost']))
                item.par_level = Decimal(str(item_data.get('par_level', 0)))
                item.bin = bin_location
                item.active = True
                item.save()
                existing_count += 1
                print(f"  🔄 Updated: {item.sku} - {item.name}")

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
