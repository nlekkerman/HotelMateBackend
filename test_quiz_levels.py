"""
Test Quiz Tournament - 10 Random Questions Per Level (1-5)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import (
    Quiz, QuizQuestion, QuizAnswer, 
    QuizSession, QuizSubmission, QuizTournament
)
from datetime import timedelta
import random


def create_test_quiz_with_levels():
    """Create a test quiz with questions across all 5 levels"""
    print("\n=== Creating Test Quiz with 5 Levels ===")
    
    quiz, created = Quiz.objects.get_or_create(
        slug='multi-level-tournament-quiz',
        defaults={
            'title': 'Multi-Level Tournament Quiz',
            'description': 'Quiz with questions from level 1 to 5',
            'difficulty_level': 1,
            'is_active': True,
            'max_questions': 50
        }
    )
    print(f"Quiz: {quiz.title} ({'created' if created else 'exists'})")
    
    # Create 15 questions per level (to have enough for random selection)
    questions_per_level = 15
    
    for level in range(1, 6):
        print(f"\nCreating questions for Level {level}...")
        for q_num in range(1, questions_per_level + 1):
            question, created = QuizQuestion.objects.get_or_create(
                quiz=quiz,
                order=(level - 1) * 100 + q_num,
                defaults={
                    'text': f'Level {level} Question {q_num}: Sample question?',
                    'difficulty_level': level,
                    'base_points': 10 * level,
                    'is_active': True
                }
            )
            
            if created:
                # Create 4 answers (1 correct, 3 wrong)
                answers_data = [
                    ('Correct Answer', True),
                    ('Wrong Answer 1', False),
                    ('Wrong Answer 2', False),
                    ('Wrong Answer 3', False)
                ]
                
                for idx, (answer_text, is_correct) in enumerate(answers_data):
                    QuizAnswer.objects.create(
                        question=question,
                        text=answer_text,
                        is_correct=is_correct,
                        order=idx
                    )
        
        level_questions = QuizQuestion.objects.filter(
            quiz=quiz,
            difficulty_level=level
        ).count()
        print(f"  Level {level}: {level_questions} questions")
    
    total = QuizQuestion.objects.filter(quiz=quiz).count()
    print(f"\nTotal questions created: {total}")
    return quiz


def test_random_question_selection(quiz):
    """Test that we get 10 random questions per level"""
    print("\n=== Testing Random Question Selection ===")
    
    all_selected = []
    
    for level in range(1, 6):
        # Get 10 random questions from this level
        questions = list(QuizQuestion.objects.filter(
            quiz=quiz,
            difficulty_level=level,
            is_active=True
        ))
        
        if len(questions) < 10:
            print(f"❌ Level {level}: Only {len(questions)} questions available")
            continue
        
        # Random selection
        selected = random.sample(questions, 10)
        all_selected.extend(selected)
        
        print(f"\nLevel {level}: Selected 10 random questions")
        print(f"  Question IDs: {[q.id for q in selected[:5]]}... (showing first 5)")
        print(f"  All have difficulty_level={level}: {all(q.difficulty_level == level for q in selected)}")
    
    print(f"\n✅ Total questions selected: {len(all_selected)} (should be 50)")
    return all_selected


def simulate_tournament_session(quiz, player_name, questions):
    """Simulate a player completing all 50 questions"""
    print(f"\n=== Simulating Session for {player_name} ===")
    
    # Create session
    session = QuizSession.objects.create(
        quiz=quiz,
        player_name=player_name,
        is_tournament=True,
        score=0,
        is_completed=False
    )
    
    total_score = 0
    total_time = 0
    correct_count = 0
    
    # Simulate answering questions level by level
    for level in range(1, 6):
        level_questions = [q for q in questions if q.difficulty_level == level]
        print(f"\nLevel {level}: {len(level_questions)} questions")
        
        for question in level_questions:
            # Randomly decide if answer is correct (80% success rate)
            is_correct = random.random() < 0.8
            time_taken = random.randint(3, 10)
            
            # Get correct answer
            correct_answer = question.answers.filter(is_correct=True).first()
            selected_answer = correct_answer if is_correct else question.answers.filter(is_correct=False).first()
            
            # Create submission
            points = question.base_points if is_correct else 0
            QuizSubmission.objects.create(
                session=session,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct,
                time_taken_seconds=time_taken,
                points_awarded=points
            )
            
            if is_correct:
                total_score += points
                correct_count += 1
            total_time += time_taken
        
        print(f"  Correct: {correct_count}/10, Score so far: {total_score}")
    
    # Complete session
    session.score = total_score
    session.is_completed = True
    session.finished_at = timezone.now()
    session.time_spent_seconds = total_time
    session.save()
    
    print(f"\n✅ Session completed:")
    print(f"   Final Score: {total_score}")
    print(f"   Correct: {correct_count}/50")
    print(f"   Time: {total_time}s")
    
    return session


def test_level_progression():
    """Test complete flow: 10 questions per level, levels 1-5"""
    print("=" * 70)
    print("QUIZ TOURNAMENT TEST: 10 Random Questions Per Level (1-5)")
    print("=" * 70)
    
    # Setup
    quiz = create_test_quiz_with_levels()
    
    # Test random selection
    selected_questions = test_random_question_selection(quiz)
    
    # Verify level distribution
    print("\n=== Verifying Level Distribution ===")
    for level in range(1, 6):
        count = sum(1 for q in selected_questions if q.difficulty_level == level)
        status = "✅" if count == 10 else "❌"
        print(f"{status} Level {level}: {count} questions (expected: 10)")
    
    # Simulate tournament sessions for multiple players
    print("\n=== Simulating Tournament Sessions ===")
    players = ['Alice', 'Bob', 'Charlie']
    
    for player in players:
        # Each player gets fresh random questions
        player_questions = []
        for level in range(1, 6):
            level_qs = list(QuizQuestion.objects.filter(
                quiz=quiz,
                difficulty_level=level,
                is_active=True
            ))
            player_questions.extend(random.sample(level_qs, 10))
        
        simulate_tournament_session(quiz, player, player_questions)
    
    # Check leaderboard
    print("\n=== Tournament Leaderboard ===")
    sessions = QuizSession.objects.filter(
        quiz=quiz,
        is_tournament=True,
        is_completed=True
    ).order_by('-score', 'time_spent_seconds')
    
    for rank, session in enumerate(sessions, 1):
        print(f"#{rank} {session.player_name}: {session.score} pts ({session.time_spent_seconds}s)")
    
    # Cleanup
    print("\n=== Cleanup ===")
    response = input("Delete test data? (y/n): ")
    if response.lower() == 'y':
        QuizSession.objects.filter(quiz=quiz).delete()
        QuizAnswer.objects.filter(question__quiz=quiz).delete()
        QuizQuestion.objects.filter(quiz=quiz).delete()
        Quiz.objects.filter(slug='multi-level-tournament-quiz').delete()
        print("✅ Test data deleted")
    else:
        print("⚠️  Test data kept in database")


if __name__ == '__main__':
    test_level_progression()
