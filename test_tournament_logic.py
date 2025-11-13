"""
Test Quiz Tournament Logic - Best Result Per Player
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import Quiz, QuizLevel, QuizQuestion, QuizSession, QuizSubmission, QuizTournament
from datetime import timedelta

def create_test_quiz():
    """Create a test quiz with levels and questions"""
    print("\n=== Creating Test Quiz ===")
    
    # Create quiz
    quiz, created = Quiz.objects.get_or_create(
        slug='tournament-test-quiz',
        defaults={
            'title': 'Tournament Test Quiz',
            'description': 'Test quiz for tournament',
            'active': True
        }
    )
    print(f"Quiz: {quiz.title} ({'created' if created else 'exists'})")
    
    # Create levels
    for level_num in range(1, 4):
        level, created = QuizLevel.objects.get_or_create(
            quiz=quiz,
            level=level_num,
            defaults={
                'points_per_question': 10,
                'time_limit_seconds': 30
            }
        )
        
        # Create questions for each level
        for q_num in range(1, 4):
            question, created = QuizQuestion.objects.get_or_create(
                level=level,
                defaults={
                    'question_text': f'Level {level_num} Question {q_num}?',
                    'correct_answer': 'A',
                    'option_a': 'Correct Answer',
                    'option_b': 'Wrong 1',
                    'option_c': 'Wrong 2',
                    'option_d': 'Wrong 3'
                }
            )
    
    print(f"Created quiz with {quiz.levels.count()} levels and {QuizQuestion.objects.filter(level__quiz=quiz).count()} questions")
    return quiz


def create_test_tournament(quiz):
    """Create a test tournament"""
    print("\n=== Creating Test Tournament ===")
    
    now = timezone.now()
    tournament, created = QuizTournament.objects.get_or_create(
        slug='winter-championship',
        defaults={
            'name': 'Winter Championship 2025',
            'quiz': quiz,
            'start_date': now - timedelta(days=1),
            'end_date': now + timedelta(days=7),
            'status': QuizTournament.TournamentStatus.ACTIVE,
            'first_prize': '$100',
            'second_prize': '$50',
            'third_prize': '$25',
            'rules': 'Best score wins! You can play multiple times.'
        }
    )
    
    print(f"Tournament: {tournament.name} ({'created' if created else 'exists'})")
    print(f"Status: {tournament.status}")
    print(f"Date Range: {tournament.start_date.date()} to {tournament.end_date.date()}")
    return tournament


def simulate_player_sessions(quiz, tournament):
    """Simulate multiple players playing the tournament multiple times"""
    print("\n=== Simulating Tournament Sessions ===")
    
    # Player scenarios:
    # Alice: 3 attempts (scores: 50, 75, 90) - best: 90
    # Bob: 2 attempts (scores: 80, 70) - best: 80
    # Charlie: 1 attempt (score: 95) - best: 95
    # Diana: 4 attempts (scores: 60, 65, 85, 82) - best: 85
    
    scenarios = [
        ('Alice', [50, 75, 90]),
        ('Bob', [80, 70]),
        ('Charlie', [95]),
        ('Diana', [60, 65, 85, 82])
    ]
    
    all_sessions = []
    
    for player_name, scores in scenarios:
        print(f"\n{player_name}'s attempts:")
        for attempt_num, score in enumerate(scores, 1):
            # Create session
            session = QuizSession.objects.create(
                quiz=quiz,
                player_name=player_name,
                is_tournament=True,
                current_level=1,
                score=0,
                is_completed=False,
                started_at=timezone.now() - timedelta(minutes=30 * attempt_num)
            )
            
            # Simulate answering questions to reach the score
            questions = list(QuizQuestion.objects.filter(level__quiz=quiz))
            correct_answers = min(score // 10, len(questions))  # 10 points per question
            
            for i, question in enumerate(questions[:correct_answers]):
                QuizSubmission.objects.create(
                    session=session,
                    question=question,
                    selected_answer=question.correct_answer,
                    is_correct=True,
                    time_taken_seconds=5
                )
            
            # Complete session with final score
            session.score = score
            session.is_completed = True
            session.finished_at = timezone.now()
            session.time_spent_seconds = 120 - (attempt_num * 10)  # Vary time
            session.save()
            
            all_sessions.append(session)
            print(f"  Attempt {attempt_num}: Score {score}, Time {session.time_spent_seconds}s")
    
    print(f"\nTotal sessions created: {len(all_sessions)}")
    return all_sessions


def test_leaderboard_logic(tournament):
    """Test that leaderboard shows only best result per player"""
    print("\n=== Testing Leaderboard Logic ===")
    
    # Get all tournament sessions
    all_sessions = QuizSession.objects.filter(
        quiz=tournament.quiz,
        is_tournament=True,
        is_completed=True
    ).order_by('player_name', '-score')
    
    print(f"\nAll sessions in database: {all_sessions.count()}")
    for session in all_sessions:
        print(f"  {session.player_name}: {session.score} pts ({session.time_spent_seconds}s)")
    
    # Get tournament leaderboard (should show only best per player)
    leaderboard = tournament.get_leaderboard(limit=10)
    
    print(f"\nTournament Leaderboard (best per player): {leaderboard.count()}")
    for rank, session in enumerate(leaderboard, 1):
        print(f"  #{rank} {session.player_name}: {session.score} pts ({session.time_spent_seconds}s)")
    
    # Verify results
    print("\n=== Verification ===")
    expected_results = {
        'Charlie': 95,
        'Alice': 90,
        'Diana': 85,
        'Bob': 80
    }
    
    leaderboard_list = list(leaderboard)
    success = True
    
    for rank, (expected_name, expected_score) in enumerate(expected_results.items(), 1):
        if rank <= len(leaderboard_list):
            session = leaderboard_list[rank - 1]
            if session.player_name == expected_name and session.score == expected_score:
                print(f"✅ Rank {rank}: {expected_name} with {expected_score} pts - CORRECT")
            else:
                print(f"❌ Rank {rank}: Expected {expected_name} ({expected_score}), got {session.player_name} ({session.score})")
                success = False
        else:
            print(f"❌ Rank {rank}: Missing entry for {expected_name}")
            success = False
    
    # Check that we don't have duplicate players
    player_names = [s.player_name for s in leaderboard_list]
    unique_names = set(player_names)
    if len(player_names) == len(unique_names):
        print(f"✅ No duplicate players in leaderboard")
    else:
        print(f"❌ Found duplicate players: {[n for n in player_names if player_names.count(n) > 1]}")
        success = False
    
    return success


def test_participant_count(tournament):
    """Test participant count"""
    print("\n=== Testing Participant Count ===")
    count = tournament.participant_count
    print(f"Unique participants: {count}")
    
    if count == 4:
        print("✅ Correct participant count (Alice, Bob, Charlie, Diana)")
        return True
    else:
        print(f"❌ Expected 4 participants, got {count}")
        return False


def test_tournament_qr_code(tournament):
    """Test QR code generation"""
    print("\n=== Testing QR Code Generation ===")
    
    try:
        success = tournament.generate_qr_code()
        if success and tournament.qr_code_url:
            print(f"✅ QR Code generated successfully")
            print(f"   URL: {tournament.qr_code_url}")
            print(f"   Generated at: {tournament.qr_generated_at}")
            return True
        else:
            print(f"❌ QR Code generation failed")
            return False
    except Exception as e:
        print(f"❌ Error generating QR code: {str(e)}")
        return False


def cleanup():
    """Clean up test data"""
    print("\n=== Cleanup ===")
    response = input("Delete test data? (y/n): ")
    if response.lower() == 'y':
        QuizSession.objects.filter(quiz__slug='tournament-test-quiz').delete()
        QuizTournament.objects.filter(slug='winter-championship').delete()
        QuizQuestion.objects.filter(level__quiz__slug='tournament-test-quiz').delete()
        QuizLevel.objects.filter(quiz__slug='tournament-test-quiz').delete()
        Quiz.objects.filter(slug='tournament-test-quiz').delete()
        print("✅ Test data deleted")
    else:
        print("⚠️  Test data kept in database")


def main():
    """Run all tests"""
    print("=" * 60)
    print("QUIZ TOURNAMENT LOGIC TEST")
    print("Testing: Best Result Per Player")
    print("=" * 60)
    
    # Setup
    quiz = create_test_quiz()
    tournament = create_test_tournament(quiz)
    simulate_player_sessions(quiz, tournament)
    
    # Run tests
    results = []
    results.append(("Leaderboard Logic", test_leaderboard_logic(tournament)))
    results.append(("Participant Count", test_participant_count(tournament)))
    results.append(("QR Code Generation", test_tournament_qr_code(tournament)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 60)
    
    # Cleanup
    cleanup()


if __name__ == '__main__':
    main()
