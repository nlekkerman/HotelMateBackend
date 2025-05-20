import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "porterproject.settings")
django.setup()

# Import models
from room.models import BreakfastItem, BreakfastOrder, BreakfastOrderItem

def create_breakfast_items():
    # Define the items to be created (no prices)
    items = [
        {"name": "Full Irish Breakfast", "category": "Mains", "description": "Traditional Irish breakfast with eggs, bacon, sausage, black pudding, white pudding, and grilled tomato."},
        {"name": "Pancakes", "category": "Mains", "description": "Fluffy pancakes served with maple syrup, butter, and fresh berries."},
        {"name": "Toast (White or Brown)", "category": "Breads", "description": "Choice of white or brown toast, served with butter and jam."},
        {"name": "Yogurt with Granola", "category": "Sides", "description": "Creamy yogurt topped with crunchy granola and fresh fruit."},
        {"name": "Tea", "category": "Drinks", "description": "A pot of freshly brewed Irish tea."},
        {"name": "Coffee", "category": "Drinks", "description": "Freshly brewed coffee served with milk or sugar."},
        {"name": "Sautéed Mushrooms", "category": "Sides", "description": "Fresh mushrooms sautéed in butter and herbs."},
        {"name": "Crispy Bacon", "category": "Sides", "description": "Crispy, golden bacon strips."},
        {"name": "Eggs (Fried/Scrambled/Poached)", "category": "Mains", "description": "Eggs cooked to your choice: fried, scrambled, or poached."},
        {"name": "Fresh Fruit Salad", "category": "Sides", "description": "A refreshing selection of seasonal fresh fruits."}
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
   
