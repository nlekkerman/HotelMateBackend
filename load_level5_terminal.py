import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion, QuizAnswer

# Level 5 data
data = {
  "level_5": [
    { "text": "Which statement is scientifically correct?", "options": ["Atoms directly touch each other", "Atoms are mostly empty space", "Atoms are solid spheres", "Atoms do not move"], "correct": "Atoms are mostly empty space" },
    { "text": "Which fact is true?", "options": ["Venus rotates eastward", "Mercury rotates fastest", "Mars rotates clockwise", "Jupiter rotates eastward"], "correct": "Venus rotates eastward" },
    { "text": "Which statement is accurate?", "options": ["Octopuses have one heart", "Octopuses have three hearts", "Octopuses have four hearts", "Octopuses have no hearts"], "correct": "Octopuses have three hearts" },
    { "text": "Which statement is correct?", "options": ["Bananas grow on trees", "Bananas grow on giant herbs", "Bananas grow on vines", "Bananas grow underground"], "correct": "Bananas grow on giant herbs" },
    { "text": "Which one is true?", "options": ["Sharks are mammals", "Sharks have no bones", "Sharks breathe air", "Sharks lay their eggs on land"], "correct": "Sharks have no bones" },
    { "text": "Which statement is accurate?", "options": ["Humans have only 5 senses", "Humans have more than 5 senses", "Humans have 3 senses", "Humans have exactly 7 senses"], "correct": "Humans have more than 5 senses" },
    { "text": "Which fact is correct?", "options": ["Lightning is hotter than the Sun", "Lightning is cooler than ice", "Lightning is room temperature", "Lightning is the same temperature as fire"], "correct": "Lightning is hotter than the Sun" },
    { "text": "Which statement is true?", "options": ["Time moves slower at high speed", "Time moves faster at high speed", "Time never changes", "Time flows the same everywhere"], "correct": "Time moves slower at high speed" },
    { "text": "Which is correct?", "options": ["Humans use 100% of the brain", "Humans always use 10% of the brain", "Different brain regions activate at different times", "We use only one hemisphere at a time"], "correct": "Different brain regions activate at different times" },
    { "text": "Which fact is accurate?", "options": ["Koalas have fingerprints", "Koalas have hooves", "Koalas have scales", "Koalas have no fingerprints"], "correct": "Koalas have fingerprints" },
    { "text": "Which statement is correct?", "options": ["Glass is a slow-moving liquid", "Glass is an amorphous solid", "Glass is crystalline", "Glass is fully liquid"], "correct": "Glass is an amorphous solid" },
    { "text": "Which is true?", "options": ["Fire is a plasma", "Fire is a liquid", "Fire is a solid", "Fire is a gas"], "correct": "Fire is a plasma" },
    { "text": "Which fact is accurate?", "options": ["Sound cannot travel in a vacuum", "Sound travels fastest in air", "Sound travels fastest in a vacuum", "Sound travels only in liquids"], "correct": "Sound cannot travel in a vacuum" },
    { "text": "Which is correct?", "options": ["A year is exactly 365 days", "A year is approximately 365.25 days", "A year is exactly 364 days", "A year is 367 days"], "correct": "A year is approximately 365.25 days" },
    { "text": "Which statement is true?", "options": ["Water expands when frozen", "Water shrinks when frozen", "Water keeps the same volume when frozen", "Water becomes denser when frozen"], "correct": "Water expands when frozen" },
    { "text": "Which fact is real?", "options": ["The Moon produces its own light", "The Moon reflects sunlight", "The Moon glows from radiation", "The Moon glows due to heat"], "correct": "The Moon reflects sunlight" },
    { "text": "Which fact is correct?", "options": ["Clouds weigh millions of kilograms", "Clouds weigh nothing", "Clouds weigh one kilogram", "Clouds are weightless gas"], "correct": "Clouds weigh millions of kilograms" },
    { "text": "Which is true?", "options": ["Humans glow in visible light", "Humans glow in infrared light", "Humans do not emit any light", "Humans glow in ultraviolet"], "correct": "Humans glow in infrared light" },
    { "text": "Which statement is accurate?", "options": ["Saturn could float in water", "Jupiter could float in water", "Earth could float in water", "Mercury could float in water"], "correct": "Saturn could float in water" },
    { "text": "Which is scientifically correct?", "options": ["A day on Venus is longer than a Venusian year", "A Venus year is longer than a Venus day", "They are equal", "Venus does not rotate"], "correct": "A day on Venus is longer than a Venusian year" },
    { "text": "Which statement is factual?", "options": ["Heat rises because it is lighter", "Heat rises because warm air expands", "Heat rises because gravity pushes it", "Heat rises because cold air is magnetic"], "correct": "Heat rises because warm air expands" },
    { "text": "Which is true?", "options": ["The Sun is yellow in space", "The Sun is white in space", "The Sun is red in space", "The Sun is blue in space"], "correct": "The Sun is white in space" },
    { "text": "Which fact is accurate?", "options": ["A sneeze can reach 150 km/h", "A sneeze can break bones", "A sneeze is 10 km/h", "A sneeze is 1 km/h"], "correct": "A sneeze can reach 150 km/h" },
    { "text": "Which statement is correct?", "options": ["All snakes lay eggs", "Some snakes give live birth", "No snakes lay eggs", "Snakes hatch internally only"], "correct": "Some snakes give live birth" },
    { "text": "Which fact is true?", "options": ["Trees communicate chemically", "Trees communicate verbally", "Trees do not communicate", "Trees communicate electrically"], "correct": "Trees communicate chemically" },
    { "text": "Which statement is accurate?", "options": ["Spider silk is stronger than steel by weight", "Spider silk is weaker than wood", "Spider silk dissolves in water", "Spider silk is metallic"], "correct": "Spider silk is stronger than steel by weight" },
    { "text": "Which is true?", "options": ["Vitamin C cures all colds", "Vitamin C prevents viruses", "Vitamin C supports immune function", "Vitamin C heals wounds instantly"], "correct": "Vitamin C supports immune function" },
    { "text": "Which one is correct?", "options": ["Coal forms diamonds", "Diamonds form from carbon over time under pressure", "Diamonds form from quartz", "Diamonds form from gold"], "correct": "Diamonds form from carbon over time under pressure" },
    { "text": "Which is factual?", "options": ["Bees see ultraviolet light", "Bees see infrared light", "Bees see no colors", "Bees see only black and white"], "correct": "Bees see ultraviolet light" },
    { "text": "Which is accurate?", "options": ["Black holes suck everything", "Black holes warp spacetime", "Black holes are holes in matter", "Black holes are empty spheres"], "correct": "Black holes warp spacetime" },
    { "text": "Which statement is correct?", "options": ["Humans have 300 bones as adults", "Humans have 206 bones as adults", "Humans have 150 bones as adults", "Humans have 250 bones as adults"], "correct": "Humans have 206 bones as adults" },
    { "text": "Which fact is accurate?", "options": ["Stars twinkle due to space distortion", "Stars twinkle due to Earth's atmosphere", "Stars twinkle because they flicker", "Stars twinkle due to solar winds"], "correct": "Stars twinkle due to Earth's atmosphere" },
    { "text": "Which is true?", "options": ["The Pacific Ocean contains the majority of Earth's water", "The Atlantic contains most water", "The Indian contains most water", "No ocean contains most water"], "correct": "The Pacific Ocean contains the majority of Earth's water" },
    { "text": "Which is correct?", "options": ["Bats are blind", "Bats have excellent vision", "Bats cannot see at all", "Bats see only in UV"], "correct": "Bats have excellent vision" },
    { "text": "Which fact is real?", "options": ["Humans cannot burp in space", "Humans can burp normally in space", "Humans can burp twice as loud in space", "Burping causes motion in space"], "correct": "Humans cannot burp in space" },
    { "text": "Which is true?", "options": ["Butterflies taste with their wings", "Butterflies taste with their feet", "Butterflies taste with antennas", "Butterflies cannot taste"], "correct": "Butterflies taste with their feet" },
    { "text": "Which statement is correct?", "options": ["Trees stop growing after 50 years", "Trees can grow as long as they live", "Trees shrink with age", "Trees grow only in summer"], "correct": "Trees can grow as long as they live" },
    { "text": "Which is accurate?", "options": ["The universe is static", "The universe is expanding", "The universe is shrinking", "The universe is oscillating constantly"], "correct": "The universe is expanding" },
    { "text": "Which is true?", "options": ["Humans cannot live without stomachs", "Humans can live without stomachs", "Stomach removal is impossible", "The stomach is the most vital organ"], "correct": "Humans can live without stomachs" },
    { "text": "Which fact is correct?", "options": ["Pineapples grow on trees", "Pineapples grow from the ground on plants", "Pineapples grow underground", "Pineapples grow on vines"], "correct": "Pineapples grow from the ground on plants" },
    { "text": "Which statement is true?", "options": ["Electric eels store electricity like batteries", "Electric eels generate electricity biologically", "Electric eels use friction to charge", "Electric eels absorb electricity"], "correct": "Electric eels generate electricity biologically" },
    { "text": "Which is accurate?", "options": ["Humans can see infrared naturally", "Humans cannot see infrared naturally", "Humans naturally see UV", "Humans see radio waves"], "correct": "Humans cannot see infrared naturally" },
    { "text": "Which fact is real?", "options": ["Tigers have striped fur only", "Tigers have striped skin and fur", "Tigers have plain skin", "Tiger skin is spotted"], "correct": "Tigers have striped skin and fur" },
    { "text": "Which statement is correct?", "options": ["Snails are insects", "Snails are mollusks", "Snails are crustaceans", "Snails are fish"], "correct": "Snails are mollusks" },
    { "text": "Which is true?", "options": ["Trees breathe oxygen only", "Trees produce oxygen and absorb CO₂", "Trees breathe nitrogen", "Trees do not exchange gases"], "correct": "Trees produce oxygen and absorb CO₂" },
    { "text": "Which is accurate?", "options": ["Ants sleep like humans", "Ants do not sleep in a human-like cycle", "Ants never sleep", "Ants sleep for 12 hours"], "correct": "Ants do not sleep in a human-like cycle" },
    { "text": "Which is scientifically correct?", "options": ["Stars are eternal", "Stars have life cycles", "Stars do not die", "Stars expand forever"], "correct": "Stars have life cycles" },
    { "text": "Which statement is real?", "options": ["Humans shed skin every 2 weeks", "Humans shed skin constantly over a month", "Humans shed skin yearly", "Humans do not shed skin"], "correct": "Humans shed skin constantly over a month" },
    { "text": "Which fact is correct?", "options": ["Heat cannot travel through space", "Heat can travel through space by radiation", "Heat travels only through solids", "Heat travels only by conduction"], "correct": "Heat can travel through space by radiation" },
    { "text": "Which is accurate?", "options": ["Birds evolved from reptiles", "Birds evolved from mammals", "Birds evolved from amphibians", "Birds evolved from fish"], "correct": "Birds evolved from reptiles" },
    { "text": "Which statement is true?", "options": ["Water boils at 100°C everywhere", "Boiling point depends on altitude", "Water always boils higher in mountains", "Water boils hotter in space"], "correct": "Boiling point depends on altitude" },
    { "text": "Which fact is real?", "options": ["Mercury has no atmosphere", "Mercury has a thin exosphere", "Mercury has a thick atmosphere", "Mercury has a methane atmosphere"], "correct": "Mercury has a thin exosphere" },
    { "text": "Which statement is correct?", "options": ["Neutron stars are larger than cities", "Neutron stars can be 20 km across", "Neutron stars are the size of Earth", "Neutron stars are as large as Jupiter"], "correct": "Neutron stars can be 20 km across" },
    { "text": "Which is true?", "options": ["Whales are fish", "Whales breathe air", "Whales breathe water", "Whales lay eggs"], "correct": "Whales breathe air" },
    { "text": "Which fact is accurate?", "options": ["Bones are non-living", "Bones are living tissue", "Bones are dead structures", "Bones are crystals"], "correct": "Bones are living tissue" },
    { "text": "Which is correct?", "options": ["Gravity is identical everywhere", "Gravity varies by mass and distance", "Gravity is constant on all planets", "Gravity does not exist in space"], "correct": "Gravity varies by mass and distance" },
    { "text": "Which statement is real?", "options": ["Evolution happens within one lifetime", "Evolution happens over generations", "Evolution stops at adulthood", "Evolution is instant"], "correct": "Evolution happens over generations" },
    { "text": "Which is factual?", "options": ["Hurricanes rotate the same direction everywhere", "Hurricanes rotate differently by hemisphere", "Hurricanes do not rotate", "Hurricanes rotate toward the equator"], "correct": "Hurricanes rotate differently by hemisphere" },
    { "text": "Which is true?", "options": ["Human blood is blue inside veins", "Human blood is always red", "Human blood changes color with oxygen", "Blood is purple before oxygen"], "correct": "Human blood is always red" },
    { "text": "Which fact is accurate?", "options": ["Water conducts electricity well by itself", "Pure water is a poor conductor", "Pure water is highly conductive", "Water conducts only when boiling"], "correct": "Pure water is a poor conductor" },
    { "text": "Which is correct?", "options": ["Earth has two moons", "Earth has one permanent moon", "Earth has no moons", "Earth has three moons"], "correct": "Earth has one permanent moon" },
    { "text": "Which fact is real?", "options": ["The Milky Way is the only galaxy", "There are billions of galaxies", "There are 10 galaxies total", "Galaxies do not exist"], "correct": "There are billions of galaxies" },
    { "text": "Which statement is accurate?", "options": ["Electrons orbit like planets", "Electrons exist in probability clouds", "Electrons are fixed in place", "Electrons move in straight lines"], "correct": "Electrons exist in probability clouds" },
    { "text": "Which is true?", "options": ["Flies live 24 hours", "Flies can live for weeks", "Flies live for years", "Flies live 1 hour"], "correct": "Flies can live for weeks" },
    { "text": "Which fact is accurate?", "options": ["Mosquitoes bite for food", "Mosquitoes bite to feed eggs", "Mosquitoes bite for hydration", "Mosquitoes bite to spread disease"], "correct": "Mosquitoes bite to feed eggs" },
    { "text": "Which is correct?", "options": ["Some mammals lay eggs", "No mammals lay eggs", "All mammals lay eggs", "Mammals lay eggs only when cold"], "correct": "Some mammals lay eggs" },
    { "text": "Which statement is true?", "options": ["Black is a wavelength of light", "Black is the absence of visible light", "Black is a mixture of all colors", "Black is ultraviolet"], "correct": "Black is the absence of visible light" },
    { "text": "Which is accurate?", "options": ["Trees produce most of Earth's oxygen", "Oceans produce most oxygen", "Animals produce most oxygen", "Mountains produce oxygen"], "correct": "Oceans produce most oxygen" },
    { "text": "Which statement is factual?", "options": ["Iron is magnetic", "Gold is magnetic", "Silver is magnetic", "Copper is magnetic"], "correct": "Iron is magnetic" },
    { "text": "Which is true?", "options": ["Some frogs freeze solid and survive", "All frogs die if frozen", "Frogs cannot freeze", "Frozen frogs turn to ice permanently"], "correct": "Some frogs freeze solid and survive" },
    { "text": "Which fact is real?", "options": ["Hydrogen is the most abundant element", "Oxygen is the most abundant", "Carbon is the most abundant", "Iron is the most abundant"], "correct": "Hydrogen is the most abundant element" },
    { "text": "Which fact is correct?", "options": ["Termites are ants", "Termites are more closely related to cockroaches", "Termites are beetles", "Termites are flies"], "correct": "Termites are more closely related to cockroaches" },
    { "text": "Which statement is accurate?", "options": ["Snakes smell with their tongues", "Snakes smell with their eyes", "Snakes smell with their skin", "Snakes smell with their lungs"], "correct": "Snakes smell with their tongues" },
    { "text": "Which is true?", "options": ["Birds have teeth", "Birds have no teeth", "Birds grow teeth when old", "Birds swallow with teeth-like bones"], "correct": "Birds have no teeth" },
    { "text": "Which fact is correct?", "options": ["Electricity travels at light speed always", "Electrical signals in wires travel slower", "Electricity moves as fast as sound", "Electricity is instant"], "correct": "Electrical signals in wires travel slower" },
    { "text": "Which is accurate?", "options": ["Human hair is dead protein", "Human hair is living tissue", "Hair contains nerves", "Hair feels pain"], "correct": "Human hair is dead protein" },
    { "text": "Which statement is correct?", "options": ["Earth's magnetic field never changes", "Earth's magnetic poles can flip", "Earth has no magnetic field", "Magnets cause earthquakes"], "correct": "Earth's magnetic poles can flip" },
    { "text": "Which is factual?", "options": ["The ozone layer blocks UV radiation", "The ozone layer blocks infrared", "The ozone layer blocks visible light", "The ozone layer blocks oxygen"], "correct": "The ozone layer blocks UV radiation" },
    { "text": "Which is true?", "options": ["Orcas are dolphins", "Orcas are whales", "Orcas are fish", "Orcas are sharks"], "correct": "Orcas are dolphins" },
    { "text": "Which fact is accurate?", "options": ["Humidity makes sweat evaporate faster", "Humidity slows sweat evaporation", "Humidity has no effect", "Humidity stops sweating"], "correct": "Humidity slows sweat evaporation" },
    { "text": "Which statement is correct?", "options": ["DNA is arranged as a double helix", "DNA is arranged in a perfect cube", "DNA is a flat spiral", "DNA is a single straight line"], "correct": "DNA is arranged as a double helix" },
    { "text": "Which fact is true?", "options": ["Skin is the largest organ in the human body", "The liver is the largest organ by area", "The brain is the largest organ", "The heart is the largest organ"], "correct": "Skin is the largest organ in the human body" },
    { "text": "Which statement is accurate?", "options": ["Enzymes are proteins that speed up reactions", "Enzymes are types of sugars", "Enzymes are a kind of fat", "Enzymes are minerals"], "correct": "Enzymes are proteins that speed up reactions" },
    { "text": "Which is scientifically correct?", "options": ["Coral reefs are made of plants", "Corals are animals", "Corals are rocks", "Corals are bacteria"], "correct": "Corals are animals" },
    { "text": "Which fact is real?", "options": ["Plate tectonics cause many earthquakes", "Earthquakes are caused only by weather", "Earthquakes are caused by tides", "Earthquakes are caused by volcanoes only"], "correct": "Plate tectonics cause many earthquakes" },
    { "text": "Which statement is true?", "options": ["Helium is lighter than air", "Helium is heavier than air", "Helium is the same density as air", "Helium cannot float"], "correct": "Helium is lighter than air" },
    { "text": "Which is accurate?", "options": ["Greenhouse gases trap heat in the atmosphere", "Greenhouse gases cool the planet", "Greenhouse gases are harmless and inert", "Greenhouse gases block all sunlight"], "correct": "Greenhouse gases trap heat in the atmosphere" },
    { "text": "Which fact is correct?", "options": ["Carbon dioxide is a greenhouse gas", "Nitrogen is the main greenhouse gas", "Helium is the main greenhouse gas", "Neon is the main greenhouse gas"], "correct": "Carbon dioxide is a greenhouse gas" },
    { "text": "Which statement is factual?", "options": ["Viruses need host cells to reproduce", "Viruses reproduce independently like bacteria", "Viruses are just small bacteria", "Viruses are a type of fungus"], "correct": "Viruses need host cells to reproduce" },
    { "text": "Which is true?", "options": ["Bacteria can reproduce by binary fission", "Bacteria reproduce only with eggs", "Bacteria reproduce by seeds", "Bacteria do not reproduce"], "correct": "Bacteria can reproduce by binary fission" },
    { "text": "Which statement is correct?", "options": ["The speed of light in vacuum is constant", "The speed of light changes randomly in vacuum", "The speed of light in vacuum depends on color", "The speed of light in vacuum depends on gravity only"], "correct": "The speed of light in vacuum is constant" },
    { "text": "Which fact is accurate?", "options": ["A vacuum has no air molecules", "A vacuum is full of compressed air", "A vacuum is just very thin air", "A vacuum is made of nitrogen"], "correct": "A vacuum has no air molecules" },
    { "text": "Which statement is true?", "options": ["Helium balloons rise because of buoyant force", "Helium balloons rise because of magnetism", "Helium balloons rise due to electricity", "Helium balloons rise due to gravity pulling them up"], "correct": "Helium balloons rise because of buoyant force" },
    { "text": "Which is scientifically correct?", "options": ["An eclipse happens when one celestial body blocks light from another", "An eclipse is when stars disappear permanently", "An eclipse happens when planets collide", "An eclipse is just a cloud shadow"], "correct": "An eclipse happens when one celestial body blocks light from another" },
    { "text": "Which fact is real?", "options": ["The iris controls how much light enters the eye", "The cornea controls image color", "The lens controls the heartbeat", "The pupil controls eye pressure"], "correct": "The iris controls how much light enters the eye" },
    { "text": "Which statement is accurate?", "options": ["White light is a mix of many colors", "White light is colorless and pure", "White light contains only blue", "White light contains only red and green"], "correct": "White light is a mix of many colors" },
    { "text": "Which is true?", "options": ["Rainbows are formed by refraction and reflection of light in water droplets", "Rainbows are painted in the sky by dust", "Rainbows are projected by the Sun directly", "Rainbows are caused by magnetic fields"], "correct": "Rainbows are formed by refraction and reflection of light in water droplets" },
    { "text": "Which fact is correct?", "options": ["Insulin helps regulate blood sugar levels", "Insulin digests fats in the stomach", "Insulin is only a painkiller", "Insulin controls body temperature"], "correct": "Insulin helps regulate blood sugar levels" },
    { "text": "Which statement is real?", "options": ["Red blood cells carry oxygen using hemoglobin", "Red blood cells carry hormones only", "Red blood cells produce electricity", "Red blood cells store fat"], "correct": "Red blood cells carry oxygen using hemoglobin" },
    { "text": "Which is accurate?", "options": ["The mitochondrion is often called the powerhouse of the cell", "The nucleus is called the powerhouse of the cell", "The ribosome is the powerhouse of the cell", "The cell membrane is the powerhouse of the cell"], "correct": "The mitochondrion is often called the powerhouse of the cell" }
  ]
}

def load_level5():
    # Get or create the category
    category, created = QuizCategory.objects.get_or_create(
        slug='knowledge-trap',
        defaults={
            'name': 'Knowledge Trap',
            'description': 'Test your knowledge with tricky scientific facts',
            'difficulty_level': 5,
            'time_limit': 15,
            'points_per_question': 5
        }
    )
    
    if created:
        print(f"✓ Created category: {category.name}")
    else:
        print(f"ℹ Category already exists: {category.name}")
    
    # Delete existing questions
    deleted_count = category.questions.all().delete()[0]
    print(f"🗑 Deleted {deleted_count} old questions")
    
    # Load new questions
    questions = data['level_5']
    created_count = 0
    
    for q_data in questions:
        # Create question
        question = QuizQuestion.objects.create(
            category=category,
            text=q_data['text']
        )
        
        # Create answers
        for option in q_data['options']:
            QuizAnswer.objects.create(
                question=question,
                text=option,
                is_correct=(option == q_data['correct'])
            )
        
        created_count += 1
    
    print(f"✓ Created {created_count} new questions")
    print(f"📊 Total Level 5 questions: {category.questions.count()}")

if __name__ == '__main__':
    load_level5()
