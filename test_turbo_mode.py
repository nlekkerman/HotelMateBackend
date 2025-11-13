"""
Test Turbo Mode Scoring
Verifies 5-second timer and multiplier doubling logic
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizSession, QuizSubmission, QuizQuestion

print('='*70)
print('TURBO MODE SCORING TEST')
print('='*70)
print()

# Get any quiz
quiz = Quiz.objects.filter(is_active=True).first()

if not quiz:
    print('❌ No quiz found!')
    exit(1)

# Create test session
session = QuizSession.objects.create(
    quiz=quiz,
    hotel_identifier='test-hotel',
    player_name='Test Player'
)

print(f'Created test session: {session.id}')
print(f'Quiz: {quiz.title}')
print()

# Get a question (or use None for math)
if quiz.is_math_quiz:
    question = None
    question_data = {'correct_answer': '10', 'question': '5 + 5'}
    question_text = 'What is 5 + 5?'
else:
    question = quiz.questions.first()
    question_data = None
    question_text = question.text if question else 'Test'

print('TURBO MODE RULES:')
print('  - 5 points max per question')
print('  - -1 point per second taken (5 sec timer)')
print('  - Correct streak: 1x -> 2x -> 4x -> 8x -> 16x...')
print('  - Wrong answer: reset to 1x')
print()

# Test scenarios
scenarios = [
    {'time': 1, 'correct': True, 'answer': '10', 'desc': 'Q1: Fast correct (1s)'},
    {'time': 2, 'correct': True, 'answer': '10', 'desc': 'Q2: Medium correct (2s)'},
    {'time': 3, 'correct': True, 'answer': '10', 'desc': 'Q3: Slow correct (3s)'},
    {'time': 1, 'correct': True, 'answer': '10', 'desc': 'Q4: Fast correct (1s)'},
    {'time': 5, 'correct': True, 'answer': '10', 'desc': 'Q5: Timeout correct (5s)'},
    {'time': 2, 'correct': False, 'answer': 'wrong', 'desc': 'Q6: Wrong answer'},
    {'time': 1, 'correct': True, 'answer': '10', 'desc': 'Q7: After reset (1s)'},
]

print('SIMULATION:')
print()

for idx, scenario in enumerate(scenarios, 1):
    time_taken = scenario['time']
    is_correct = scenario['correct']
    answer = scenario['answer']
    desc = scenario['desc']
    
    # Get current state before submission
    mult_before = session.current_multiplier
    streak_before = session.consecutive_correct
    
    # Create submission
    if question:
        correct_answer = question.answers.filter(is_correct=True).first()
        selected = correct_answer.text if is_correct else 'Wrong Answer'
        submission = QuizSubmission.objects.create(
            session=session,
            hotel_identifier=session.hotel_identifier,
            question=question,
            question_text=question.text,
            selected_answer=selected,
            is_correct=is_correct,
            base_points=5,
            time_taken_seconds=time_taken
        )
    else:
        submission = QuizSubmission.objects.create(
            session=session,
            hotel_identifier=session.hotel_identifier,
            question_text=question_text,
            question_data=question_data,
            selected_answer=answer,
            is_correct=is_correct,
            base_points=5,
            time_taken_seconds=time_taken
        )
    
    # Refresh session to see updated values
    session.refresh_from_db()
    
    # Calculate what points should be
    base = max(0, 5 - time_taken)
    expected_points = base * mult_before if is_correct else 0
    
    status = 'OK' if is_correct else 'WRONG'
    print(f'{status} {desc}')
    print(f'   Time: {time_taken}s -> Base: {base} pts')
    print(f'   Multiplier used: {mult_before}x -> Score: {submission.points_awarded} pts')
    
    if is_correct:
        print(f'   Streak: {streak_before} -> {session.consecutive_correct}')
        print(f'   Next multiplier: {session.current_multiplier}x')
    else:
        print(f'   RESET! Streak: {streak_before} -> {session.consecutive_correct}')
        print(f'   Multiplier reset to: {session.current_multiplier}x')
    
    print(f'   Session total: {session.score} pts')
    print()

print('='*70)
print('SUMMARY')
print('='*70)
print(f'Final Score: {session.score} pts')
print(f'Final Streak: {session.consecutive_correct}')
print(f'Final Multiplier: {session.current_multiplier}x')
print()

# Clean up
session.delete()
print('✓ Test complete! (Test data cleaned up)')
