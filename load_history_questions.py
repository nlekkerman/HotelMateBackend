"""
Script to load History true/false questions into the quiz system
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion

def load_history_questions():
    """Load History questions from JSON file"""
    
    # Read the JSON file
    json_path = "history_questions.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get or create History category
    category, created = QuizCategory.objects.get_or_create(
        slug='history',
        defaults={
            'name': 'History',
            'description': 'Test your knowledge of historical events',
            'icon': '📚',
            'color': '#8B4513',
            'is_active': True,
            'display_order': 1
        }
    )
    
    if created:
        print(f"✅ Created History category")
    else:
        print(f"✅ History category already exists")
    
    # Load questions
    questions_created = 0
    questions_skipped = 0
    
    for idx, q_data in enumerate(data['questions'], 1):
        question_text = q_data['question']
        is_correct = q_data['correct']
        
        # Check if question already exists
        existing = QuizQuestion.objects.filter(
            category=category,
            question_text=question_text
        ).exists()
        
        if existing:
            questions_skipped += 1
            continue
        
        # Determine difficulty based on position (mix them up)
        if idx % 3 == 0:
            difficulty = 'hard'
        elif idx % 2 == 0:
            difficulty = 'medium'
        else:
            difficulty = 'easy'
        
        # Create the question with True/False options
        QuizQuestion.objects.create(
            category=category,
            question_text=question_text,
            difficulty=difficulty,
            option_a='True',
            option_b='False',
            option_c='',  # Empty for true/false questions
            option_d='',  # Empty for true/false questions
            correct_answer='A' if is_correct else 'B',
            explanation='',
            points=10,
            is_active=True
        )
        questions_created += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ Questions created: {questions_created}")
    print(f"⏭️  Questions skipped (already exist): {questions_skipped}")
    print(f"📚 Total History questions in database: {QuizQuestion.objects.filter(category=category).count()}")
    print(f"\n🎯 History category is ready!")

if __name__ == '__main__':
    print("🔄 Loading History questions...")
    load_history_questions()
    print("✅ Done!")
