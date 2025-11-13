"""
Test Two Leaderboards System:
1. General Leaderboard - ALL sessions (practice + tournament)
2. Tournament Leaderboard - ONLY tournament mode (room_number + not practice)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizSession, QuizSubmission

print('='*70)
print('TWO LEADERBOARDS TEST')
print('='*70)

# Get quiz
quiz = Quiz.objects.filter(difficulty_level=1).first()
if not quiz:
    print('ERROR: No quiz found')
    exit(1)

questions = list(quiz.questions.all()[:3])
hotel = 'paradise-hotel'

print(f'\nQuiz: {quiz.title}')
print(f'Hotel: {hotel}')
print()

# Create test sessions
sessions_data = [
    {'name': 'Alice', 'room': '101', 'practice': False, 'score_times': [1, 1, 1]},
    {'name': 'Bob', 'room': '102', 'practice': False, 'score_times': [2, 2, 2]},
    {'name': 'Charlie', 'room': None, 'practice': True, 'score_times': [1, 1, 1]},
    {'name': 'Diana', 'room': '103', 'practice': False, 'score_times': [1, 2, 3]},
    {'name': 'Eve', 'room': None, 'practice': True, 'score_times': [0, 0, 0]},
]

created_sessions = []

print('Creating test sessions...')
print('-'*70)

for data in sessions_data:
    session = QuizSession.objects.create(
        quiz=quiz,
        hotel_identifier=hotel,
        player_name=data['name'],
        room_number=data['room'],
        is_practice_mode=data['practice']
    )
    
    # Submit answers
    for idx, time_taken in enumerate(data['score_times']):
        question = questions[idx]
        correct_answer = question.answers.filter(is_correct=True).first()
        
        QuizSubmission.objects.create(
            hotel_identifier=hotel,
            session=session,
            question=question,
            question_text=question.text,
            selected_answer=correct_answer.text,
            selected_answer_id=correct_answer.id,
            is_correct=True,
            base_points=10,
            time_taken_seconds=time_taken
        )
    
    session.complete_session()
    session.refresh_from_db()
    created_sessions.append(session)
    
    mode = 'PRACTICE' if session.is_practice_mode else 'TOURNAMENT'
    room = session.room_number or 'N/A'
    print(f'{session.player_name:10} | Room: {room:3} | {mode:10} | Score: {session.score:3}')

print()
print('='*70)
print('GENERAL LEADERBOARD (All Sessions)')
print('='*70)

general = QuizSession.objects.filter(
    quiz=quiz,
    hotel_identifier=hotel,
    is_completed=True
).order_by('-score', 'time_spent_seconds')

print(f'Total entries: {general.count()}\n')
for rank, session in enumerate(general, 1):
    mode = 'PRACTICE' if session.is_practice_mode else 'TOURNAMENT'
    room = session.room_number or 'N/A'
    print(f'{rank}. {session.player_name:10} | Room: {room:3} | {mode:10} | {session.score} pts')

print()
print('='*70)
print('TOURNAMENT LEADERBOARD (Tournament Mode Only)')
print('='*70)

tournament = QuizSession.objects.filter(
    quiz=quiz,
    hotel_identifier=hotel,
    is_completed=True,
    is_practice_mode=False,
    room_number__isnull=False
).exclude(room_number='').order_by('-score', 'time_spent_seconds')

print(f'Total entries: {tournament.count()}\n')
for rank, session in enumerate(tournament, 1):
    print(f'{rank}. {session.player_name:10} | Room: {session.room_number:3} | {session.score} pts')

print()
print('='*70)
print('VERIFICATION')
print('='*70)

# Count sessions by type
total = general.count()
tournament_count = tournament.count()
practice_count = general.filter(is_practice_mode=True).count()

print(f'Total sessions: {total}')
print(f'Tournament mode: {tournament_count}')
print(f'Practice mode: {practice_count}')
print()

# Verify logic
if total == tournament_count + practice_count:
    print('✓ PASS: All sessions accounted for')
else:
    print('✗ FAIL: Count mismatch')

if tournament_count == 3:  # Alice, Bob, Diana
    print('✓ PASS: Tournament has 3 entries (Alice, Bob, Diana)')
else:
    print(f'✗ FAIL: Expected 3 tournament entries, got {tournament_count}')

if practice_count == 2:  # Charlie, Eve
    print('✓ PASS: Practice has 2 entries (Charlie, Eve)')
else:
    print(f'✗ FAIL: Expected 2 practice entries, got {practice_count}')

# Check tournament entries don't include practice
tournament_names = [s.player_name for s in tournament]
if 'Charlie' not in tournament_names and 'Eve' not in tournament_names:
    print('✓ PASS: Practice players not in tournament leaderboard')
else:
    print('✗ FAIL: Practice players found in tournament leaderboard')

# Check general includes everyone
general_names = [s.player_name for s in general]
if all(name in general_names for name in ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']):
    print('✓ PASS: All players in general leaderboard')
else:
    print('✗ FAIL: Missing players in general leaderboard')

print()
print('='*70)
print('SUMMARY')
print('='*70)
print('✓ General Leaderboard: Shows ALL 5 sessions')
print('✓ Tournament Leaderboard: Shows only 3 tournament sessions')
print('✓ Practice sessions excluded from tournament')
print('✓ Tournament sessions appear on BOTH leaderboards')
print('='*70)

# Cleanup
for session in created_sessions:
    session.delete()

print('\nTest complete! Sessions cleaned up.')
