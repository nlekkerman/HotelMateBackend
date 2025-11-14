"""
Script to load Music multiple-choice questions into the quiz system
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


def load_music_questions():
    """Load Music questions from JSON file"""
    
    # Read the JSON file
    json_path = "music_questions.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get or create Music category
    category, created = QuizCategory.objects.get_or_create(
        slug='music',
        defaults={
            'name': 'Music',
            'description': 'Test your music knowledge',
            'icon': '🎵',
            'color': '#9333EA',
            'is_active': True,
            'display_order': 2
        }
    )
    
    if created:
        print("✅ Created Music category")
    else:
        print("✅ Music category already exists")
    
    # Load questions
    questions_created = 0
    questions_skipped = 0
    
    for idx, q_data in enumerate(data['questions'], 1):
        question_text = q_data['question']
        options = q_data['options']
        correct_answer_text = q_data['correct']
        
        # Check if question already exists
        existing = QuizQuestion.objects.filter(
            category=category,
            question_text=question_text
        ).exists()
        
        if existing:
            questions_skipped += 1
            continue
        
        # Determine difficulty based on position
        if idx % 3 == 0:
            difficulty = 'hard'
        elif idx % 2 == 0:
            difficulty = 'medium'
        else:
            difficulty = 'easy'
        
        # Find which option (A, B, C, D) is correct
        correct_letter = 'A'
        for i, option in enumerate(options):
            if option == correct_answer_text:
                correct_letter = chr(65 + i)  # A=65, B=66, C=67, D=68
                break
        
        # Create the question
        QuizQuestion.objects.create(
            category=category,
            question_text=question_text,
            difficulty=difficulty,
            option_a=options[0],
            option_b=options[1],
            option_c=options[2] if len(options) > 2 else '',
            option_d=options[3] if len(options) > 3 else '',
            correct_answer=correct_letter,
            explanation='',
            points=10,
            is_active=True
        )
        questions_created += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ Questions created: {questions_created}")
    print(f"⏭️  Questions skipped (already exist): {questions_skipped}")
    total = QuizQuestion.objects.filter(category=category).count()
    print(f"🎵 Total Music questions in database: {total}")
    print(f"\n🎯 Music category is ready!")


if __name__ == '__main__':
    print("🔄 Loading Music questions...")
    load_music_questions()
    print("✅ Done!")
