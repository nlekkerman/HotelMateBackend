"""
Debug test to see what backend returns for submit_answer
"""
import os
import django
import uuid
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizAnswer, QuizSession
)
from rest_framework.test import APIRequestFactory
from entertainment.views import QuizGameViewSet

print("=" * 80)
print("DEBUG: Submit Answer - Check Correct Answer in Response")
print("=" * 80)

# Get or create quiz
quiz, _ = Quiz.objects.get_or_create(
    slug='guessticulator',
    defaults={
        'title': 'Guessticulator',
        'description': 'The ultimate quiz game',
        'is_active': True
    }
)

# Get a category
category = QuizCategory.objects.filter(
    is_active=True,
    is_math_category=False
).first()

if not category:
    print("❌ No category found")
    exit()

# Get a question
question = QuizQuestion.objects.filter(
    category=category,
    is_active=True
).prefetch_related('answers').first()

if not question:
    print("❌ No question found")
    exit()

print(f"\n📝 Question: {question.text}")
print(f"   Category: {category.name}")

# Check answers
answers = list(question.answers.all())
correct_answer = question.correct_answer

print(f"\n🔍 Answers ({len(answers)} total):")
for ans in answers:
    mark = "✅" if ans.is_correct else "❌"
    print(f"   {mark} ID: {ans.id} | Text: '{ans.text}' | Correct: {ans.is_correct}")

if correct_answer:
    print(f"\n✅ Correct Answer Found:")
    print(f"   ID: {correct_answer.id}")
    print(f"   Text: '{correct_answer.text}'")
else:
    print(f"\n❌ NO CORRECT ANSWER SET!")
    exit()

# Create a session
session_token = str(uuid.uuid4())
session = QuizSession.objects.create(
    quiz=quiz,
    session_token=session_token,
    player_name='DebugPlayer',
    score=0
)

print(f"\n🎮 Session Created: {session.id}")

# Submit WRONG answer
factory = APIRequestFactory()

wrong_answer = next((a for a in answers if not a.is_correct), None)
if not wrong_answer:
    print("❌ No wrong answer found")
    exit()

data = {
    'session_id': str(session.id),
    'category_slug': category.slug,
    'question_id': question.id,
    'question_text': question.text,
    'selected_answer': wrong_answer.text,
    'selected_answer_id': wrong_answer.id,
    'time_taken_seconds': 2
}

print(f"\n📤 SUBMITTING ANSWER:")
print(f"   Question: {data['question_text'][:50]}")
print(f"   Selected: '{data['selected_answer']}'")
print(f"   Should be: '{correct_answer.text}'")

request = factory.post(
    '/api/entertainment/quiz/game/submit_answer/',
    data,
    format='json'
)

view = QuizGameViewSet.as_view({'post': 'submit_answer'})

try:
    response = view(request)
    response.render()
    
    print(f"\n📥 RESPONSE (Status {response.status_code}):")
    
    if response.status_code == 200:
        result = response.data
        submission = result.get('submission', {})
        
        print(f"\n✅ SUCCESS Response:")
        print(f"   Is Correct: {submission.get('is_correct')}")
        print(f"   Selected Answer: '{submission.get('selected_answer')}'")
        print(f"   Correct Answer: '{submission.get('correct_answer')}'")  # THIS IS THE KEY
        print(f"   Points Awarded: {submission.get('points_awarded')}")
        
        print(f"\n📋 FULL SUBMISSION DATA:")
        print(json.dumps(submission, indent=2, default=str))
        
        if not submission.get('correct_answer'):
            print(f"\n⚠️  WARNING: correct_answer is EMPTY in response!")
        elif submission.get('correct_answer') == 'Answer':
            print(f"\n⚠️  WARNING: correct_answer has default value 'Answer'!")
        else:
            print(f"\n✅ correct_answer properly set in response")
            
    else:
        print(f"❌ FAILED!")
        print(f"Error: {response.data}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
