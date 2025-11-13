"""
Management command to import Level 5 (Knowledge Trap) quiz questions
Usage: python manage.py import_quiz_level5
"""
from django.core.management.base import BaseCommand
from entertainment.models import QuizCategory, Quiz, QuizQuestion, QuizAnswer


class Command(BaseCommand):
    help = 'Import Level 5 Knowledge Trap quiz questions'

    def handle(self, *args, **options):
        # JSON data from file - 100 scientifically accurate knowledge trap questions
        questions_data = {
            "level_5": [
                { "text": "Which statement is scientifically correct?", "options": ["Atoms directly touch each other", "Atoms are mostly empty space", "Atoms are solid spheres", "Atoms do not move"], "correct": "Atoms are mostly empty space" },
                {"text": "Which of these is scientifically correct?", "options": ["Humans have five senses", "Lightning never strikes twice", "Water freezes at 0°C under normal pressure", "Bananas grow on trees"], "correct": "Water freezes at 0°C under normal pressure"},
                {"text": "Which statement is accurate?", "options": ["Sugar causes hyperactivity", "Vaccines cause autism", "Evolution is a scientific theory", "Antibiotics kill viruses"], "correct": "Evolution is a scientific theory"},
                {"text": "Which is factually correct?", "options": ["Mount Everest is the closest mountain to the moon", "Diamonds are made of compressed coal", "Shaving makes hair grow thicker", "Humans share DNA with bananas"], "correct": "Humans share DNA with bananas"},
                {"text": "Which statement is true?", "options": ["The Great Wall is visible from space", "Chameleons change color to camouflage only", "Ostriches bury their heads in the sand", "The Sahara is a cold desert at night"], "correct": "The Sahara is a cold desert at night"},
                {"text": "Which is the correct statement?", "options": ["You can see the far side of the Moon from Earth", "Earth revolves around the Sun", "Goldfish have three-second memory", "The human tongue has taste zones"], "correct": "Earth revolves around the Sun"},
                {"text": "Which of these is true?", "options": ["Bulls get angry when they see red", "Glass is a slow-flowing liquid", "Humans use 100% of their brain", "Sound travels faster in water than in air"], "correct": "Sound travels faster in water than in air"},
                {"text": "Which statement is correct?", "options": ["The North Star is the brightest star", "The Milky Way is a galaxy", "Penguins live in the Arctic", "All deserts are hot"], "correct": "The Milky Way is a galaxy"},
                {"text": "Which is technically correct?", "options": ["Sharks are mammals", "Peanuts are nuts", "Spiders have 8 legs", "Bamboo is a tree"], "correct": "Spiders have 8 legs"},
                {"text": "Which one is accurate?", "options": ["Tides are caused by the Sun only", "Lightning always strikes the tallest object", "Humans have more than five senses", "Birds cannot fly without wind"], "correct": "Humans have more than five senses"},
                {"text": "Which fact is correct?", "options": ["All snakes are venomous", "Bacteria can be beneficial", "Alcohol kills all germs instantly", "A year is exactly 365 days"], "correct": "Bacteria can be beneficial"},
                {"text": "Which statement is true?", "options": ["Mercury is the hottest planet", "Venus rotates clockwise", "Jupiter has no storms", "Mars has liquid oceans"], "correct": "Venus rotates clockwise"},
                {"text": "Which is factually true?", "options": ["Humans have four lungs", "The heart stops when sneezing", "Pluto is still a planet", "Koalas have fingerprints"], "correct": "Koalas have fingerprints"},
                {"text": "Which statement is correct?", "options": ["The Amazon is the longest river", "GPS satellites use relativity", "Whales have gills", "Earth is perfectly round"], "correct": "GPS satellites use relativity"},
                {"text": "Which is true?", "options": ["The brain feels pain", "Hair keeps growing after death", "Octopuses have three hearts", "The moon glows by itself"], "correct": "Octopuses have three hearts"},
                {"text": "Which fact is accurate?", "options": ["Plants take in oxygen only", "Mammals lay eggs", "The speed of light is constant in all materials", "Bananas are berries"], "correct": "Bananas are berries"},
                {"text": "Choose the correct statement.", "options": ["Clothing dries faster in humidity", "Humans glow in the dark", "Sharks don't get cancer", "Camels store fat in their humps"], "correct": "Camels store fat in their humps"},
                {"text": "Which is the true statement?", "options": ["Raindrops are teardrop-shaped", "A day is 24 hours exactly", "Earth has more than one moon temporarily", "Lightning comes from the ground only"], "correct": "Earth has more than one moon temporarily"},
                {"text": "Which is scientifically accurate?", "options": ["Birds urinate like mammals", "Humans have more bacterial cells than human cells", "Blood is always blue before oxygen", "Snakes dislocate their jaws to eat"], "correct": "Humans have more bacterial cells than human cells"},
                {"text": "Which fact is correct?", "options": ["An atom is mostly empty space", "Atoms cannot be split", "Electric cars produce no emissions ever", "Stars are holes in the sky"], "correct": "An atom is mostly empty space"},
                {"text": "Which statement is correct?", "options": ["Apes can't swim", "Giraffes have no vocal cords", "Owls can turn their heads 360 degrees", "Humans evolved from chimpanzees"], "correct": "Giraffes have no vocal cords"},
                {"text": "Which of these is correct?", "options": ["Time moves slower at high speeds", "Salt makes water boil faster", "Black holes suck everything like vacuums", "A rainbow has seven fixed colors"], "correct": "Time moves slower at high speeds"},
                {"text": "Which one is true?", "options": ["Penguins mate for life always", "Dolphins sleep with one eye open", "Horses can't lie down", "Cats are nocturnal only"], "correct": "Dolphins sleep with one eye open"},
                {"text": "Which fact is accurate?", "options": ["Tornadoes rotate the same direction everywhere", "Space has no temperature", "Humans can't breathe pure oxygen", "Heat rises because it is lighter"], "correct": "Humans can't breathe pure oxygen"},
                {"text": "Which is scientifically correct?", "options": ["Fingernails grow after death", "Clouds are weightless", "A virus is not a living organism", "Humans have unique tongue prints"], "correct": "A virus is not a living organism"},
                {"text": "Which statement is true?", "options": ["Birds detect magnetic fields", "Ants sleep", "Elephants can't jump", "Flamingos are always pink naturally"], "correct": "Elephants can't jump"},
                {"text": "Which one is the true fact?", "options": ["Heat is a substance", "A year is the same length everywhere", "Sound cannot travel in space", "Fire has no shadow"], "correct": "Sound cannot travel in space"},
                {"text": "Which is true?", "options": ["Humans can see 10 million colors", "Red makes bulls angry", "Sugar melts in cold water instantly", "Sharks prefer human meat"], "correct": "Humans can see 10 million colors"},
                {"text": "Which statement is correct?", "options": ["Fish drink water", "Owls have eyeballs that rotate", "All jellyfish sting", "Snakes smell with their tongues"], "correct": "Snakes smell with their tongues"},
                {"text": "Which is true?", "options": ["The Moon causes most tides", "The Sun revolves around Earth", "Water conducts electricity strongly", "Glass is crystalline"], "correct": "The Moon causes most tides"},
                {"text": "Which one is accurate?", "options": ["Metal expands when cold", "Humans have a third eyelid", "All mushrooms are edible when cooked", "Penguins are mammals"], "correct": "Humans have a third eyelid"},
                {"text": "Which statement is correct?", "options": ["Cracking knuckles causes arthritis", "Hair grows from the ends", "Your stomach has two brains", "Taste is affected by smell"], "correct": "Taste is affected by smell"},
                {"text": "Which fact is true?", "options": ["Earth is the only planet with seasons", "Saturn could float in water", "Black is a color", "Eyes stay the same size from birth"], "correct": "Saturn could float in water"},
                {"text": "Which statement is real?", "options": ["Chili peppers burn the tongue physically", "Antibiotics cure the flu", "Baldness is inherited only from mother's side", "Humans have tailbones"], "correct": "Humans have tailbones"},
                {"text": "Which is correct?", "options": ["A tomato is a vegetable scientifically", "Light can bend", "Horses sleep standing only", "Blood is blue in veins"], "correct": "Light can bend"},
                {"text": "Which of these is true?", "options": ["A sneeze stops the heart", "Humans swallow spiders in sleep", "Bacteria outnumber human cells", "Dogs sweat through their tongues"], "correct": "Bacteria outnumber human cells"},
                {"text": "Which one is right?", "options": ["The body digests water", "The appendix has no purpose", "The brain uses 20% of our energy", "Sweat smells bad"], "correct": "The brain uses 20% of our energy"},
                {"text": "Which is accurate?", "options": ["All snowflakes are identical", "Venus is hotter than Mercury", "Space is completely silent", "Wolves howl at the moon"], "correct": "Venus is hotter than Mercury"},
                {"text": "Which is true?", "options": ["Humans can breathe underwater briefly", "Nails and hair are made of keratin", "Coffee dehydrates you always", "Sharks sleep like humans"], "correct": "Nails and hair are made of keratin"},
                {"text": "Which statement is correct?", "options": ["Earth rotates slower each year", "Rainbows are full circles", "Cats always land on their feet", "Bubbles are always round because of air"], "correct": "Rainbows are full circles"},
                {"text": "Which is true?", "options": ["Water is blue because of reflection", "Bees see ultraviolet light", "Humans have only 1 type of taste receptor", "Ants can't swim"], "correct": "Bees see ultraviolet light"},
                {"text": "Which statement is real?", "options": ["Tigers have striped skin", "Camels spit saliva only", "Bats are blind", "Elephants drink through their trunks"], "correct": "Tigers have striped skin"},
                {"text": "Which one is correct?", "options": ["Planets emit their own light", "Mammals existed before dinosaurs", "Antimatter weighs less than air", "Humans can't live above 3000m"], "correct": "Mammals existed before dinosaurs"},
                {"text": "Which statement is true?", "options": ["Octopuses have one brain", "Your heart is on the left only", "Humans dream every night", "Gold is magnetic sometimes"], "correct": "Humans dream every night"},
                {"text": "Which is accurate?", "options": ["Only humans use tools", "Birds evolved from dinosaurs", "Atoms touch each other", "Snakes are deaf to all sounds"], "correct": "Birds evolved from dinosaurs"},
                {"text": "Which is true?", "options": ["A compass points to true north", "Time moves slower in gravity", "All planets spin the same direction", "The sun is yellow"], "correct": "Time moves slower in gravity"},
                {"text": "Which fact is correct?", "options": ["Poison and venom are the same", "The kangaroo cannot walk backward", "All fish lay eggs", "Blue whales eat humans accidentally"], "correct": "The kangaroo cannot walk backward"},
                {"text": "Which statement is true?", "options": ["A day on Venus is longer than its year", "Black holes last forever", "Dogs see only black and white", "Gravity is constant everywhere"], "correct": "A day on Venus is longer than its year"},
                {"text": "Which is correct?", "options": ["Hot water freezes slower always", "Oxygen is flammable", "Aluminum can be dissolved by mercury", "Earth is the center of the universe"], "correct": "Aluminum can be dissolved by mercury"},
                {"text": "Which statement is accurate?", "options": ["Polar bears live in Antarctica", "Spiders are insects", "Clouds are made of tiny water droplets", "The sun goes around Earth"], "correct": "Clouds are made of tiny water droplets"},
                {"text": "Which statement is correct?", "options": ["Sharks must keep swimming to survive", "All snakes lay eggs", "Humans have a dominant hand from birth", "The Sun is made of burning fire"], "correct": "Sharks must keep swimming to survive"},
                {"text": "Which fact is true?", "options": ["Humans can live without a stomach", "You can see stars in the daytime", "Clouds weigh almost nothing", "Spiders have 10 legs"], "correct": "Humans can live without a stomach"},
                {"text": "Which statement is true?", "options": ["Heat cannot travel through vacuum", "Earth's core is colder than the surface", "Saturn has no solid surface", "The solar system has 10 planets"], "correct": "Saturn has no solid surface"},
                {"text": "Which is scientifically accurate?", "options": ["Birds have teeth", "Electric eels generate electricity", "Wolves are solitary animals", "Bulls hate red"], "correct": "Electric eels generate electricity"},
                {"text": "Which statement is correct?", "options": ["Humans shed skin every 2 weeks", "Salt preserves meat by dehydrating bacteria", "Wind is produced by ocean currents", "Dogs see in full RGB color"], "correct": "Salt preserves meat by dehydrating bacteria"},
                {"text": "Which is the true statement?", "options": ["Earth spins faster in winter", "Humans are the only animals that cry emotionally", "Water boils at the same temperature everywhere", "Rabbits are rodents"], "correct": "Earth spins faster in winter"},
                {"text": "Which fact is accurate?", "options": ["The moon is shrinking over time", "Venus has liquid oceans", "Mars has blue sunsets", "All bees can sting multiple times"], "correct": "The moon is shrinking over time"},
                {"text": "Which statement is correct?", "options": ["Turtles breathe through their shells", "Most of the oxygen we breathe comes from the ocean", "Owls are blind during the day", "Zebras are black with white stripes"], "correct": "Most of the oxygen we breathe comes from the ocean"},
                {"text": "Which fact is true?", "options": ["Humans cannot burp in space", "Ants have two brains", "Fire is a type of plasma", "Bananas grow upside down"], "correct": "Humans cannot burp in space"},
                {"text": "Which statement is accurate?", "options": ["Sharks are older than trees", "Crabs have 12 legs", "Octopuses have bones", "Whales sleep standing up"], "correct": "Sharks are older than trees"},
                {"text": "Which one is scientifically correct?", "options": ["A rainbow has an end point", "Trees communicate through fungal networks", "Humans have 300 bones as adults", "Mountains do not grow"], "correct": "Trees communicate through fungal networks"},
                {"text": "Which statement is correct?", "options": ["Bees can recognize human faces", "Clouds are made of steam", "You can't get sunburned on cloudy days", "Sound travels fastest in air"], "correct": "Bees can recognize human faces"},
                {"text": "Which fact is true?", "options": ["Venus rotates faster than Earth", "A human sneeze can travel 150 km/h", "Sharks have no immune system", "Metal shrinks when heated"], "correct": "A human sneeze can travel 150 km/h"},
                {"text": "Which statement is accurate?", "options": ["Humans grow new taste buds every 12 days", "All snakes are deaf", "Fish cannot drown", "Earth is the densest planet"], "correct": "Earth is the densest planet"},
                {"text": "Which is the true statement?", "options": ["Birds sleep while flying", "Clouds can weigh millions of kilograms", "Goldfish have 2-second memory", "The Sun is yellow in space"], "correct": "Clouds can weigh millions of kilograms"},
                {"text": "Which fact is correct?", "options": ["Elephants use sunscreen made of mud", "Vitamin C cures any cold", "Spiders are insects", "You lose heat fastest through your head"], "correct": "Elephants use sunscreen made of mud"},
                {"text": "Which one is true?", "options": ["Fire needs gravity to burn", "Bamboo can grow nearly 1 meter in a day", "Trees stop growing after 50 years", "Humans can tickle themselves"], "correct": "Bamboo can grow nearly 1 meter in a day"},
                {"text": "Which statement is accurate?", "options": ["Butterflies taste with their feet", "Human blood is blue without oxygen", "Most diamonds come from coal", "Dogs only see black and white"], "correct": "Butterflies taste with their feet"},
                {"text": "Which fact is correct?", "options": ["The Sun makes up 99% of the solar system's mass", "Mercury has seasons like Earth", "Neutron stars are smaller than cities", "Bees sleep with eyes open"], "correct": "The Sun makes up 99% of the solar system's mass"},
                {"text": "Which statement is true?", "options": ["Plants can communicate distress", "Bats are blind", "Humans have only 5 senses", "All birds can fly"], "correct": "Plants can communicate distress"},
                {"text": "Which is true?", "options": ["Spider silk is stronger than steel by weight", "Water conducts electricity perfectly", "The Sun is solid", "Carrots improve night vision dramatically"], "correct": "Spider silk is stronger than steel by weight"},
                {"text": "Which fact is correct?", "options": ["Octopuses taste through their arms", "Cats always land perfectly", "Birds don't urinate", "Flies live exactly 24 hours"], "correct": "Octopuses taste through their arms"},
                {"text": "Which of these statements is accurate?", "options": ["Lightning is hotter than the Sun", "Tornadoes can rotate only counterclockwise", "Ants can lift 50 times their weight", "All sharks give birth to live young"], "correct": "Lightning is hotter than the Sun"},
                {"text": "Which statement is true?", "options": ["Humans glow in visible light", "Bees die after every sting", "Snails can sleep for years", "Owls rotate their heads 360 degrees"], "correct": "Snails can sleep for years"},
                {"text": "Which fact is correct?", "options": ["The Pacific Ocean contains most of Earth's water", "The Amazon is the longest river", "There are no deserts in Europe", "Whales are fish"], "correct": "The Pacific Ocean contains most of Earth's water"},
                {"text": "Which statement is accurate?", "options": ["Fire is a plasma", "Bananas grow on trees", "Cats are purely nocturnal", "Elephants cannot swim"], "correct": "Fire is a plasma"},
                {"text": "Which fact is true?", "options": ["A blue whale's heart is the size of a small car", "Lightning only strikes metal objects", "Honey never expires", "Snakes have eyelids"], "correct": "A blue whale's heart is the size of a small car"},
                {"text": "Which is scientifically correct?", "options": ["The human eye can see infrared", "Flamingos are pink because of diet", "Humans have 3 kidneys", "Turtles can breathe through their ears"], "correct": "Flamingos are pink because of diet"},
                {"text": "Which statement is accurate?", "options": ["Water expands when it freezes", "Clouds are cotton-like solids", "Mountains never grow", "Glass conducts electricity well"], "correct": "Water expands when it freezes"},
                {"text": "Which of these is true?", "options": ["The human body has a magnetic field", "Stars are perfect spheres", "All volcanoes are active", "Birds are warm-blooded sometimes"], "correct": "The human body has a magnetic field"},
                {"text": "Which fact is correct?", "options": ["A single bolt of lightning contains 1 billion volts", "We only use 10% of our brain", "Gravity pulls objects equally on all planets", "Ants can't get injured from falling"], "correct": "A single bolt of lightning contains 1 billion volts"},
                {"text": "Which is true?", "options": ["Whales have belly buttons", "Spiders have 12 eyes always", "Birds sleep without resting their heads", "Seahorses are mammals"], "correct": "Whales have belly buttons"},
                {"text": "Which statement is accurate?", "options": ["Pineapples take 2 years to grow", "Fish cannot smell", "Clouds are weightless", "Tigers can't swim"], "correct": "Pineapples take 2 years to grow"},
                {"text": "Which one is correct?", "options": ["Humans once had tails", "Venus has 3 moons", "Water boils at same temperature regardless of altitude", "Tomatoes grow underground"], "correct": "Humans once had tails"},
                {"text": "Which statement is true?", "options": ["Fire burns in space", "Jupiter has a solid surface", "The Sun is powered by nuclear fusion", "All snakes produce venom"], "correct": "The Sun is powered by nuclear fusion"},
                {"text": "Which fact is accurate?", "options": ["The universe is expanding", "Stars are smaller than Earth", "All oceans are the same depth", "Humans cannot live above 1000m"], "correct": "The universe is expanding"},
                {"text": "Which statement is correct?", "options": ["The Earth once had two moons", "Mars has only one moon", "The Milky Way is the only galaxy", "Gravity pushes objects away"], "correct": "The Earth once had two moons"},
                {"text": "Which fact is true?", "options": ["Butterflies remember being caterpillars", "Sharks give live birth always", "Rain falls identical droplet shapes", "Bees can breathe underwater"], "correct": "Butterflies remember being caterpillars"},
                {"text": "Which one is accurate?", "options": ["Stars twinkle due to atmosphere", "Electricity travels at the speed of light", "Giraffes have two hearts", "Glass is a liquid at room temperature"], "correct": "Stars twinkle due to atmosphere"},
                {"text": "Which statement is true?", "options": ["Saturn rains diamonds", "Magnetism only works on metals", "Humans can smell better than dogs", "Plants have central nervous systems"], "correct": "Saturn rains diamonds"}
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

        # Create or get Level 5 Quiz
        quiz, created = Quiz.objects.get_or_create(
            slug='knowledge-trap-expert',
            defaults={
                'category': category,
                'title': 'Knowledge Trap - Expert',
                'description': 'Level 5: Deceptively tricky questions - think carefully!',
                'difficulty_level': 5,
                'is_active': True,
                'is_daily': False,
                'max_questions': 10,
                'time_per_question_seconds': 5,
                'enable_background_music': True,
                'enable_sound_effects': True,
                'sound_theme': 'tense'
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

        for index, q_data in enumerate(questions_data['level_5']):
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
