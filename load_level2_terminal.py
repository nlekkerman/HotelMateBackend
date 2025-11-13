"""
Load Level 2 (Odd One Out) questions from terminal input
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion, QuizAnswer

def load_level2():
    data = {
        "level_2": [
            {"text": "Odd one out", "options": ["Apple", "Banana", "Grapes", "Carrot"], "correct": "Carrot"},
            {"text": "Odd one out", "options": ["Lion", "Tiger", "Leopard", "Shark"], "correct": "Shark"},
            {"text": "Odd one out", "options": ["January", "February", "July", "Spider"], "correct": "Spider"},
            {"text": "Odd one out", "options": ["Copper", "Silver", "Gold", "Plastic"], "correct": "Plastic"},
            {"text": "Odd one out", "options": ["BMW", "Audi", "Mercedes", "Boeing"], "correct": "Boeing"},
            {"text": "Odd one out", "options": ["Paris", "Rome", "Berlin", "Oxygen"], "correct": "Oxygen"},
            {"text": "Odd one out", "options": ["Soccer", "Tennis", "Chess", "Basketball"], "correct": "Chess"},
            {"text": "Odd one out", "options": ["Rose", "Tulip", "Lily", "Pine Tree"], "correct": "Pine Tree"},
            {"text": "Odd one out", "options": ["Car", "Bus", "Train", "Helicopter"], "correct": "Helicopter"},
            {"text": "Odd one out", "options": ["Hammer", "Screwdriver", "Wrench", "Plate"], "correct": "Plate"},
            {"text": "Odd one out", "options": ["Earth", "Mars", "Venus", "Sirius"], "correct": "Sirius"},
            {"text": "Odd one out", "options": ["Milk", "Cheese", "Butter", "Bread"], "correct": "Bread"},
            {"text": "Odd one out", "options": ["Dog", "Cat", "Wolf", "Penguin"], "correct": "Penguin"},
            {"text": "Odd one out", "options": ["Cabbage", "Lettuce", "Spinach", "Chicken"], "correct": "Chicken"},
            {"text": "Odd one out", "options": ["Mozart", "Beethoven", "Shakespeare", "Bach"], "correct": "Shakespeare"},
            {"text": "Odd one out", "options": ["Horse", "Donkey", "Camel", "Snake"], "correct": "Snake"},
            {"text": "Odd one out", "options": ["Tablet", "Laptop", "Smartphone", "Microwave"], "correct": "Microwave"},
            {"text": "Odd one out", "options": ["Tea", "Coffee", "Juice", "Iron"], "correct": "Iron"},
            {"text": "Odd one out", "options": ["Red", "Blue", "Green", "Triangle"], "correct": "Triangle"},
            {"text": "Odd one out", "options": ["Paris", "London", "New York", "Horse"], "correct": "Horse"},
            {"text": "Odd one out", "options": ["Football", "Rugby", "Cricket", "Laptop"], "correct": "Laptop"},
            {"text": "Odd one out", "options": ["Gold", "Silver", "Bronze", "Wood"], "correct": "Wood"},
            {"text": "Odd one out", "options": ["Knife", "Fork", "Spoon", "Television"], "correct": "Television"},
            {"text": "Odd one out", "options": ["Shirt", "Pants", "Shoes", "Helicopter"], "correct": "Helicopter"},
            {"text": "Odd one out", "options": ["Pen", "Pencil", "Marker", "Bottle"], "correct": "Bottle"},
            {"text": "Odd one out", "options": ["Carrot", "Potato", "Onion", "Fish"], "correct": "Fish"},
            {"text": "Odd one out", "options": ["Jeans", "T-Shirt", "Sweater", "Hamburger"], "correct": "Hamburger"},
            {"text": "Odd one out", "options": ["Guitar", "Piano", "Violin", "Refrigerator"], "correct": "Refrigerator"},
            {"text": "Odd one out", "options": ["Bread", "Rice", "Pasta", "Eraser"], "correct": "Eraser"},
            {"text": "Odd one out", "options": ["Bird", "Bat", "Eagle", "Hawk"], "correct": "Bat"},
            {"text": "Odd one out", "options": ["Rose", "Sunflower", "Daisy", "Hammer"], "correct": "Hammer"},
            {"text": "Odd one out", "options": ["Ice", "Steam", "Water", "Stone"], "correct": "Stone"},
            {"text": "Odd one out", "options": ["Pizza", "Pasta", "Burger", "Telescope"], "correct": "Telescope"},
            {"text": "Odd one out", "options": ["Chair", "Table", "Couch", "Tiger"], "correct": "Tiger"},
            {"text": "Odd one out", "options": ["Laptop", "Phone", "Mouse", "Banana"], "correct": "Banana"},
            {"text": "Odd one out", "options": ["Sun", "Moon", "Star", "Car"], "correct": "Car"},
            {"text": "Odd one out", "options": ["Salt", "Pepper", "Sugar", "Chair"], "correct": "Chair"},
            {"text": "Odd one out", "options": ["Shark", "Whale", "Dolphin", "Cow"], "correct": "Cow"},
            {"text": "Odd one out", "options": ["Blue", "Red", "Yellow", "Elephant"], "correct": "Elephant"},
            {"text": "Odd one out", "options": ["Cheetah", "Eagle", "Falcon", "Hawk"], "correct": "Cheetah"},
            {"text": "Odd one out", "options": ["Denmark", "Sweden", "Norway", "Brazil"], "correct": "Brazil"},
            {"text": "Odd one out", "options": ["Doctor", "Nurse", "Pilot", "Teacher"], "correct": "Pilot"},
            {"text": "Odd one out", "options": ["Iron Man", "Batman", "Superman", "Shrek"], "correct": "Shrek"},
            {"text": "Odd one out", "options": ["Tennis", "Badminton", "Volleyball", "Printer"], "correct": "Printer"},
            {"text": "Odd one out", "options": ["Cash", "Card", "Coins", "Chair"], "correct": "Chair"},
            {"text": "Odd one out", "options": ["Train", "Plane", "Boat", "Giraffe"], "correct": "Giraffe"},
            {"text": "Odd one out", "options": ["Apple", "Pear", "Orange", "Steak"], "correct": "Steak"},
            {"text": "Odd one out", "options": ["Water", "Juice", "Soda", "Screwdriver"], "correct": "Screwdriver"},
            {"text": "Odd one out", "options": ["Cat", "Dog", "Rabbit", "Shark"], "correct": "Shark"},
            {"text": "Odd one out", "options": ["Keyboard", "Mouse", "Monitor", "Pizza"], "correct": "Pizza"},
            {"text": "Odd one out", "options": ["Earth", "Mars", "Jupiter", "Apple"], "correct": "Apple"},
            {"text": "Odd one out", "options": ["Singer", "Dancer", "Actor", "Carpenter"], "correct": "Carpenter"},
            {"text": "Odd one out", "options": ["Nile", "Amazon", "Mississippi", "Mt. Everest"], "correct": "Mt. Everest"},
            {"text": "Odd one out", "options": ["Egg", "Chicken", "Duck", "Goat"], "correct": "Egg"},
            {"text": "Odd one out", "options": ["Horse", "Zebra", "Donkey", "Laptop"], "correct": "Laptop"},
            {"text": "Odd one out", "options": ["Socks", "Shoes", "Sandals", "Watermelon"], "correct": "Watermelon"},
            {"text": "Odd one out", "options": ["Sand", "Stone", "Soil", "Butter"], "correct": "Butter"},
            {"text": "Odd one out", "options": ["Car", "Bus", "Train", "Toaster"], "correct": "Toaster"},
            {"text": "Odd one out", "options": ["Grapes", "Strawberries", "Blueberries", "Chicken Wing"], "correct": "Chicken Wing"},
            {"text": "Odd one out", "options": ["Leaf", "Tree", "Branch", "Bottle"], "correct": "Bottle"},
            {"text": "Odd one out", "options": ["Frog", "Toad", "Salamander", "Shark"], "correct": "Shark"},
            {"text": "Odd one out", "options": ["Sparrow", "Pigeon", "Eagle", "Lion"], "correct": "Lion"},
            {"text": "Odd one out", "options": ["Keyboard", "Mouse", "CPU", "Spoon"], "correct": "Spoon"},
            {"text": "Odd one out", "options": ["Rice", "Bread", "Pasta", "Shampoo"], "correct": "Shampoo"},
            {"text": "Odd one out", "options": ["Clock", "Watch", "Timer", "Burger"], "correct": "Burger"},
            {"text": "Odd one out", "options": ["Swan", "Duck", "Goose", "Bat"], "correct": "Bat"},
            {"text": "Odd one out", "options": ["Blue", "Green", "Yellow", "Cat"], "correct": "Cat"},
            {"text": "Odd one out", "options": ["Iron", "Copper", "Silver", "Bread"], "correct": "Bread"},
            {"text": "Odd one out", "options": ["Pizza", "Burger", "Pasta", "Printer"], "correct": "Printer"},
            {"text": "Odd one out", "options": ["Hammer", "Saw", "Drill", "Pineapple"], "correct": "Pineapple"},
            {"text": "Odd one out", "options": ["Apple", "Peach", "Pear", "Potato"], "correct": "Potato"},
            {"text": "Odd one out", "options": ["Shark", "Whale", "Dolphin", "Eagle"], "correct": "Eagle"},
            {"text": "Odd one out", "options": ["Hat", "Scarf", "Gloves", "Laptop"], "correct": "Laptop"},
            {"text": "Odd one out", "options": ["Circle", "Square", "Rectangle", "Chocolate"], "correct": "Chocolate"},
            {"text": "Odd one out", "options": ["Coconut", "Banana", "Mango", "Car"], "correct": "Car"},
            {"text": "Odd one out", "options": ["Pen", "Pencil", "Crayon", "Fish"], "correct": "Fish"},
            {"text": "Odd one out", "options": ["Tiger", "Lion", "Panther", "Sheep"], "correct": "Sheep"},
            {"text": "Odd one out", "options": ["Coffee", "Tea", "Juice", "Stone"], "correct": "Stone"},
            {"text": "Odd one out", "options": ["Carrot", "Tomato", "Cucumber", "Shirt"], "correct": "Shirt"},
            {"text": "Odd one out", "options": ["Piano", "Guitar", "Drums", "Airplane"], "correct": "Airplane"},
            {"text": "Odd one out", "options": ["Notebook", "Pen", "Pencil", "Toaster"], "correct": "Toaster"},
            {"text": "Odd one out", "options": ["Shampoo", "Soap", "Conditioner", "Laptop"], "correct": "Laptop"},
            {"text": "Odd one out", "options": ["Broccoli", "Lettuce", "Cabbage", "Ice Cream"], "correct": "Ice Cream"},
            {"text": "Odd one out", "options": ["Train", "Bus", "Tram", "Tiger"], "correct": "Tiger"},
            {"text": "Odd one out", "options": ["Iron", "Steel", "Copper", "Bread"], "correct": "Bread"},
            {"text": "Odd one out", "options": ["Wolf", "Fox", "Dog", "Goldfish"], "correct": "Goldfish"},
            {"text": "Odd one out", "options": ["Socks", "Shoes", "Gloves", "Banana"], "correct": "Banana"},
            {"text": "Odd one out", "options": ["Keyboard", "Mouse", "Monitor", "Carrot"], "correct": "Carrot"},
            {"text": "Odd one out", "options": ["Helium", "Oxygen", "Nitrogen", "Cheese"], "correct": "Cheese"},
            {"text": "Odd one out", "options": ["Car", "Motorcycle", "Bicycle", "Toothbrush"], "correct": "Toothbrush"},
            {"text": "Odd one out", "options": ["Cup", "Plate", "Bowl", "Laptop"], "correct": "Laptop"},
            {"text": "Odd one out", "options": ["Moon", "Mars", "Jupiter", "Table"], "correct": "Table"},
            {"text": "Odd one out", "options": ["Chicken", "Beef", "Pork", "Apple"], "correct": "Apple"},
            {"text": "Odd one out", "options": ["Sweater", "Jacket", "Hat", "Hammer"], "correct": "Hammer"},
            {"text": "Odd one out", "options": ["Penguin", "Eagle", "Sparrow", "Camel"], "correct": "Camel"},
            {"text": "Odd one out", "options": ["Soap", "Toothpaste", "Shaving Cream", "Burger"], "correct": "Burger"},
            {"text": "Odd one out", "options": ["Giraffe", "Elephant", "Hippo", "Fan"], "correct": "Fan"},
            {"text": "Odd one out", "options": ["Salt", "Pepper", "Sugar", "Computer"], "correct": "Computer"},
            {"text": "Odd one out", "options": ["Flute", "Violin", "Trumpet", "Fork"], "correct": "Fork"},
            {"text": "Odd one out", "options": ["Bread", "Rice", "Noodles", "Hat"], "correct": "Hat"}
        ]
    }
    
    print("=" * 60)
    print("LOADING LEVEL 2 - ODD ONE OUT")
    print("=" * 60)
    
    # Get category
    try:
        category = QuizCategory.objects.get(slug='odd-one-out')
        print(f"\n✓ Found category: {category.name}")
        
        # Delete existing questions
        old_count = category.questions.count()
        category.questions.all().delete()
        print(f"🗑 Deleted {old_count} old questions")
        
    except QuizCategory.DoesNotExist:
        print("\n❌ Category 'odd-one-out' not found!")
        return
    
    created_count = 0
    skipped_count = 0
    
    for idx, q_data in enumerate(data['level_2'], 1):
        options = q_data['options']
        correct = q_data['correct']
        
        # Make unique text with question number and options
        text = f"Odd one out: {', '.join(options)}"
        
        # Create or get question
        question, created = QuizQuestion.objects.get_or_create(
            category=category,
            text=text,
            defaults={'is_active': True}
        )
        
        if created:
            # Create answers
            for order, option in enumerate(options):
                is_correct = (option == correct)
                QuizAnswer.objects.create(
                    question=question,
                    text=option,
                    is_correct=is_correct,
                    order=order
                )
            created_count += 1
        else:
            skipped_count += 1
    
    print(f"\n✓ Created {created_count} new questions")
    print(f"⚠ Skipped {skipped_count} existing questions")
    print(f"📊 Total Level 2 questions: {category.questions.count()}")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    load_level2()
