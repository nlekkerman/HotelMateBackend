"""
Load quiz questions from JSON files and populate database
Run this after setup_quiz_game.py
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion, QuizAnswer

def load_questions_from_json(file_path, category_slug):
    """Load questions from JSON file and add to category"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return 0
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {file_path}: {e}")
        return 0
    
    # Get category
    try:
        category = QuizCategory.objects.get(slug=category_slug)
    except QuizCategory.DoesNotExist:
        print(f"❌ Category not found: {category_slug}")
        return 0
    
    # Find the questions array in the JSON
    questions_data = None
    for key in data.keys():
        if isinstance(data[key], list):
            questions_data = data[key]
            break
    
    if not questions_data:
        print(f"❌ No questions array found in {file_path}")
        return 0
    
    created_count = 0
    for q_data in questions_data:
        text = q_data.get('text', '')
        options = q_data.get('options', [])
        correct = q_data.get('correct', '')
        
        if not text or not options or not correct:
            continue
        
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
    
    return created_count


def main():
    print("=" * 60)
    print("LOADING QUIZ QUESTIONS FROM JSON FILES")
    print("=" * 60)
    
    # Define file mappings - Load one at a time
    files_to_load = [
        {
            'file': r'fixed_json\level_two_fixed.json',
            'category': 'odd-one-out',
            'name': 'Odd One Out (Level 2)'
        }
    ]
    
    total_created = 0
    
    for file_info in files_to_load:
        print(f"\n📁 Loading {file_info['name']}...")
        print(f"   File: {file_info['file']}")
        
        count = load_questions_from_json(
            file_info['file'],
            file_info['category']
        )
        
        if count > 0:
            print(f"   ✓ Created {count} questions")
            total_created += count
        else:
            print(f"   ⚠ No questions created")
    
    # Summary
    print("\n" + "=" * 60)
    print("LOADING COMPLETE!")
    print("=" * 60)
    
    for cat in QuizCategory.objects.all().order_by('order'):
        q_count = cat.questions.count()
        cat_type = "🧮 Math (Dynamic)" if cat.is_math_category else f"📝 {q_count} questions"
        print(f"{cat.order + 1}. {cat.name} - {cat_type}")
    
    print(f"\n✨ Total questions created: {total_created}")
    print(f"📊 Total questions in database: {QuizQuestion.objects.count()}")
    print(f"✅ Total answers in database: {QuizAnswer.objects.count()}")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
