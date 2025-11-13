"""
Load Level 3 (Fill the Blank) questions
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion, QuizAnswer


def load_level3():
    data = {
        "level_3": [
            {"text": "The famous Italian city destroyed by Mount Vesuvius was ______.", "options": ["Pompeii", "Rome", "Naples", "Verona"], "correct": "Pompeii"},
            {"text": "The continent where the Amazon rainforest is located is ______.", "options": ["Africa", "Asia", "South America", "Australia"], "correct": "South America"},
            {"text": "The economic system based on private ownership and market competition is called ______.", "options": ["Socialism", "Feudalism", "Capitalism", "Communism"], "correct": "Capitalism"},
            {"text": "The scale commonly used to measure the magnitude of earthquakes is the ______ scale.", "options": ["Richter", "Beaufort", "Mercalli", "Fahrenheit"], "correct": "Richter"},
            {"text": "The Greek philosopher who taught Alexander the Great was ______.", "options": ["Socrates", "Plato", "Aristotle", "Pythagoras"], "correct": "Aristotle"},
            {"text": "The hormone that regulates blood sugar levels is ______.", "options": ["Adrenaline", "Insulin", "Thyroxine", "Estrogen"], "correct": "Insulin"},
            {"text": "The city that hosts the headquarters of the European Central Bank is ______.", "options": ["Brussels", "Frankfurt", "Paris", "Luxembourg"], "correct": "Frankfurt"},
            {"text": "The main metal in steel is ______.", "options": ["Copper", "Aluminium", "Iron", "Zinc"], "correct": "Iron"},
            {"text": "The Italian word commonly used in music to mean \"fast\" is ______.", "options": ["Adagio", "Largo", "Allegro", "Andante"], "correct": "Allegro"},
            {"text": "The process by which a liquid changes into a gas at its surface is called ______.", "options": ["Condensation", "Evaporation", "Sublimation", "Melting"], "correct": "Evaporation"},
            {"text": "The longest side of a right-angled triangle is called the ______.", "options": ["Radius", "Diameter", "Hypotenuse", "Median"], "correct": "Hypotenuse"},
            {"text": "The Middle Eastern dish made from mashed chickpeas, tahini, and lemon is ______.", "options": ["Falafel", "Tabbouleh", "Hummus", "Shawarma"], "correct": "Hummus"},
            {"text": "The scientist who developed the first successful polio vaccine was Jonas ______.", "options": ["Salk", "Pasteur", "Fleming", "Curie"], "correct": "Salk"},
            {"text": "The raw material used to make glass is mainly ______.", "options": ["Clay", "Sand", "Limestone", "Granite"], "correct": "Sand"},
            {"text": "The layer of skin where hair follicles and sweat glands are found is the ______.", "options": ["Epidermis", "Dermis", "Hypodermis", "Cuticle"], "correct": "Dermis"},
            {"text": "The device commonly used today to navigate using satellite signals is a ______.", "options": ["Radar", "GPS receiver", "Compass", "Altimeter"], "correct": "GPS receiver"},
            {"text": "The science of designing equipment and devices that fit the human body is called ______.", "options": ["Ecology", "Ergonomics", "Geology", "Kinesiology"], "correct": "Ergonomics"},
            {"text": "______ is the capital of France.", "options": ["Paris", "Rome", "Berlin", "Madrid"], "correct": "Paris"},
            {"text": "The chemical symbol for sodium is ____.", "options": ["Na", "So", "Sn", "Sd"], "correct": "Na"},
            {"text": "The largest planet in our solar system is ______.", "options": ["Earth", "Jupiter", "Saturn", "Neptune"], "correct": "Jupiter"},
            {"text": "The process by which plants make food is called ______.", "options": ["Respiration", "Fermentation", "Photosynthesis", "Digestion"], "correct": "Photosynthesis"},
            {"text": "The currency used in Japan is the ______.", "options": ["Yen", "Won", "Dollar", "Euro"], "correct": "Yen"},
            {"text": "The Great Wall is located in ______.", "options": ["India", "China", "Mongolia", "Japan"], "correct": "China"},
            {"text": "The organ that pumps blood through the body is the ______.", "options": ["Liver", "Lung", "Heart", "Kidney"], "correct": "Heart"},
            {"text": "The freezing point of water at sea level is ______ degrees Celsius.", "options": ["0", "10", "32", "100"], "correct": "0"},
            {"text": "The writer of 'Romeo and Juliet' is William ______.", "options": ["Dickens", "Shakespeare", "Hemingway", "Austen"], "correct": "Shakespeare"},
            {"text": "The smallest unit of life is the ______.", "options": ["Atom", "Tissue", "Cell", "Organ"], "correct": "Cell"},
            {"text": "The desert that covers much of northern Africa is the ______.", "options": ["Gobi", "Sahara", "Mojave", "Kalahari"], "correct": "Sahara"},
            {"text": "Albert ______ developed the theory of relativity.", "options": ["Darwin", "Einstein", "Tesla", "Newton"], "correct": "Einstein"},
            {"text": "The chemical symbol for gold is ______.", "options": ["G", "Go", "Au", "Ag"], "correct": "Au"},
            {"text": "The hardest natural substance on Earth is ______.", "options": ["Steel", "Diamond", "Granite", "Iron"], "correct": "Diamond"},
            {"text": "The river that flows through Cairo is the ______.", "options": ["Amazon", "Danube", "Nile", "Rhine"], "correct": "Nile"},
            {"text": "The largest ocean on Earth is the ______ Ocean.", "options": ["Atlantic", "Indian", "Pacific", "Arctic"], "correct": "Pacific"},
            {"text": "The gas most abundant in Earth's atmosphere is ______.", "options": ["Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen"], "correct": "Nitrogen"},
            {"text": "Light travels fastest in a ______.", "options": ["Vacuum", "Water", "Glass", "Air"], "correct": "Vacuum"},
            {"text": "The largest continent on Earth is ______.", "options": ["Africa", "Asia", "Europe", "South America"], "correct": "Asia"},
            {"text": "The Italian city famous for its canals is ______.", "options": ["Florence", "Venice", "Milan", "Rome"], "correct": "Venice"},
            {"text": "The three primary colors of light are red, green, and ______.", "options": ["Blue", "Yellow", "Purple", "Orange"], "correct": "Blue"},
            {"text": "The organ responsible for filtering blood in the human body is the ______.", "options": ["Stomach", "Kidney", "Pancreas", "Bladder"], "correct": "Kidney"},
            {"text": "The study of past human life and culture through artifacts is called ______.", "options": ["Anthropology", "Sociology", "Archaeology", "Geology"], "correct": "Archaeology"},
            {"text": "The country famous for the Eiffel Tower is ______.", "options": ["Italy", "Germany", "France", "Spain"], "correct": "France"},
            {"text": "The longest river in the world is traditionally considered the ______.", "options": ["Nile", "Amazon", "Yangtze", "Mississippi"], "correct": "Nile"},
            {"text": "The primary language spoken in Brazil is ______.", "options": ["Spanish", "Portuguese", "French", "English"], "correct": "Portuguese"},
            {"text": "The scientist who proposed the laws of motion was Isaac ______.", "options": ["Darwin", "Newton", "Kepler", "Maxwell"], "correct": "Newton"},
            {"text": "The largest internal organ in the human body is the ______.", "options": ["Heart", "Liver", "Lung", "Stomach"], "correct": "Liver"},
            {"text": "The art style characterized by swirling night skies in 'Starry Night' is ______.", "options": ["Cubism", "Impressionism", "Post-Impressionism", "Surrealism"], "correct": "Post-Impressionism"},
            {"text": "The chemical formula for water is ______.", "options": ["CO2", "H2O", "O2", "NaCl"], "correct": "H2O"},
            {"text": "The tallest mountain above sea level is Mount ______.", "options": ["Everest", "K2", "Kilimanjaro", "Denali"], "correct": "Everest"},
            {"text": "The structure in cells that contains genetic material is the ______.", "options": ["Mitochondrion", "Nucleus", "Ribosome", "Golgi Apparatus"], "correct": "Nucleus"},
            {"text": "The chemical symbol for iron is ______.", "options": ["Ir", "In", "Fe", "I"], "correct": "Fe"},
            {"text": "The European city split by the Danube and known for Buda and Pest is ______.", "options": ["Prague", "Vienna", "Budapest", "Bucharest"], "correct": "Budapest"},
            {"text": "The Italian painter of the ceiling of the Sistine Chapel was ______.", "options": ["Raphael", "Donatello", "Michelangelo", "Caravaggio"], "correct": "Michelangelo"},
            {"text": "The musical period of Mozart and Haydn is known as the ______ era.", "options": ["Baroque", "Classical", "Romantic", "Modern"], "correct": "Classical"},
            {"text": "The Earth orbits around the ______.", "options": ["Moon", "Sun", "Mars", "Jupiter"], "correct": "Sun"},
            {"text": "The longest bone in the human body is the ______.", "options": ["Humerus", "Femur", "Tibia", "Radius"], "correct": "Femur"},
            {"text": "The smallest country in the world by area is ______.", "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"], "correct": "Vatican City"},
            {"text": "The city known as the 'Big Apple' is ______.", "options": ["Los Angeles", "New York", "Chicago", "Miami"], "correct": "New York"},
            {"text": "The soft tissue that fills most bones is called bone ______.", "options": ["Liquid", "Marrow", "Fiber", "Matrix"], "correct": "Marrow"},
            {"text": "The branch of science dealing with matter and energy is ______.", "options": ["Biology", "Chemistry", "Physics", "Geography"], "correct": "Physics"},
            {"text": "The main gas we exhale after breathing in oxygen is ______.", "options": ["Nitrogen", "Carbon Dioxide", "Helium", "Methane"], "correct": "Carbon Dioxide"},
            {"text": "The primary organ involved in detoxifying chemicals is the ______.", "options": ["Heart", "Lung", "Liver", "Spleen"], "correct": "Liver"},
            {"text": "The person who leads an orchestra is called a ______.", "options": ["Soloist", "Conductor", "Composer", "Director"], "correct": "Conductor"},
            {"text": "The large landmass that includes France, Germany, and Italy is ______.", "options": ["Asia", "Europe", "Africa", "Oceania"], "correct": "Europe"},
            {"text": "The three states of matter are solid, liquid, and ______.", "options": ["Gas", "Plasma", "Vapor", "Foam"], "correct": "Gas"},
            {"text": "The chemical symbol for carbon is ______.", "options": ["C", "Ca", "Cb", "Co"], "correct": "C"},
            {"text": "The organ that primarily controls balance is located in the ______.", "options": ["Brain", "Inner Ear", "Spine", "Feet"], "correct": "Inner Ear"},
            {"text": "The language most widely spoken worldwide is ______.", "options": ["English", "Mandarin Chinese", "Spanish", "Hindi"], "correct": "Mandarin Chinese"},
            {"text": "The boiling point of water at sea level is ______ degrees Celsius.", "options": ["50", "90", "100", "120"], "correct": "100"},
            {"text": "The region of space where gravity prevents even light from escaping is a ______.", "options": ["Star", "Galaxy", "Black Hole", "Nebula"], "correct": "Black Hole"},
            {"text": "The piece of gym equipment used for running in place is a ______.", "options": ["Rower", "Treadmill", "Stepper", "Bench"], "correct": "Treadmill"},
            {"text": "The animal often associated with Wall Street is the ______.", "options": ["Lion", "Bull", "Wolf", "Bear"], "correct": "Bull"},
            {"text": "The human body's main source of immediate energy is ______.", "options": ["Protein", "Fat", "Carbohydrate", "Water"], "correct": "Carbohydrate"},
            {"text": "The musical symbol indicating silence is a ______.", "options": ["Note", "Clef", "Rest", "Sharp"], "correct": "Rest"},
            {"text": "The star at the center of our solar system is called the ______.", "options": ["Pole Star", "Sun", "Sirius", "Vega"], "correct": "Sun"},
            {"text": "The boundary between two tectonic plates is called a ______.", "options": ["Fault", "Fold", "Ridge", "Trench"], "correct": "Fault"},
            {"text": "The movement of people from rural areas to cities is known as urban ______.", "options": ["Decline", "Migration", "Stagnation", "Fragmentation"], "correct": "Migration"},
            {"text": "The Japanese art of paper folding is called ______.", "options": ["Ikebana", "Origami", "Kintsugi", "Sumi-e"], "correct": "Origami"},
            {"text": "The blood vessels that carry blood away from the heart are called ______.", "options": ["Veins", "Arteries", "Capillaries", "Ducts"], "correct": "Arteries"},
            {"text": "The layer of gases surrounding Earth is called the ______.", "options": ["Biosphere", "Atmosphere", "Lithosphere", "Hydrosphere"], "correct": "Atmosphere"},
            {"text": "The fear of confined spaces is called ______.", "options": ["Acrophobia", "Claustrophobia", "Arachnophobia", "Agoraphobia"], "correct": "Claustrophobia"},
            {"text": "The famous scientist who wrote 'On the Origin of Species' was Charles ______.", "options": ["Darwin", "Wallace", "Lamarck", "Linnaeus"], "correct": "Darwin"},
            {"text": "The fluid that circulates through the heart and vessels is called ______.", "options": ["Water", "Lymph", "Blood", "Plasma"], "correct": "Blood"},
            {"text": "The Italian dish made from layers of pasta, sauce, and cheese is ______.", "options": ["Risotto", "Lasagna", "Gnocchi", "Carbonara"], "correct": "Lasagna"},
            {"text": "The device used to measure atmospheric pressure is a ______.", "options": ["Thermometer", "Barometer", "Altimeter", "Manometer"], "correct": "Barometer"},
            {"text": "The organ that produces insulin in the body is the ______.", "options": ["Liver", "Pancreas", "Kidney", "Spleen"], "correct": "Pancreas"},
            {"text": "The ancient civilization that built Machu Picchu was the ______.", "options": ["Aztec", "Mayan", "Inca", "Olmec"], "correct": "Inca"},
            {"text": "The lines that run parallel to the equator are called lines of ______.", "options": ["Longitude", "Latitude", "Altitude", "Magnitude"], "correct": "Latitude"},
            {"text": "The Scandinavian country with fjords and Viking history is ______.", "options": ["Denmark", "Norway", "Finland", "Iceland"], "correct": "Norway"},
            {"text": "The phenomenon of bending light as it passes from one medium to another is called ______.", "options": ["Reflection", "Refraction", "Diffraction", "Dispersion"], "correct": "Refraction"},
            {"text": "The chemical symbol for oxygen is ______.", "options": ["Ox", "O", "Og", "On"], "correct": "O"},
            {"text": "The person responsible for keeping financial records of a company is an ______.", "options": ["Attorney", "Accountant", "Architect", "Analyst"], "correct": "Accountant"},
            {"text": "The structure that connects muscle to bone is called a ______.", "options": ["Ligament", "Tendon", "Cartilage", "Fascia"], "correct": "Tendon"},
            {"text": "The country that is also a continent is ______.", "options": ["Canada", "Russia", "Australia", "India"], "correct": "Australia"},
            {"text": "The layer of Earth we live on is called the ______.", "options": ["Core", "Mantle", "Crust", "Lithosphere"], "correct": "Crust"},
            {"text": "The liquid part of blood in which cells are suspended is called ______.", "options": ["Serum", "Plasma", "Lymph", "Bile"], "correct": "Plasma"},
            {"text": "The substance in red blood cells that carries oxygen is ______.", "options": ["Chlorophyll", "Hemoglobin", "Myosin", "Insulin"], "correct": "Hemoglobin"},
            {"text": "The distance light travels in one year is called a light ______.", "options": ["Minute", "Hour", "Year", "Second"], "correct": "Year"},
            {"text": "The smallest whole unit of an element that still retains its properties is an ______.", "options": ["Ion", "Molecule", "Atom", "Cell"], "correct": "Atom"},
            {"text": "The historic wall dividing East and West until 1989 was the ______ Wall.", "options": ["China", "Berlin", "Hadrian's", "Wailing"], "correct": "Berlin"},
            {"text": "The middle layer of the Earth between crust and core is the ______.", "options": ["Mantle", "Shell", "Ring", "Band"], "correct": "Mantle"}
        ]
    }
    
    print("=" * 60)
    print("LOADING LEVEL 3 - FILL THE BLANK")
    print("=" * 60)
    
    try:
        category = QuizCategory.objects.get(slug='fill-the-blank')
        print(f"\n✓ Found category: {category.name}")
        
        old_count = category.questions.count()
        category.questions.all().delete()
        print(f"🗑 Deleted {old_count} old questions")
        
    except QuizCategory.DoesNotExist:
        print("\n❌ Category 'fill-the-blank' not found!")
        return
    
    created_count = 0
    
    for q_data in data['level_3']:
        text = q_data['text']
        options = q_data['options']
        correct = q_data['correct']
        
        question = QuizQuestion.objects.create(
            category=category,
            text=text,
            is_active=True
        )
        
        for order, option in enumerate(options):
            is_correct = (option == correct)
            QuizAnswer.objects.create(
                question=question,
                text=option,
                is_correct=is_correct,
                order=order
            )
        created_count += 1
    
    print(f"\n✓ Created {created_count} new questions")
    print(f"📊 Total Level 3 questions: {category.questions.count()}")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    load_level3()
