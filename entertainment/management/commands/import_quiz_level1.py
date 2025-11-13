"""
Management command to import Level 1 (Classic Trivia) quiz questions
Usage: python manage.py import_quiz_level1
"""
import json
from django.core.management.base import BaseCommand
from entertainment.models import QuizCategory, Quiz, QuizQuestion, QuizAnswer


class Command(BaseCommand):
    help = 'Import Level 1 Classic Trivia quiz questions'

    def handle(self, *args, **options):
        # JSON data from file
        questions_data = {
            "level_1": [
                {"text": "What is the capital of Canada?", "options": ["Toronto", "Vancouver", "Ottawa", "Montreal"], "correct": "Ottawa"},
                {"text": "Which planet is closest to the Sun?", "options": ["Earth", "Mercury", "Venus", "Mars"], "correct": "Mercury"},
                {"text": "What is the largest mammal?", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippo"], "correct": "Blue Whale"},
                {"text": "How many days are in a leap year?", "options": ["364", "365", "366", "367"], "correct": "366"},
                {"text": "What country invented pizza?", "options": ["France", "Italy", "Spain", "Greece"], "correct": "Italy"},
                {"text": "What is the hardest natural substance?", "options": ["Gold", "Iron", "Diamond", "Platinum"], "correct": "Diamond"},
                {"text": "Who painted the Mona Lisa?", "options": ["Da Vinci", "Picasso", "Van Gogh", "Michelangelo"], "correct": "Da Vinci"},
                {"text": "Which sea creature has three hearts?", "options": ["Shark", "Octopus", "Dolphin", "Seal"], "correct": "Octopus"},
                {"text": "What gas do plants absorb?", "options": ["Oxygen", "Carbon Dioxide", "Nitrogen", "Helium"], "correct": "Carbon Dioxide"},
                {"text": "What is the tallest mountain in the world?", "options": ["K2", "Everest", "Kangchenjunga", "Makalu"], "correct": "Everest"},
                {"text": "Who wrote 'Harry Potter'?", "options": ["J.R.R. Tolkien", "J.K. Rowling", "George R.R. Martin", "Lewis Carroll"], "correct": "J.K. Rowling"},
                {"text": "How many continents are there?", "options": ["5", "6", "7", "8"], "correct": "7"},
                {"text": "Which element has the chemical symbol O?", "options": ["Gold", "Oxygen", "Osmium", "Zinc"], "correct": "Oxygen"},
                {"text": "Which animal is known as the King of the Jungle?", "options": ["Tiger", "Lion", "Panther", "Jaguar"], "correct": "Lion"},
                {"text": "What is Japan's capital?", "options": ["Tokyo", "Osaka", "Kyoto", "Hiroshima"], "correct": "Tokyo"},
                {"text": "How many players in a soccer team on the field?", "options": ["9", "10", "11", "12"], "correct": "11"},
                {"text": "What is the boiling point of water?", "options": ["50°C", "90°C", "100°C", "120°C"], "correct": "100°C"},
                {"text": "What is the largest desert?", "options": ["Sahara", "Antarctica", "Gobi", "Arabian"], "correct": "Antarctica"},
                {"text": "Where is the Eiffel Tower located?", "options": ["Rome", "Madrid", "Paris", "Berlin"], "correct": "Paris"},
                {"text": "What do bees make?", "options": ["Wax", "Milk", "Honey", "Oil"], "correct": "Honey"},
                {"text": "Which planet is known as the Red Planet?", "options": ["Jupiter", "Mars", "Venus", "Saturn"], "correct": "Mars"},
                {"text": "What is the largest ocean?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "correct": "Pacific"},
                {"text": "What instrument has black and white keys?", "options": ["Guitar", "Harp", "Piano", "Flute"], "correct": "Piano"},
                {"text": "What is the currency of the UK?", "options": ["Euro", "Dollar", "Pound", "Franc"], "correct": "Pound"},
                {"text": "Which blood type is known as the universal donor?", "options": ["A", "B", "AB", "O-"], "correct": "O-"},
                {"text": "How many bones are in the adult human body?", "options": ["199", "206", "214", "120"], "correct": "206"},
                {"text": "What does DNA stand for?", "options": ["Deoxyribonucleic Acid", "Dinuclear Acid", "Digital Nucleic Acid", "Dextro Acid"], "correct": "Deoxyribonucleic Acid"},
                {"text": "What is Earth's only natural satellite?", "options": ["Moon", "Europa", "Phobos", "Titan"], "correct": "Moon"},
                {"text": "Which organ pumps blood?", "options": ["Lungs", "Stomach", "Heart", "Kidneys"], "correct": "Heart"},
                {"text": "What animal is the symbol of peace?", "options": ["Eagle", "Dove", "Falcon", "Owl"], "correct": "Dove"},
                {"text": "The Great Wall is in which country?", "options": ["India", "China", "Japan", "Korea"], "correct": "China"},
                {"text": "What is the square root of 64?", "options": ["6", "7", "8", "9"], "correct": "8"},
                {"text": "What fruit keeps the doctor away?", "options": ["Banana", "Apple", "Orange", "Pear"], "correct": "Apple"},
                {"text": "Which metal is liquid at room temperature?", "options": ["Gold", "Iron", "Mercury", "Copper"], "correct": "Mercury"},
                {"text": "Which country hosts the Taj Mahal?", "options": ["India", "Pakistan", "Nepal", "Bangladesh"], "correct": "India"},
                {"text": "How many hours in a day?", "options": ["20", "22", "24", "26"], "correct": "24"},
                {"text": "Which bird can't fly?", "options": ["Eagle", "Sparrow", "Penguin", "Crow"], "correct": "Penguin"},
                {"text": "Which superhero lives in Gotham?", "options": ["Superman", "Batman", "Iron Man", "Flash"], "correct": "Batman"},
                {"text": "What animal says 'moo'?", "options": ["Sheep", "Cow", "Dog", "Duck"], "correct": "Cow"},
                {"text": "What is frozen water called?", "options": ["Ice", "Steam", "Snow", "Frost"], "correct": "Ice"},
                {"text": "Which continent is Egypt in?", "options": ["Asia", "Europe", "Africa", "South America"], "correct": "Africa"},
                {"text": "How many minutes in an hour?", "options": ["30", "45", "60", "90"], "correct": "60"},
                {"text": "What planet do we live on?", "options": ["Mars", "Earth", "Venus", "Saturn"], "correct": "Earth"},
                {"text": "What color are bananas?", "options": ["Green", "Red", "Yellow", "Purple"], "correct": "Yellow"},
                {"text": "Who discovered gravity?", "options": ["Einstein", "Newton", "Tesla", "Darwin"], "correct": "Newton"},
                {"text": "What shape has three sides?", "options": ["Square", "Triangle", "Circle", "Pentagon"], "correct": "Triangle"},
                {"text": "How many legs do spiders have?", "options": ["6", "8", "10", "12"], "correct": "8"},
                {"text": "What device measures temperature?", "options": ["Barometer", "Thermometer", "Altimeter", "Hygrometer"], "correct": "Thermometer"},
                {"text": "What food do pandas eat?", "options": ["Bamboo", "Bananas", "Grass", "Leaves"], "correct": "Bamboo"},
                {"text": "Where is the Colosseum?", "options": ["Paris", "Athens", "Rome", "Istanbul"], "correct": "Rome"},
                {"text": "How many letters are in the English alphabet?", "options": ["20", "25", "26", "28"], "correct": "26"},
                {"text": "Which animal is the largest land mammal?", "options": ["Rhino", "Elephant", "Hippo", "Buffalo"], "correct": "Elephant"},
                {"text": "What do cows drink?", "options": ["Milk", "Juice", "Water", "Soda"], "correct": "Water"},
                {"text": "What's the capital of Spain?", "options": ["Barcelona", "Madrid", "Seville", "Valencia"], "correct": "Madrid"},
                {"text": "Which planet has rings?", "options": ["Earth", "Mars", "Saturn", "Venus"], "correct": "Saturn"},
                {"text": "What galaxy is Earth in?", "options": ["Andromeda", "Milky Way", "Whirlpool", "Sombrero"], "correct": "Milky Way"},
                {"text": "Which organ helps you breathe?", "options": ["Brain", "Lungs", "Heart", "Liver"], "correct": "Lungs"},
                {"text": "What kind of animal is Nemo?", "options": ["Shark", "Clownfish", "Dolphin", "Octopus"], "correct": "Clownfish"},
                {"text": "What is 5 × 5?", "options": ["20", "25", "30", "35"], "correct": "25"},
                {"text": "Which country is famous for sushi?", "options": ["Japan", "China", "Thailand", "Korea"], "correct": "Japan"},
                {"text": "What is the tallest land animal?", "options": ["Elephant", "Giraffe", "Horse", "Camel"], "correct": "Giraffe"},
                {"text": "Which insect makes honey?", "options": ["Bee", "Ant", "Fly", "Wasps"], "correct": "Bee"},
                {"text": "What is the capital of Germany?", "options": ["Munich", "Berlin", "Frankfurt", "Hamburg"], "correct": "Berlin"},
                {"text": "What is 10 + 15?", "options": ["20", "25", "30", "35"], "correct": "25"},
                {"text": "Which country has the Great Barrier Reef?", "options": ["USA", "Australia", "Brazil", "India"], "correct": "Australia"},
                {"text": "Which organ filters blood?", "options": ["Heart", "Liver", "Kidneys", "Stomach"], "correct": "Kidneys"},
                {"text": "What gas do humans breathe out?", "options": ["Oxygen", "Carbon Dioxide", "Hydrogen", "Nitrogen"], "correct": "Carbon Dioxide"},
                {"text": "Who was the first man on the Moon?", "options": ["Buzz Aldrin", "Neil Armstrong", "Yuri Gagarin", "Michael Collins"], "correct": "Neil Armstrong"},
                {"text": "How many wheels does a car usually have?", "options": ["2", "3", "4", "6"], "correct": "4"},
                {"text": "Which animal is known for its black and white stripes?", "options": ["Tiger", "Zebra", "Skunk", "Panda"], "correct": "Zebra"},
                {"text": "What is the smallest prime number?", "options": ["0", "1", "2", "3"], "correct": "2"},
                {"text": "Which country is known for the pyramids?", "options": ["Peru", "Greece", "Egypt", "Mexico"], "correct": "Egypt"},
                {"text": "What is the capital of Australia?", "options": ["Sydney", "Melbourne", "Canberra", "Perth"], "correct": "Canberra"},
                {"text": "What is the main ingredient in guacamole?", "options": ["Avocado", "Cucumber", "Lime", "Peas"], "correct": "Avocado"},
                {"text": "What is the chemical symbol for gold?", "options": ["G", "Ag", "Au", "Go"], "correct": "Au"},
                {"text": "How many strings does a standard guitar have?", "options": ["4", "5", "6", "7"], "correct": "6"},
                {"text": "Which planet is known for its rings?", "options": ["Mars", "Jupiter", "Saturn", "Neptune"], "correct": "Saturn"},
                {"text": "Which country hosted the 2016 Olympics?", "options": ["China", "Brazil", "UK", "Russia"], "correct": "Brazil"},
                {"text": "What is the largest internal organ in the human body?", "options": ["Heart", "Liver", "Lungs", "Stomach"], "correct": "Liver"},
                {"text": "What type of animal is a Komodo dragon?", "options": ["Mammal", "Reptile", "Fish", "Bird"], "correct": "Reptile"},
                {"text": "Which country produces the most coffee?", "options": ["Colombia", "Brazil", "Ethiopia", "Vietnam"], "correct": "Brazil"},
                {"text": "What is the capital of Portugal?", "options": ["Rome", "Lisbon", "Madrid", "Valencia"], "correct": "Lisbon"},
                {"text": "Which gas makes balloons float?", "options": ["Oxygen", "Hydrogen", "Helium", "Nitrogen"], "correct": "Helium"},
                {"text": "How many sides does a hexagon have?", "options": ["5", "6", "7", "8"], "correct": "6"},
                {"text": "Which animal is the fastest bird?", "options": ["Falcon", "Eagle", "Ostrich", "Hawk"], "correct": "Falcon"},
                {"text": "What is the process plants use to make food?", "options": ["Respiration", "Photosynthesis", "Digestion", "Fermentation"], "correct": "Photosynthesis"},
                {"text": "Which country invented the Olympics?", "options": ["Italy", "Egypt", "Greece", "Turkey"], "correct": "Greece"},
                {"text": "Which sea separates Europe and Africa?", "options": ["Atlantic", "Mediterranean", "Red Sea", "Black Sea"], "correct": "Mediterranean"},
                {"text": "Which bird lays the largest eggs?", "options": ["Duck", "Eagle", "Ostrich", "Goose"], "correct": "Ostrich"},
                {"text": "How many hearts does an octopus have?", "options": ["1", "2", "3", "4"], "correct": "3"},
                {"text": "What is the capital of Sweden?", "options": ["Oslo", "Stockholm", "Copenhagen", "Helsinki"], "correct": "Stockholm"},
                {"text": "What is the longest river in the world?", "options": ["Amazon", "Nile", "Yangtze", "Congo"], "correct": "Nile"},
                {"text": "What is sushi traditionally wrapped in?", "options": ["Rice paper", "Seaweed", "Lettuce", "Plastic"], "correct": "Seaweed"},
                {"text": "How many teeth does an adult human have?", "options": ["28", "30", "32", "34"], "correct": "32"},
                {"text": "What is the main language spoken in Brazil?", "options": ["Spanish", "Portuguese", "French", "English"], "correct": "Portuguese"},
                {"text": "Which country is the largest by land area?", "options": ["USA", "China", "Russia", "Canada"], "correct": "Russia"},
                {"text": "Which planet is known as Earth's twin?", "options": ["Mars", "Venus", "Jupiter", "Mercury"], "correct": "Venus"},
                {"text": "What animal is known for its hump?", "options": ["Camel", "Giraffe", "Horse", "Buffalo"], "correct": "Camel"},
                {"text": "How many months have 31 days?", "options": ["5", "6", "7", "8"], "correct": "7"},
                {"text": "What is the main gas in the Earth's atmosphere?", "options": ["Oxygen", "Nitrogen", "Hydrogen", "CO₂"], "correct": "Nitrogen"}
            ]
        }

        # Create or get category
        category, _ = QuizCategory.objects.get_or_create(
            name="General Knowledge",
            defaults={
                'description': 'Test your general knowledge across various topics',
                'is_active': True
            }
        )

        # Create or get Level 1 Quiz
        quiz, created = Quiz.objects.get_or_create(
            slug='classic-trivia-easy',
            defaults={
                'category': category,
                'title': 'Classic Trivia - Easy',
                'description': 'Level 1: Easy general trivia questions for all ages',
                'difficulty_level': 1,
                'is_active': True,
                'is_daily': False,
                'max_questions': 10,
                'time_per_question_seconds': 20,
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

        for index, q_data in enumerate(questions_data['level_1']):
            # Check if question already exists
            existing = QuizQuestion.objects.filter(
                quiz=quiz,
                text=q_data['text']
            ).first()

            if existing:
                questions_skipped += 1
                continue

            # Create question
            question = QuizQuestion.objects.create(
                quiz=quiz,
                text=q_data['text'],
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
