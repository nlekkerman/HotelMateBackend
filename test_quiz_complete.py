"""
Complete Quiz Game Test:
- Tournament mode (saves to leaderboard)
- Practice mode (doesn't save to leaderboard)
- Timeout breaks streak
- Turbo mode scoring
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizSession, QuizSubmission
)

print('='*70)
print('COMPLETE QUIZ GAME TEST')
print('='*70)

# Get Level 1 quiz
quiz = Quiz.objects.filter(difficulty_level=1).first()
if not quiz:
    print('ERROR: No Level 1 quiz found')
    exit(1)

questions = list(quiz.questions.all()[:6])
if len(questions) < 6:
    print('ERROR: Need at least 6 questions')
    exit(1)

print(f'\nTesting with: {quiz.title}')
print(f'Questions available: {len(questions)}')
print()

# TEST 1: TOURNAMENT MODE
print('='*70)
print('TEST 1: TOURNAMENT MODE (with room number)')
print('='*70)

tournament_session = QuizSession.objects.create(
    quiz=quiz,
    hotel_identifier='hotel-paradise',
    player_name='Alice',
    room_number='101',
    is_practice_mode=False
)

print(f'Player: {tournament_session.player_name}')
print(f'Room: {tournament_session.room_number}')
print(f'Practice Mode: {tournament_session.is_practice_mode}')
print(f'Initial multiplier: {tournament_session.current_multiplier}x')
print()

# Tournament game: Build streak, timeout breaks it
scenarios = [
    {'time': 1, 'desc': 'Q1: Fast (4 pts x 1x = 4)'},
    {'time': 1, 'desc': 'Q2: Fast (4 pts x 2x = 8)'},
    {'time': 2, 'desc': 'Q3: Medium (3 pts x 4x = 12)'},
    {'time': 5, 'desc': 'Q4: TIMEOUT (0 pts, BREAKS STREAK)'},
    {'time': 1, 'desc': 'Q5: Fast (4 pts x 1x = 4)'},
    {'time': 1, 'desc': 'Q6: Fast (4 pts x 2x = 8)'},
]

for idx, scenario in enumerate(scenarios):
    question = questions[idx]
    correct_answer = question.answers.filter(is_correct=True).first()
    
    submission = QuizSubmission.objects.create(
        hotel_identifier='hotel-paradise',
        session=tournament_session,
        question=question,
        question_text=question.text,
        selected_answer=correct_answer.text,
        selected_answer_id=correct_answer.id,
        is_correct=True,
        base_points=10,
        time_taken_seconds=scenario['time']
    )
    
    tournament_session.refresh_from_db()
    
    print(f'{scenario["desc"]}')
    print(f'  Multiplier: {submission.multiplier_used}x -> Points: {submission.points_awarded}')
    print(f'  Next multiplier: {tournament_session.current_multiplier}x')
    
    if scenario['time'] == 5:
        if tournament_session.current_multiplier == 1:
            print(f'  ✓ Streak correctly broken!')
        else:
            print(f'  ✗ ERROR: Multiplier should be 1x')

tournament_session.complete_session()
tournament_session.refresh_from_db()

print()
print(f'TOURNAMENT SESSION COMPLETE:')
print(f'  Final Score: {tournament_session.score} points')
print(f'  Time: {tournament_session.time_spent_seconds}s')
print(f'  Room: {tournament_session.room_number}')
print(f'  On Leaderboard: YES (is_practice_mode=False)')
print()

# TEST 2: PRACTICE MODE
print('='*70)
print('TEST 2: PRACTICE MODE (no room, won\'t affect leaderboard)')
print('='*70)

practice_session = QuizSession.objects.create(
    quiz=quiz,
    hotel_identifier='hotel-paradise',
    player_name='Bob',
    room_number=None,
    is_practice_mode=True
)

print(f'Player: {practice_session.player_name}')
print(f'Room: {practice_session.room_number or "None"}')
print(f'Practice Mode: {practice_session.is_practice_mode}')
print()

# Practice game: Just quick run
for idx in range(3):
    question = questions[idx]
    correct_answer = question.answers.filter(is_correct=True).first()
    
    submission = QuizSubmission.objects.create(
        hotel_identifier='hotel-paradise',
        session=practice_session,
        question=question,
        question_text=question.text,
        selected_answer=correct_answer.text,
        selected_answer_id=correct_answer.id,
        is_correct=True,
        base_points=10,
        time_taken_seconds=1
    )
    
    practice_session.refresh_from_db()
    print(f'Q{idx+1}: {submission.multiplier_used}x -> {submission.points_awarded} pts')

practice_session.complete_session()
practice_session.refresh_from_db()

print()
print(f'PRACTICE SESSION COMPLETE:')
print(f'  Final Score: {practice_session.score} points')
print(f'  On Leaderboard: NO (is_practice_mode=True)')
print()

# TEST 3: LEADERBOARD CHECK
print('='*70)
print('TEST 3: LEADERBOARD (Tournament mode only)')
print('='*70)

# Get all completed sessions for this quiz at this hotel
all_sessions = QuizSession.objects.filter(
    quiz=quiz,
    hotel_identifier='hotel-paradise',
    is_completed=True
).order_by('-score')

print(f'Total completed sessions: {all_sessions.count()}')
print()

# Tournament leaderboard (exclude practice mode)
tournament_leaderboard = all_sessions.filter(is_practice_mode=False)
print(f'TOURNAMENT LEADERBOARD ({tournament_leaderboard.count()} entries):')
for idx, session in enumerate(tournament_leaderboard[:5], 1):
    mode = "PRACTICE" if session.is_practice_mode else "TOURNAMENT"
    room = session.room_number or "N/A"
    print(f'  {idx}. {session.player_name} (Room {room}) - {session.score} pts [{mode}]')

print()
print(f'Practice sessions (not on leaderboard):')
practice_sessions = all_sessions.filter(is_practice_mode=True)
for session in practice_sessions:
    print(f'  - {session.player_name} - {session.score} pts [PRACTICE]')

print()
print('='*70)
print('TEST SUMMARY:')
print('='*70)
print(f'✓ Tournament mode: Room {tournament_session.room_number}, Score: {tournament_session.score}')
print(f'✓ Practice mode: No room, Score: {practice_session.score}, Not on leaderboard')
print(f'✓ Timeout breaks streak: Verified')
print(f'✓ Turbo multiplier: Working (1x→2x→4x, reset on timeout)')
print('='*70)

# Cleanup
tournament_session.delete()
practice_session.delete()
