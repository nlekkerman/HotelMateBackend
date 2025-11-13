"""
Test script for Level 4 Dynamic Math quiz generation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizCategory
from entertainment.views import QuizViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

# Get or create category
category, _ = QuizCategory.objects.get_or_create(
    name="General Knowledge",
    defaults={
        'description': 'Test your general knowledge across various topics',
        'is_active': True
    }
)

# Create Level 4 Math Quiz if it doesn't exist
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

if created:
    print(f'✓ Created quiz: {quiz.title}')
else:
    print(f'Quiz already exists: {quiz.title}')

print(f'\nQuiz Details:')
print(f'  - ID: {quiz.id}')
print(f'  - Slug: {quiz.slug}')
print(f'  - Difficulty Level: {quiz.difficulty_level}')
print(f'  - Time per question: {quiz.time_per_question_seconds}s')
print(f'  - Max questions: {quiz.max_questions}')

# Test math question generation
print('\n' + '='*60)
print('Testing Dynamic Math Question Generation')
print('='*60)

factory = APIRequestFactory()
request = factory.post(f'/api/entertainment/quizzes/{quiz.slug}/generate_math_question/')
request = Request(request)

viewset = QuizViewSet()
viewset.request = request
viewset.kwargs = {'slug': quiz.slug}

# Set up the queryset for get_object() to work
viewset.queryset = Quiz.objects.all()

# Generate 10 sample math questions
print('\nGenerating 10 sample math questions:\n')

for i in range(10):
    response = viewset.generate_math_question(request, slug=quiz.slug)
    data = response.data
    
    print(f'Question {i+1}:')
    print(f'  Problem: {data["question_text"]}')
    print(f'  Correct Answer: {data["correct_answer"]}')
    print(f'  Options: {data["options"]}')
    print(f'  Base Points: {data["base_points"]}')
    
    # Verify correct answer is in options
    if data["correct_answer"] in data["options"]:
        print('  ✓ Correct answer is in options')
    else:
        print('  ✗ ERROR: Correct answer not in options!')
    
    # Verify exactly 4 options
    if len(data["options"]) == 4:
        print('  ✓ Has 4 options')
    else:
        print(f'  ✗ ERROR: Has {len(data["options"])} options instead of 4!')
    
    # Verify all options are unique
    if len(set(data["options"])) == 4:
        print('  ✓ All options are unique')
    else:
        print('  ✗ ERROR: Duplicate options found!')
    
    print()

print('='*60)
print('Test Complete!')
print('='*60)
