"""
Test that sessions return 10 random questions per level
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizSession
from entertainment.serializers import QuizSessionSerializer

print("=" * 80)
print("TESTING: 10 Random Questions Per Session")
print("=" * 80)

# Test each level
levels = [
    'classic-trivia-easy',
    'odd-one-out-moderate',
    'fill-the-blank-challenging',
    'knowledge-trap-expert'
]

for level_slug in levels:
    print(f"\n{'='*80}")
    print(f"Testing: {level_slug}")
    print('='*80)
    
    try:
        quiz = Quiz.objects.get(slug=level_slug)
        total_questions = quiz.questions.filter(is_active=True).count()
        print(f"Total questions in database: {total_questions}")
        
        # Create a test session
        session = QuizSession.objects.create(
            quiz=quiz,
            hotel_identifier='killarney',
            player_name='Test Player',
            is_practice_mode=True
        )
        
        # Serialize to see what frontend will receive
        serializer = QuizSessionSerializer(session)
        data = serializer.data
        
        questions_returned = data.get('questions', [])
        print(f"Questions returned to frontend: {len(questions_returned)}")
        
        if len(questions_returned) == 10:
            print("✓ PASS: Exactly 10 questions returned")
        else:
            print(f"✗ FAIL: Expected 10, got {len(questions_returned)}")
        
        # Show first 3 question texts to verify they're real questions
        print("\nSample questions:")
        for i, q in enumerate(questions_returned[:3], 1):
            text = q.get('text', 'N/A')[:60]
            answers_count = len(q.get('answers', []))
            print(f"  {i}. {text}... ({answers_count} answers)")
        
        # Test randomness: create another session and compare
        session2 = QuizSession.objects.create(
            quiz=quiz,
            hotel_identifier='killarney',
            player_name='Test Player 2',
            is_practice_mode=True
        )
        
        serializer2 = QuizSessionSerializer(session2)
        questions2 = serializer2.data.get('questions', [])
        
        # Check if order is different (randomness check)
        if questions_returned and questions2:
            first_q1 = questions_returned[0].get('id')
            first_q2 = questions2[0].get('id')
            
            if first_q1 != first_q2:
                print("✓ Questions are randomized (different first question)")
            else:
                print("⚠ Same first question (might not be random)")
        
        # Cleanup test sessions
        session.delete()
        session2.delete()
        
    except Quiz.DoesNotExist:
        print(f"✗ Quiz '{level_slug}' not found")
    except Exception as e:
        print(f"✗ Error: {e}")

# Test Level 4 (Math - should return empty)
print(f"\n{'='*80}")
print("Testing: dynamic-math-expert")
print('='*80)

try:
    quiz = Quiz.objects.get(slug='dynamic-math-expert')
    print(f"Is math quiz: {quiz.is_math_quiz}")
    
    session = QuizSession.objects.create(
        quiz=quiz,
        hotel_identifier='killarney',
        player_name='Test Player',
        is_practice_mode=True
    )
    
    serializer = QuizSessionSerializer(session)
    questions = serializer.data.get('questions', [])
    
    print(f"Questions returned: {len(questions)}")
    
    if len(questions) == 0:
        print("✓ PASS: Math quiz returns empty list (dynamic generation)")
    else:
        print(f"✗ FAIL: Expected 0, got {len(questions)}")
    
    session.delete()
    
except Quiz.DoesNotExist:
    print("✗ Quiz 'level-4-dynamic-math' not found")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*80)
print("Test Complete!")
print("="*80)
