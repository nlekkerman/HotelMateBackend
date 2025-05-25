import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from room_services.models import RoomServiceItem

def create_room_service_items():
    food_items = [
        {"name": "Soup", "price": 5.99, "description": "A comforting house soup, perfect to start your meal."},
        {"name": "Chicken Wings", "price": 7.49, "description": "Crispy chicken wings tossed in a spicy sauce."},
        {"name": "Caesar Salad", "price": 9.99, "description": "Classic Caesar salad with grilled chicken and croutons."},
        {"name": "Smash (Beef) Burger", "price": 11.99, "description": "Juicy smashed beef burger with cheddar and special sauce."},
        {"name": "Chicken Burger", "price": 10.99, "description": "Grilled chicken burger with lettuce, tomato, and mayo."},
        {"name": "Chicken Curry", "price": 9.49, "description": "Tender chicken cooked in a flavorful curry sauce."},
        {"name": "Veg Curry", "price": 8.99, "description": "Mixed vegetables simmered in a spicy curry sauce."},
        {"name": "Margherita Pizza", "price": 9.29, "description": "Classic Margherita pizza with fresh basil and mozzarella."},
        {"name": "Garlic Mushroom Pizza", "price": 6.79, "description": "Sautéed garlic mushrooms served as a tasty starter."},
        {"name": "Parma Ham Pizza", "price": 10.49, "description": "Thin slices of Parma ham served with fresh greens."},
        {"name": "Goats Cheese Pizza", "price": 9.59, "description": "Creamy goats cheese served with a side salad."},
    ]

    drinks_items = [
        # Cocktail Selection
        {"name": "At The Beach", "price": 14.00, "description": "Fruity mix of Smirnoff, schnapps, orange, cranberry & grenadine."},
        {"name": "Cosmopolitan", "price": 14.00, "description": "Classic cocktail with vodka, triple sec, cranberry & lime."},
        {"name": "Strawberry Fiz", "price": 14.00, "description": "Refreshing sloe gin with strawberry, lime, and soda."},
        {"name": "Classic Negroni", "price": 14.00, "description": "Strong blend of Bombay gin, vermouth, and Campari."},
        {"name": "Passionfruit Martini", "price": 14.00, "description": "Tropical mix of vanilla vodka, Passoa, and passionfruit."},

        # Aperitif & Liqueur’s
        {"name": "Pernod/Campari", "price": 6.00, "description": "Classic aperitif with a bitter, herbal taste."},
        {"name": "Sweet/Dry Martini", "price": 6.00, "description": "Traditional vermouth-based aperitif."},
        {"name": "Baileys", "price": 6.00, "description": "Creamy Irish liqueur with hints of chocolate and whiskey."},
        {"name": "Kahlua/Tia Maria", "price": 6.00, "description": "Coffee-flavored liqueurs with a rich, sweet finish."},

        # Bottled Beers & Ciders
        {"name": "Heineken/Coors/Sol/Bud", "price": 5.70, "description": "Selection of light, refreshing bottled beers."},
        {"name": "Killarney Blonde Ale/IPA", "price": 7.50, "description": "Craft beer with smooth and hoppy flavor."},
        {"name": "West Coast Cooler Org/Rose", "price": 7.50, "description": "Light wine-based spritzers, original or rosé."},
        {"name": "WKD Blue", "price": 7.20, "description": "Fruity and fizzy blue alcopop."},
        {"name": "Smirnoff Ice", "price": 7.20, "description": "Lemon-flavored vodka-based cooler."},
        {"name": "Bulmer’s Pt Bt/Light", "price": 7.30, "description": "Classic or light Irish apple cider."},
        {"name": "Long Neck Bulmer’s", "price": 6.20, "description": "Single-serve Bulmer’s Irish cider."},
        {"name": "Cronin’s", "price": 7.30, "description": "Artisan Irish cider with crisp apple flavor."},
        {"name": "Kopparberg", "price": 7.30, "description": "Swedish fruit cider with bold flavors."},

        # Non-Alcoholic
        {"name": "Heineken/Erdinger Free", "price": 5.50, "description": "Alcohol-free beers with great taste."},
        {"name": "Cronin’s Cider Free", "price": 5.50, "description": "Refreshing non-alcoholic Irish cider."},

        # House Red Wine
        {"name": "Marques De Plata (Spain)", "price": 30.00, "description": "Smooth Syrah-Cabernet blend from Spain."},
        {"name": "Les Roucas Merlot (France)", "price": 31.00, "description": "Fruity and soft French Merlot."},
        {"name": "Roquende Reserve Cabernet (France)", "price": 34.00, "description": "Full-bodied French Cabernet Sauvignon."},
        {"name": "Equino Malbec (Argentina)", "price": 34.00, "description": "Rich and spicy Argentinian Malbec."},
        {"name": "EL Somo Rioja (Spain)", "price": 34.00, "description": "Traditional Spanish red with oaky finish."},

        # House White Wine
        {"name": "Marques De Plata Sauvignon Blanc (Spain)", "price": 30.00, "description": "Crisp and zesty white from Spain."},
        {"name": "Tini Pinot Grigio (Italy)", "price": 31.00, "description": "Light and fresh Italian Pinot Grigio."},
        {"name": "La Chevaliere Chardonnay (France)", "price": 34.00, "description": "Elegant French Chardonnay with citrus notes."},

        # Rose Wine
        {"name": "La Chevaliere Rose (France)", "price": 36.00, "description": "Delicate and fruity French rosé wine."},
    ]


    for item in food_items:
        room_service_item = RoomServiceItem(
            name=item['name'],
            category='Food',
            price=item['price'],
            description=item['description'],
            image=''
        )
        room_service_item.save()
        print(f"Created Food item: {item['name']}")

    for item in drinks_items:
        room_service_item = RoomServiceItem(
            name=item['name'],
            category='Drinks',
            price=item['price'],
            description=item['description'],
            image=''
        )
        room_service_item.save()
        print(f"Created Drink item: {item['name']}")

if __name__ == "__main__":
    create_room_service_items()
    print("All Food and Drink items created.")
