"""
Test auto-completion after 50 questions
"""
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizSession
)
from rest_framework.test import APIRequestFactory
from entertainment.views import QuizGameViewSet

print("=" * 80)
print("TEST: Auto-Completion After 50 Questions")
print("=" * 80)

# Get quiz and categories
quiz = Quiz.objects.filter(slug='guessticulator').first()
categories = list(QuizCategory.objects.filter(is_active=True).order_by('order'))

print(f"\n📊 Quiz Configuration:")
print(f"   Questions per category: {quiz.questions_per_category}")
print(f"   Active categories: {len(categories)}")
print(f"   Total questions needed: {quiz.questions_per_category * len(categories)}")

if len(categories) != 5:
    print(f"\n⚠️  WARNING: Expected 5 categories, found {len(categories)}")

# Create session
session_token = str(uuid.uuid4())
session = QuizSession.objects.create(
    quiz=quiz,
    session_token=session_token,
    player_name='AutoCompleteTestPlayer',
    score=0
)

print(f"\n🎮 Session Created: {session.id}")
print(f"   Player: {session.player_name}")
print(f"   Initial is_completed: {session.is_completed}")

# Get questions from each category
factory = APIRequestFactory()
view = QuizGameViewSet.as_view({'post': 'submit_answer'})

total_submitted = 0
total_questions = quiz.questions_per_category * len(categories)

print(f"\n📝 Submitting {total_questions} Answers...")
print("=" * 80)

for cat_idx, category in enumerate(categories, 1):
    print(f"\n[Category {cat_idx}/5] {category.name}")
    
    # Get questions for this category
    questions = list(QuizQuestion.objects.filter(
        category=category,
        is_active=True
    ).prefetch_related('answers')[:quiz.questions_per_category])
    
    if not questions:
        print(f"   ⚠️  No questions found, skipping")
        continue
    
    for q_idx, question in enumerate(questions, 1):
        correct_answer = question.correct_answer
        
        if not correct_answer:
            print(f"   ⚠️  Question {q_idx} has no correct answer")
            continue
        
        data = {
            'session_id': str(session.id),
            'category_slug': category.slug,
            'question_id': question.id,
            'question_text': question.text,
            'selected_answer': correct_answer.text,
            'selected_answer_id': correct_answer.id,
            'time_taken_seconds': 2
        }
        
        request = factory.post(
            '/api/entertainment/quiz/game/submit_answer/',
            data,
            format='json'
        )
        
        try:
            response = view(request)
            response.render()
            
            if response.status_code == 200:
                result = response.data
                total_submitted += 1
                
                session_updated = result.get('session_updated', {})
                game_completed = result.get('game_completed', False)
                
                answered = session_updated.get('total_questions_answered', 0)
                total = session_updated.get('total_questions', 0)
                is_completed = session_updated.get('is_completed', False)
                
                # Print progress for key milestones
                if q_idx == 1:
                    print(f"   Question 1: {answered}/{total} answered")
                elif q_idx == quiz.questions_per_category:
                    print(f"   Question 10: {answered}/{total} answered")
                
                # Check if game auto-completed
                if game_completed:
                    print(f"\n{'='*80}")
                    print(f"✅ GAME AUTO-COMPLETED!")
                    print(f"{'='*80}")
                    print(f"   Total submitted: {total_submitted}")
                    print(f"   Questions answered: {answered}/{total}")
                    print(f"   Is completed: {is_completed}")
                    print(f"   game_completed flag: {game_completed}")
                    print(f"   Final score: {session_updated.get('score', 0)}")
                    
                    session.refresh_from_db()
                    print(f"\n   Session Model Check:")
                    print(f"   is_completed: {session.is_completed}")
                    print(f"   finished_at: {session.finished_at}")
                    print(f"   submission count: {session.submissions.count()}")
                    
                    if session.is_completed:
                        print(f"\n✅ PASS: Session auto-completed correctly!")
                    else:
                        print(f"\n❌ FAIL: game_completed true but session not marked complete")
                    
                    break
            else:
                print(f"   ❌ Submit failed: {response.status_code}")
                print(f"   Error: {response.data}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Check if completed early
    session.refresh_from_db()
    if session.is_completed:
        break

print(f"\n{'='*80}")
print(f"TEST COMPLETE")
print(f"{'='*80}")
print(f"\nFinal Stats:")
print(f"   Total Submitted: {total_submitted}")
print(f"   Expected: {total_questions}")
print(f"   Session Completed: {session.is_completed}")
print(f"   Finished At: {session.finished_at}")
print(f"   Final Score: {session.score}")

if total_submitted == total_questions and session.is_completed:
    print(f"\n✅ SUCCESS: Game auto-completed after exactly {total_questions} questions!")
elif total_submitted < total_questions:
    print(f"\n⚠️  INCOMPLETE: Only submitted {total_submitted}/{total_questions} questions")
elif not session.is_completed:
    print(f"\n❌ FAIL: Submitted {total_submitted} questions but session not completed")
else:
    print(f"\n⚠️  UNEXPECTED: total_submitted={total_submitted}, completed={session.is_completed}")

print(f"\n{'='*80}")
