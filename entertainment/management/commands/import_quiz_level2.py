"""
Management command to import Level 2 (Odd One Out) quiz questions
Usage: python manage.py import_quiz_level2
"""
from django.core.management.base import BaseCommand
from entertainment.models import QuizCategory, Quiz, QuizQuestion, QuizAnswer


class Command(BaseCommand):
    help = 'Import Level 2 Odd One Out quiz questions'

    def handle(self, *args, **options):
        # JSON data from file
        questions_data = {
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

        # Get or create category
        category, _ = QuizCategory.objects.get_or_create(
            name="General Knowledge",
            defaults={
                'description': 'Test your general knowledge across various topics',
                'is_active': True
            }
        )

        # Create or get Level 2 Quiz
        quiz, created = Quiz.objects.get_or_create(
            slug='odd-one-out-moderate',
            defaults={
                'category': category,
                'title': 'Odd One Out - Moderate',
                'description': 'Level 2: Find the item that does not belong',
                'difficulty_level': 2,
                'is_active': True,
                'is_daily': False,
                'max_questions': 10,
                'time_per_question_seconds': 18,
                'enable_background_music': True,
                'enable_sound_effects': True,
                'sound_theme': 'default'
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created quiz: {quiz.title}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Quiz already exists: {quiz.title}')
            )

        # Import questions
        questions_imported = 0
        questions_skipped = 0

        for index, q_data in enumerate(questions_data['level_2']):
            # Create unique text by adding options context
            unique_text = f"{q_data['text']}: {', '.join(q_data['options'][:2])}"
            
            # Check if question already exists
            existing = QuizQuestion.objects.filter(
                quiz=quiz,
                order=index
            ).first()

            if existing:
                questions_skipped += 1
                continue

            # Create question
            question = QuizQuestion.objects.create(
                quiz=quiz,
                text=unique_text,
                order=index,
                base_points=10,
                is_active=True
            )

            # Create answers
            for answer_index, option in enumerate(q_data['options']):
                QuizAnswer.objects.create(
                    question=question,
                    text=option,
                    is_correct=(option == q_data['correct']),
                    order=answer_index
                )

            questions_imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Import complete!'
                f'\n  - Questions imported: {questions_imported}'
                f'\n  - Questions skipped (already exist): {questions_skipped}'
                f'\n  - Total questions in quiz: {quiz.questions.count()}'
            )
        )
