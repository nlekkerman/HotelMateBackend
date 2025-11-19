"""
Load additional Science questions (Part 2) into the database
"""

import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory, QuizQuestion  # noqa: E402


def load_science_part2():
    """Load additional Science questions from JSON file"""
    
    # Read the JSON file
    json_path = "science_questions_part2.json"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get Science category
    try:
        category = QuizCategory.objects.get(slug='science')
        print(f"✅ Found Science category (Current questions: "
              f"{category.question_count})")
    except QuizCategory.DoesNotExist:
        print("❌ Science category not found! Please run "
              "load_science_questions.py first.")
        return
    
    # Load questions
    questions_created = 0
    questions_skipped = 0
    
    for idx, q_data in enumerate(data['questions'], 1):
        question_text = q_data['question']
        correct_answer = q_data['correct']
        
        # Convert True/False to options
        if correct_answer is True or correct_answer == 'true':
            option_a = "True"
            option_b = "False"
            correct = "A"
        else:
            option_a = "False"
            option_b = "True"
            correct = "B"
        
        # Check if question already exists
        exists = QuizQuestion.objects.filter(
            category=category,
            question_text=question_text
        ).exists()
        
        if exists:
            questions_skipped += 1
            print(f"⏭️  Question {idx}: Already exists, skipping")
            continue
        
        # Create the question
        QuizQuestion.objects.create(
            category=category,
            question_text=question_text,
            difficulty='medium',
            option_a=option_a,
            option_b=option_b,
            option_c='',
            option_d='',
            correct_answer=correct,
            points=10,
            is_active=True
        )
        
        questions_created += 1
        print(f"✅ Question {idx}: {question_text[:50]}...")
    
    print("\n" + "=" * 70)
    print(f"✅ Successfully loaded {questions_created} additional Science "
          f"questions")
    print(f"⏭️  Skipped {questions_skipped} existing questions")
    print(f"📊 Total questions in Science category: "
          f"{category.question_count}")
    print("=" * 70)


if __name__ == '__main__':
    try:
        load_science_part2()
    except Exception as e:
        print(f"\n❌ Error loading science questions part 2: {e}")
        import traceback
        traceback.print_exc()
