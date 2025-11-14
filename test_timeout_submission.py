"""
Test timeout answer submission
"""
import os
import django
import uuid
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizSession
)
from rest_framework.test import APIRequestFactory
from entertainment.views import QuizGameViewSet

print("=" * 80)
print("TEST: Timeout Answer Submission")
print("=" * 80)

# Get quiz and category
quiz = Quiz.objects.filter(slug='guessticulator').first()
category = QuizCategory.objects.filter(
    is_active=True,
    is_math_category=False
).first()
question = QuizQuestion.objects.filter(
    category=category,
    is_active=True
).prefetch_related('answers').first()

if not all([quiz, category, question]):
    print("❌ Missing test data")
    exit()

print(f"\n📝 Question: {question.text}")
correct_answer = question.correct_answer
print(f"✅ Correct Answer: '{correct_answer.text}'")

# Create session
session_token = str(uuid.uuid4())
session = QuizSession.objects.create(
    quiz=quiz,
    session_token=session_token,
    player_name='TimeoutTestPlayer',
    score=0,
    consecutive_correct=3,  # Has some streak
    is_turbo_active=False
)

print(f"\n🎮 Session Created: {session.id}")
print(f"   Initial Score: {session.score}")
print(f"   Initial Streak: {session.consecutive_correct}")

# Test 1: Submit with time > 5 (timeout)
print("\n" + "="*80)
print("TEST 1: Time Exceeded (6 seconds)")
print("="*80)

factory = APIRequestFactory()
data = {
    'session_id': str(session.id),
    'category_slug': category.slug,
    'question_id': question.id,
    'question_text': question.text,
    'selected_answer': 'Some Answer',  # Even if correct, should fail
    'selected_answer_id': 1,
    'time_taken_seconds': 6  # > 5 = timeout
}

request = factory.post('/api/entertainment/quiz/game/submit_answer/', data, format='json')
view = QuizGameViewSet.as_view({'post': 'submit_answer'})

try:
    response = view(request)
    response.render()
    
    if response.status_code == 200:
        result = response.data
        submission = result['submission']
        
        print(f"\n✅ Response OK")
        print(f"   Selected Answer: '{submission['selected_answer']}'")
        print(f"   Correct Answer: '{submission['correct_answer']}'")
        print(f"   Is Correct: {submission['is_correct']}")
        print(f"   Points: {submission['points_awarded']}")
        print(f"   Time: {submission['time_taken_seconds']}s")
        
        session.refresh_from_db()
        print(f"\n   Session Streak After: {session.consecutive_correct}")
        print(f"   Turbo Active: {session.is_turbo_active}")
        
        if submission['points_awarded'] == 0:
            print("\n✅ PASS: Timeout gave 0 points")
        else:
            print(f"\n❌ FAIL: Timeout gave {submission['points_awarded']} points")
            
        if session.consecutive_correct == 0:
            print("✅ PASS: Streak reset to 0")
        else:
            print(f"❌ FAIL: Streak is {session.consecutive_correct}")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(response.data)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Submit with "TIMEOUT" answer
print("\n" + "="*80)
print("TEST 2: Explicit TIMEOUT Answer")
print("="*80)

# Reset session
session.consecutive_correct = 5
session.is_turbo_active = True
session.save()

print(f"\n🎮 Session Reset:")
print(f"   Streak: {session.consecutive_correct}")
print(f"   Turbo: {session.is_turbo_active}")

data2 = {
    'session_id': str(session.id),
    'category_slug': category.slug,
    'question_id': question.id,
    'question_text': question.text,
    'selected_answer': 'TIMEOUT',  # Special timeout value
    'selected_answer_id': None,
    'time_taken_seconds': 3  # Under 5, but TIMEOUT answer
}

request2 = factory.post('/api/entertainment/quiz/game/submit_answer/', data2, format='json')

try:
    response2 = view(request2)
    response2.render()
    
    if response2.status_code == 200:
        result2 = response2.data
        submission2 = result2['submission']
        
        print(f"\n✅ Response OK")
        print(f"   Selected Answer: '{submission2['selected_answer']}'")
        print(f"   Correct Answer: '{submission2['correct_answer']}'")
        print(f"   Is Correct: {submission2['is_correct']}")
        print(f"   Points: {submission2['points_awarded']}")
        
        session.refresh_from_db()
        print(f"\n   Session Streak After: {session.consecutive_correct}")
        print(f"   Turbo Active: {session.is_turbo_active}")
        
        if submission2['selected_answer'] == 'TIMEOUT':
            print("\n✅ PASS: Answer recorded as TIMEOUT")
        else:
            print(f"\n❌ FAIL: Answer is '{submission2['selected_answer']}'")
            
        if submission2['points_awarded'] == 0:
            print("✅ PASS: TIMEOUT gave 0 points")
        else:
            print(f"❌ FAIL: TIMEOUT gave {submission2['points_awarded']} points")
            
        if session.consecutive_correct == 0:
            print("✅ PASS: Streak reset from 5 to 0")
        else:
            print(f"❌ FAIL: Streak is {session.consecutive_correct}")
            
        if not session.is_turbo_active:
            print("✅ PASS: Turbo mode deactivated")
        else:
            print("❌ FAIL: Turbo mode still active")
    else:
        print(f"❌ FAILED: Status {response2.status_code}")
        print(response2.data)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TIMEOUT TESTS COMPLETE")
print("=" * 80)
