"""
Test that timeout (5 seconds = 0 points) BREAKS the turbo streak
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import (
    Quiz, QuizQuestion, QuizAnswer, QuizSession, QuizSubmission
)

print('='*70)
print('TIMEOUT BREAKS STREAK TEST')
print('='*70)

# Get Level 1 quiz
quiz = Quiz.objects.filter(difficulty_level=1).first()
if not quiz:
    print('ERROR: No Level 1 quiz found')
    exit(1)

# Get some questions
questions = list(quiz.questions.all()[:5])
if len(questions) < 5:
    print('ERROR: Need at least 5 questions')
    exit(1)

# Create test session
session = QuizSession.objects.create(
    quiz=quiz,
    hotel_identifier='test-hotel',
    player_name='TimeoutTester',
    room_number='Test'
)

print(f'\nStarting session: {session.player_name}')
print(f'Initial multiplier: {session.current_multiplier}x')
print()

# Test scenario: Build streak, then timeout breaks it
scenarios = [
    {'time': 1, 'desc': 'Q1: Fast correct answer'},
    {'time': 1, 'desc': 'Q2: Fast correct answer (2x multiplier)'},
    {'time': 1, 'desc': 'Q3: Fast correct answer (4x multiplier)'},
    {'time': 5, 'desc': 'Q4: TIMEOUT (0 pts, should RESET multiplier)'},
    {'time': 1, 'desc': 'Q5: Fast correct (should be back to 1x)'},
]

for idx, scenario in enumerate(scenarios):
    question = questions[idx]
    correct_answer = question.answers.filter(is_correct=True).first()
    
    time_taken = scenario['time']
    
    # Create submission
    submission = QuizSubmission.objects.create(
        hotel_identifier='test-hotel',
        session=session,
        question=question,
        question_text=question.text,
        selected_answer=correct_answer.text,
        selected_answer_id=correct_answer.id,
        is_correct=True,
        base_points=10,
        time_taken_seconds=time_taken
    )
    
    # Refresh session to see updates
    session.refresh_from_db()
    
    print(f'\n{scenario["desc"]}')
    print(f'  Time taken: {time_taken}s')
    print(f'  Base points: {5 - time_taken}')
    print(f'  Multiplier used: {submission.multiplier_used}x')
    print(f'  Points awarded: {submission.points_awarded}')
    print(f'  Consecutive correct: {session.consecutive_correct}')
    print(f'  Next multiplier: {session.current_multiplier}x')
    
    if time_taken == 5 and submission.points_awarded == 0:
        print(f'  🔥 TIMEOUT! Streak should break!')
        if session.current_multiplier == 1:
            print(f'  ✓ CORRECT: Multiplier reset to 1x')
        else:
            print(f'  ✗ ERROR: Multiplier is {session.current_multiplier}x (should be 1x)')

print()
print('='*70)
print('VERIFICATION:')
if session.current_multiplier == 2:  # After Q5 (1st correct after reset)
    print('✓ PASS: Timeout correctly broke the streak!')
    print('  Q4 timeout reset to 1x, Q5 correct brought it to 2x')
else:
    print(f'✗ FAIL: Expected 2x multiplier, got {session.current_multiplier}x')
print('='*70)

# Cleanup
session.delete()
