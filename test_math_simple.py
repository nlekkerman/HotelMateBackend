"""
Simple test for Level 4 Dynamic Math quiz generation
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizCategory

# Get or create category
category, _ = QuizCategory.objects.get_or_create(
    name="General Knowledge",
    defaults={
        'description': 'Test your general knowledge across various topics',
        'is_active': True
    }
)

# Create Level 4 Math Quiz
quiz, created = Quiz.objects.get_or_create(
    slug='dynamic-math-expert',
    defaults={
        'category': category,
        'title': 'Dynamic Math - Expert',
        'description': 'Level 4: Fast-paced mental math challenges',
        'difficulty_level': 4,
        'is_active': True,
        'is_daily': False,
        'max_questions': 10,
        'time_per_question_seconds': 12,
        'enable_background_music': True,
        'enable_sound_effects': True,
        'sound_theme': 'default'
    }
)

print(f'Quiz: {quiz.title} (Level {quiz.difficulty_level})')
print(f'Is Math Quiz: {quiz.is_math_quiz}')
print()

# Test math generation logic directly
print('='*60)
print('Testing Math Question Generation')
print('='*60)
print()

for i in range(10):
    # Generate random math problem
    num1 = random.randint(0, 10)
    num2 = random.randint(0, 10)
    operation = random.choice(['+', '-', '×', '÷'])
    
    # Calculate correct answer
    if operation == '+':
        correct_answer = num1 + num2
        question_text = f"What is {num1} + {num2}?"
    elif operation == '-':
        correct_answer = num1 - num2
        question_text = f"What is {num1} - {num2}?"
    elif operation == '×':
        correct_answer = num1 * num2
        question_text = f"What is {num1} × {num2}?"
    else:  # ÷
        # Ensure whole number division
        num1 = num2 * random.randint(1, 10)
        correct_answer = num1 // num2
        question_text = f"What is {num1} ÷ {num2}?"
    
    # Generate 3 believable distractors
    distractors = set()
    while len(distractors) < 3:
        offset = random.choice([-2, -1, 1, 2, 3, -3])
        distractor = correct_answer + offset
        if distractor != correct_answer and distractor >= 0:
            distractors.add(distractor)
    
    # Create answer options
    answers = [str(correct_answer)] + [str(d) for d in distractors]
    random.shuffle(answers)
    
    print(f'Question {i+1}: {question_text}')
    print(f'  Correct Answer: {correct_answer}')
    print(f'  Options: {answers}')
    print(f'  ✓ Correct in options: {str(correct_answer) in answers}')
    print(f'  ✓ Has 4 options: {len(answers) == 4}')
    print(f'  ✓ All unique: {len(set(answers)) == 4}')
    print()

print('='*60)
print('✓ Math generation test complete!')
print('='*60)
