import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "porterproject.settings")
django.setup()

from room.models import RoomServiceItem

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
        {'name': 'Cappuccino', 'price': 3.95, 'description': 'A rich and creamy cappuccino with a perfect foam.'},
        {'name': 'Irish Coffee', 'price': 7.00, 'description': 'A warm Irish coffee made with whiskey, coffee, sugar, and cream.'},
        {'name': 'Guinness', 'price': 5.90, 'description': 'A pint of the famous Irish stout, rich and smooth.'},
        {'name': 'Mineral Water', 'price': 2.00, 'description': 'Refreshing still or sparkling water.'},
        {'name': 'Coca-Cola', 'price': 3.60, 'description': 'Classic Coca-Cola served chilled.'},
        {'name': 'Orange Juice', 'price': 3.60, 'description': 'Freshly squeezed orange juice.'},
        {'name': 'Hot Chocolate', 'price': 3.50, 'description': 'Rich and creamy hot chocolate with whipped cream.'},
        {'name': 'Sparkling Wine', 'price': 8.00, 'description': 'A glass of refreshing sparkling wine.'},
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
