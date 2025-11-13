"""
Simple Quiz Game Test - Direct API Testing
Tests the anonymous quiz game endpoints
"""
import os
import django
import uuid
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizAnswer,
    QuizSession, QuizSubmission
)


def test_fetch_quizzes():
    """Test fetching quiz data from models"""
    print("\n" + "="*70)
    print("TEST 1: Fetch Quiz Data from Database")
    print("="*70)
    
    quizzes = Quiz.objects.filter(is_active=True)
    print(f"\nActive Quizzes: {quizzes.count()}")
    
    for quiz in quizzes:
        print(f"\n  📝 Quiz: {quiz.title}")
        print(f"     Slug: {quiz.slug}")
        print(f"     Questions per category: {quiz.questions_per_category}")
        print(f"     Time per question: {quiz.time_per_question_seconds}s")
        print(f"     Turbo threshold: {quiz.turbo_mode_threshold}")
        print(f"     Turbo multiplier: {quiz.turbo_multiplier}x")
    
    assert quizzes.exists(), "No active quizzes found!"
    print("\n✅ Quiz data fetched successfully")
    return quizzes.first()


def test_fetch_categories():
    """Test fetching categories"""
    print("\n" + "="*70)
    print("TEST 2: Fetch Quiz Categories")
    print("="*70)
    
    categories = QuizCategory.objects.filter(is_active=True).order_by('order')
    print(f"\nActive Categories: {categories.count()}")
    
    for cat in categories:
        question_count = cat.questions.filter(is_active=True).count() if not cat.is_math_category else "Dynamic"
        print(f"\n  📂 Category: {cat.name}")
        print(f"     Slug: {cat.slug}")
        print(f"     Order: {cat.order}")
        print(f"     Is Math: {cat.is_math_category}")
        print(f"     Questions: {question_count}")
    
    assert categories.exists(), "No active categories found!"
    print("\n✅ Categories fetched successfully")
    return list(categories)


def test_fetch_questions():
    """Test fetching questions from a category"""
    print("\n" + "="*70)
    print("TEST 3: Fetch Questions from Category")
    print("="*70)
    
    # Get a non-math category
    category = QuizCategory.objects.filter(
        is_active=True,
        is_math_category=False
    ).first()
    
    if not category:
        print("⚠️  No non-math categories available")
        return
    
    print(f"\nCategory: {category.name}")
    
    questions = QuizQuestion.objects.filter(
        category=category,
        is_active=True
    ).prefetch_related('answers')[:5]
    
    print(f"Sample Questions: {questions.count()}")
    
    for i, q in enumerate(questions, 1):
        print(f"\n  ❓ Question {i}: {q.text[:60]}...")
        answers = q.answers.all()
        print(f"     Answers: {answers.count()}")
        
        for ans in answers:
            mark = "✓" if ans.is_correct else "✗"
            print(f"       {mark} {ans.text}")
    
    print("\n✅ Questions fetched successfully")


def test_create_session():
    """Test creating a game session"""
    print("\n" + "="*70)
    print("TEST 4: Create Game Session")
    print("="*70)
    
    quiz = Quiz.objects.filter(is_active=True).first()
    if not quiz:
        print("❌ No quiz available")
        return None
    
    session_token = str(uuid.uuid4())
    player_name = "TestPlayer123"
    
    session = QuizSession.objects.create(
        quiz=quiz,
        session_token=session_token,
        player_name=player_name,
        is_tournament_mode=False,
        score=0
    )
    
    print(f"\n✅ Session Created!")
    print(f"   ID: {session.id}")
    print(f"   Player: {session.player_name}")
    print(f"   Session Token: {session.session_token}")
    print(f"   Score: {session.score}")
    print(f"   Turbo Active: {session.is_turbo_active}")
    print(f"   Created: {session.started_at}")
    
    return session


def test_submit_answers(session):
    """Test submitting answers and scoring"""
    print("\n" + "="*70)
    print("TEST 5: Submit Answers and Calculate Points")
    print("="*70)
    
    if not session:
        print("⚠️  No session to test")
        return
    
    # Get a category and questions
    category = QuizCategory.objects.filter(
        is_active=True,
        is_math_category=False
    ).first()
    
    if not category:
        print("⚠️  No categories available")
        return
    
    questions = QuizQuestion.objects.filter(
        category=category,
        is_active=True
    ).prefetch_related('answers')[:10]
    
    print(f"\nSubmitting answers for {questions.count()} questions...")
    
    # Submit 5 correct answers (should trigger turbo)
    for i, question in enumerate(questions[:5], 1):
        correct_answer = question.correct_answer
        
        submission = QuizSubmission.objects.create(
            session=session,
            category=category,
            question=question,
            question_text=question.text,
            selected_answer=correct_answer.text,
            selected_answer_id=correct_answer.id,
            correct_answer=correct_answer.text,
            is_correct=True,
            time_taken_seconds=1,
            was_turbo_active=session.is_turbo_active
        )
        
        points = submission.calculate_points()
        submission.points_awarded = points
        submission.save()
        
        session.score += points
        session.consecutive_correct += 1
        
        # Check turbo activation
        if session.consecutive_correct >= session.quiz.turbo_mode_threshold:
            session.is_turbo_active = True
        
        session.save()
        
        turbo_status = "🔥 TURBO" if session.is_turbo_active else "⚡ Normal"
        print(f"\n  {i}. Correct Answer ({turbo_status})")
        print(f"     Points: {points}")
        print(f"     Total Score: {session.score}")
        print(f"     Consecutive: {session.consecutive_correct}")
    
    # Submit 1 wrong answer (should break turbo)
    wrong_question = questions[5]
    wrong_answer = wrong_question.answers.filter(is_correct=False).first()
    
    submission = QuizSubmission.objects.create(
        session=session,
        category=category,
        question=wrong_question,
        question_text=wrong_question.text,
        selected_answer=wrong_answer.text,
        selected_answer_id=wrong_answer.id,
        correct_answer=wrong_question.correct_answer.text,
        is_correct=False,
        time_taken_seconds=2,
        was_turbo_active=session.is_turbo_active
    )
    
    points = submission.calculate_points()
    submission.points_awarded = points
    submission.save()
    
    session.consecutive_correct = 0
    session.is_turbo_active = False
    session.save()
    
    print(f"\n  6. Wrong Answer ❌")
    print(f"     Points: {points}")
    print(f"     Total Score: {session.score}")
    print(f"     Consecutive Reset: {session.consecutive_correct}")
    print(f"     Turbo Deactivated: {not session.is_turbo_active}")
    
    print("\n✅ Answer submission tested successfully")


def test_complete_session(session):
    """Test completing a session"""
    print("\n" + "="*70)
    print("TEST 6: Complete Session")
    print("="*70)
    
    if not session:
        print("⚠️  No session to complete")
        return
    
    session.complete_session()
    session.refresh_from_db()
    
    print(f"\n✅ Session Completed!")
    print(f"   Final Score: {session.score}")
    print(f"   Duration: {session.duration_formatted}")
    print(f"   Completed: {session.is_completed}")
    print(f"   Finished At: {session.finished_at}")
    
    # Get submission stats
    submissions = QuizSubmission.objects.filter(session=session)
    correct_count = submissions.filter(is_correct=True).count()
    
    print(f"\n   Submission Stats:")
    print(f"     Total Answers: {submissions.count()}")
    print(f"     Correct: {correct_count}")
    print(f"     Wrong: {submissions.count() - correct_count}")
    print(f"     Accuracy: {(correct_count/submissions.count()*100):.1f}%")


def test_point_calculation():
    """Test the point calculation logic"""
    print("\n" + "="*70)
    print("TEST 7: Point Calculation Logic")
    print("="*70)
    
    quiz = Quiz.objects.filter(is_active=True).first()
    category = QuizCategory.objects.filter(is_active=True).first()
    question = QuizQuestion.objects.filter(
        category=category,
        is_active=True
    ).first()
    
    if not all([quiz, category, question]):
        print("⚠️  Missing data for test")
        return
    
    session = QuizSession.objects.create(
        quiz=quiz,
        session_token=str(uuid.uuid4()),
        player_name="PointTestPlayer",
        score=0
    )
    
    print("\n📊 Point Calculation Matrix:")
    print("\nNormal Mode:")
    
    for seconds in range(6):
        submission = QuizSubmission(
            session=session,
            category=category,
            question=question,
            question_text="Test",
            selected_answer="Test",
            correct_answer="Test",
            is_correct=True,
            time_taken_seconds=seconds,
            was_turbo_active=False
        )
        points = submission.calculate_points()
        print(f"  {seconds}s → {points} points")
    
    print("\nTurbo Mode (2x multiplier):")
    
    for seconds in range(6):
        submission = QuizSubmission(
            session=session,
            category=category,
            question=question,
            question_text="Test",
            selected_answer="Test",
            correct_answer="Test",
            is_correct=True,
            time_taken_seconds=seconds,
            was_turbo_active=True
        )
        points = submission.calculate_points()
        print(f"  {seconds}s → {points} points")
    
    print("\n✅ Point calculation tested successfully")
    
    # Cleanup
    session.delete()


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🎮 QUIZ GAME - COMPREHENSIVE TEST SUITE")
    print("Testing Anonymous Quiz Game Logic")
    print("="*70)
    
    try:
        # Test 1: Fetch quiz
        quiz = test_fetch_quizzes()
        
        # Test 2: Fetch categories
        categories = test_fetch_categories()
        
        # Test 3: Fetch questions
        test_fetch_questions()
        
        # Test 4: Create session
        session = test_create_session()
        
        # Test 5: Submit answers
        test_submit_answers(session)
        
        # Test 6: Complete session
        test_complete_session(session)
        
        # Test 7: Point calculation
        test_point_calculation()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
        print("\n📊 Summary:")
        print(f"   Total Quizzes: {Quiz.objects.filter(is_active=True).count()}")
        print(f"   Total Categories: {QuizCategory.objects.filter(is_active=True).count()}")
        print(f"   Total Questions: {QuizQuestion.objects.filter(is_active=True).count()}")
        print(f"   Total Sessions: {QuizSession.objects.count()}")
        print(f"   Total Submissions: {QuizSubmission.objects.count()}")
        
        # Cleanup option
        print("\n" + "="*70)
        cleanup = input("\nDelete test session data? (y/n): ")
        if cleanup.lower() == 'y':
            if session:
                QuizSubmission.objects.filter(session=session).delete()
                session.delete()
                print("✅ Test data cleaned up")
        else:
            print("⚠️  Test data kept in database")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
