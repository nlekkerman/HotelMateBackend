import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

# Import models
from room_services.models import BreakfastItem, BreakfastOrder, BreakfastOrderItem

def create_breakfast_items():
    # Define the items to be created (no prices)
    items = [
        # Mains
        {"name": "Full Irish Breakfast", "category": "Mains", "description": "Eggs, bacon, sausage, black & white pudding, grilled tomato, beans, toast."},
        {"name": "Vegetarian Full Irish Breakfast", "category": "Mains", "description": "Grilled halloumi, vegetarian sausage, eggs, mushrooms, tomato, beans, toast."},
        {"name": "Pancakes with Syrup & Berries", "category": "Mains", "description": "Fluffy pancakes served with maple syrup and mixed berries."},
        {"name": "Fried Eggs", "category": "Mains", "description": "Eggs fried sunny side up or over easy."},
        {"name": "Scrambled Eggs", "category": "Mains", "description": "Light and fluffy scrambled eggs with a hint of cream."},
        {"name": "Poached Eggs", "category": "Mains", "description": "Soft poached eggs, perfect on toast."},

        # Hot Buffet
        {"name": "Crispy Bacon", "category": "Hot Buffet", "description": "Crispy rashers of bacon cooked to perfection."},
        {"name": "Irish Sausages", "category": "Hot Buffet", "description": "Traditional pork sausages with herbs."},
        {"name": "Vegan Sausage", "category": "Hot Buffet", "description": "Plant-based sausage, flavorful and satisfying."},
        {"name": "Grilled Tomatoes", "category": "Hot Buffet", "description": "Seasoned tomatoes grilled for extra flavor."},
        {"name": "Baked Beans", "category": "Hot Buffet", "description": "Classic baked beans in tomato sauce."},
        {"name": "Sautéed Mushrooms", "category": "Hot Buffet", "description": "Buttery mushrooms sautéed with herbs."},
        {"name": "Hash Browns", "category": "Hot Buffet", "description": "Crispy golden-brown hash browns."},
        {"name": "Oat Porridge", "category": "Hot Buffet", "description": "Warm creamy oat porridge served with honey or brown sugar."},

        # Cold Buffet
        {"name": "Yogurt with Granola", "category": "Cold Buffet", "description": "Creamy natural yogurt topped with granola and fruit."},
        {"name": "Fresh Fruit Salad", "category": "Cold Buffet", "description": "Seasonal fruits cut fresh daily."},
        {"name": "Cold Meats & Cheese Plate", "category": "Cold Buffet", "description": "Selection of sliced ham, salami, and cheeses."},

        # Cereals (split out individually, removing 'Cereal Selection')
        {"name": "Choco Pops", "category": "Cold Buffet", "description": "Sweet chocolate-flavored puffed rice cereal."},
        {"name": "Cornflakes", "category": "Cold Buffet", "description": "Classic toasted cornflake cereal."},
        {"name": "Muesli", "category": "Cold Buffet", "description": "Mixed rolled oats, nuts, seeds, and dried fruit."},
        {"name": "Bran Flakes", "category": "Cold Buffet", "description": "High-fiber bran flake cereal."},

        # Breads & Baked Goods
        {"name": "White Toast", "category": "Breads", "description": "Freshly toasted white bread served with butter."},
        {"name": "Brown Toast", "category": "Breads", "description": "Freshly toasted brown bread served with butter."},
        {"name": "Gluten-Free Bread", "category": "Breads", "description": "Toasted gluten-free bread option."},
        {"name": "Croissant", "category": "Breads", "description": "Flaky and buttery croissant, freshly baked."},
        {"name": "Pain au Chocolat", "category": "Breads", "description": "French pastry filled with dark chocolate."},
        {"name": "Assorted Danish Pastries", "category": "Breads", "description": "Selection of mini danishes with fruit or custard."},

        # Condiments
        {"name": "Strawberry Jam", "category": "Condiments", "description": "Sweet strawberry jam portion."},
        {"name": "Raspberry Jam", "category": "Condiments", "description": "Tart raspberry jam portion."},
        {"name": "Apricot Jam", "category": "Condiments", "description": "Rich apricot jam portion."},
        {"name": "Honey", "category": "Condiments", "description": "Golden honey served in individual pots."},
        {"name": "Butter", "category": "Condiments", "description": "Portioned Irish creamery butter."},

        # Drinks
        {"name": "Irish Breakfast Tea", "category": "Drinks", "description": "Strong black tea with a rich aroma."},
        {"name": "Green Tea", "category": "Drinks", "description": "Soothing green tea, light and refreshing."},
        {"name": "Coffee", "category": "Drinks", "description": "Freshly ground coffee, served hot."},
        {"name": "Latte", "category": "Drinks", "description": "Creamy espresso with steamed milk."},
        {"name": "Espresso", "category": "Drinks", "description": "Strong concentrated coffee shot."},
        {"name": "Cappuccino", "category": "Drinks", "description": "Espresso with frothy milk foam."},
        {"name": "Orange Juice", "category": "Drinks", "description": "Chilled orange juice."},
        {"name": "Apple Juice", "category": "Drinks", "description": "Chilled apple juice."},
        {"name": "Still Mineral Water", "category": "Drinks", "description": "Bottled still water."}
    ]



    created = 0
    skipped = 0

    # Create each item
    for item in items:
        if BreakfastItem.objects.filter(name=item['name']).exists():
            print(f"Item '{item['name']}' already exists. Skipping.")
            skipped += 1
            continue
        
        breakfast_item = BreakfastItem(
            name=item['name'],
            category=item['category'],
            description=item['description']
        )
        breakfast_item.save()
        created += 1
        print(f"Created Breakfast Item: {item['name']}.")

    print(f"\nDone. {created} new items created. {skipped} items skipped.")



if __name__ == "__main__":
    create_breakfast_items()  # Create breakfast items
   
