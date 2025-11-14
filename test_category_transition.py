"""
Test category transition endpoint
"""
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizSession, QuizSubmission
)
from rest_framework.test import APIRequestFactory
from entertainment.views import QuizGameViewSet

print("=" * 80)
print("TEST: Category Transition Endpoint")
print("=" * 80)

# Get test data
quiz = Quiz.objects.filter(slug='guessticulator').first()
categories = list(QuizCategory.objects.filter(
    is_active=True
).order_by('order_index'))

print(f"\n📚 Categories ({len(categories)} total):")
for i, cat in enumerate(categories, 1):
    print(f"   {i}. {cat.name} ({cat.slug})")

# Create session
session = QuizSession.objects.create(
    quiz=quiz,
    session_token=str(uuid.uuid4()),
    player_name='CategoryTest',
    score=40
)

# Simulate completing first category (10 questions)
first_category = categories[0]
questions = QuizQuestion.objects.filter(
    category=first_category,
    is_active=True
)[:10]

print(f"\n🎮 Simulating completion of: {first_category.name}")
for question in questions:
    QuizSubmission.objects.create(
        session=session,
        category=first_category,
        question=question,
        question_text=question.text,
        selected_answer=question.correct_answer.text,
        correct_answer=question.correct_answer.text,
        is_correct=True,
        time_taken_seconds=2,
        points_awarded=4
    )

print(f"   ✅ Created 10 submissions for {first_category.name}")

factory = APIRequestFactory()
view = QuizGameViewSet.as_view({'post': 'ready_for_next_category'})

# Test 1: Check after completing first category
print("\n" + "="*80)
print("TEST 1: After Completing First Category")
print("="*80)

request1 = factory.post(
    '/api/entertainment/quiz/game/ready_for_next_category/',
    {
        'session_id': str(session.id),
        'current_category_slug': first_category.slug
    },
    format='json'
)
response1 = view(request1)
response1.render()

if response1.status_code == 200:
    result = response1.data
    
    print(f"\n✅ Response Status: 200 OK")
    print(f"\n📊 Response:")
    print(f"   has_next_category: {result.get('has_next_category')}")
    print(f"   game_completed: {result.get('game_completed')}")
    
    if result.get('next_category'):
        next_cat = result['next_category']
        print(f"\n   Next Category:")
        print(f"      name: {next_cat['name']}")
        print(f"      slug: {next_cat['slug']}")
        print(f"      is_math: {next_cat['is_math_category']}")
    
    print(f"\n   Category Progress:")
    for slug, progress in result.get('category_progress', {}).items():
        status = "✅" if progress['is_complete'] else "⏳"
        print(f"      {status} {progress['name']}: {progress['completed']}/10")
    
    stats = result.get('session_stats', {})
    print(f"\n   Session Stats:")
    print(f"      score: {stats.get('score')}")
    print(f"      answered: {stats.get('total_questions_answered')}/{stats.get('total_questions')}")
    
    # Validation
    print(f"\n   Validation:")
    checks = [
        (result.get('has_next_category') is True, "Has next category"),
        (result.get('game_completed') is False, "Game not complete yet"),
        (result['next_category']['slug'] == categories[1].slug, "Next is second category"),
    ]
    
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"      {status} {desc}")

else:
    print(f"❌ Failed: {response1.status_code}")
    print(response1.data)

# Test 2: Complete ALL categories
print("\n" + "="*80)
print("TEST 2: After Completing ALL Categories")
print("="*80)

# Complete remaining categories
for cat in categories[1:]:
    questions = QuizQuestion.objects.filter(
        category=cat,
        is_active=True
    )[:10]
    
    for question in questions:
        QuizSubmission.objects.create(
            session=session,
            category=cat,
            question=question,
            question_text=question.text,
            selected_answer=question.correct_answer.text,
            correct_answer=question.correct_answer.text,
            is_correct=True,
            time_taken_seconds=2,
            points_awarded=4
        )
    print(f"   ✅ Completed {cat.name}")

last_category = categories[-1]

request2 = factory.post(
    '/api/entertainment/quiz/game/ready_for_next_category/',
    {
        'session_id': str(session.id),
        'current_category_slug': last_category.slug
    },
    format='json'
)
response2 = view(request2)
response2.render()

if response2.status_code == 200:
    result = response2.data
    
    print(f"\n✅ Response Status: 200 OK")
    print(f"\n📊 Response:")
    print(f"   has_next_category: {result.get('has_next_category')}")
    print(f"   game_completed: {result.get('game_completed')}")
    print(f"   next_category: {result.get('next_category')}")
    
    print(f"\n   Category Progress:")
    for slug, progress in result.get('category_progress', {}).items():
        status = "✅" if progress['is_complete'] else "⏳"
        print(f"      {status} {progress['name']}: {progress['completed']}/10")
    
    stats = result.get('session_stats', {})
    print(f"\n   Session Stats:")
    print(f"      Total answered: {stats.get('total_questions_answered')}/{stats.get('total_questions')}")
    
    # Validation
    print(f"\n   Validation:")
    checks = [
        (result.get('has_next_category') is False, "No more categories"),
        (result.get('game_completed') is True, "Game is complete"),
        (result.get('next_category') is None, "Next category is None"),
    ]
    
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"      {status} {desc}")

else:
    print(f"❌ Failed: {response2.status_code}")
    print(response2.data)

print("\n" + "="*80)
print("CATEGORY TRANSITION READY")
print("="*80)
