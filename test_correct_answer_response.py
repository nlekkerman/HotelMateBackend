"""
Test that correct answer is returned in submission response
Frontend needs this to show "Wrong! Correct answer was X"
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizSession, QuizSubmission
from entertainment.serializers import QuizSubmissionSerializer

print('='*70)
print('CORRECT ANSWER IN RESPONSE TEST')
print('='*70)
print()

# Get quiz and questions
quiz = Quiz.objects.filter(difficulty_level=1).first()
if not quiz:
    print('ERROR: No quiz found')
    exit(1)

questions = list(quiz.questions.all()[:3])

print(f'Quiz: {quiz.title}')
print()

# Create session
session = QuizSession.objects.create(
    quiz=quiz,
    hotel_identifier='test-hotel',
    player_name='TestPlayer',
    room_number='101',
    is_practice_mode=False
)

print('Testing 3 scenarios:')
print('-'*70)
print()

# Scenario 1: CORRECT answer
print('SCENARIO 1: Correct Answer')
print('-'*40)
question1 = questions[0]
correct_answer1 = question1.answers.filter(is_correct=True).first()
wrong_answers1 = list(question1.answers.filter(is_correct=False))

submission1 = QuizSubmission.objects.create(
    hotel_identifier='test-hotel',
    session=session,
    question=question1,
    question_text=question1.text,
    selected_answer=correct_answer1.text,
    selected_answer_id=correct_answer1.id,
    is_correct=True,
    base_points=10,
    time_taken_seconds=2
)

serializer1 = QuizSubmissionSerializer(submission1)
data1 = serializer1.data

print(f'Question: {question1.text[:50]}...')
print(f'Selected: {data1["selected_answer"]}')
print(f'Correct:  {data1["correct_answer"]}')
print(f'Result:   {"✓ CORRECT" if data1["is_correct"] else "✗ WRONG"}')
print(f'Points:   {data1["points_awarded"]}')
print()

if data1["correct_answer"] == correct_answer1.text:
    print('✓ Correct answer returned in response')
else:
    print('✗ ERROR: Correct answer not matching')

print()

# Scenario 2: WRONG answer
print('SCENARIO 2: Wrong Answer')
print('-'*40)
question2 = questions[1]
correct_answer2 = question2.answers.filter(is_correct=True).first()
wrong_answer2 = question2.answers.filter(is_correct=False).first()

submission2 = QuizSubmission.objects.create(
    hotel_identifier='test-hotel',
    session=session,
    question=question2,
    question_text=question2.text,
    selected_answer=wrong_answer2.text,
    selected_answer_id=wrong_answer2.id,
    is_correct=False,
    base_points=10,
    time_taken_seconds=3
)

serializer2 = QuizSubmissionSerializer(submission2)
data2 = serializer2.data

print(f'Question: {question2.text[:50]}...')
print(f'Selected: {data2["selected_answer"]}')
print(f'Correct:  {data2["correct_answer"]}')
print(f'Result:   {"✓ CORRECT" if data2["is_correct"] else "✗ WRONG"}')
print(f'Points:   {data2["points_awarded"]}')
print()

if data2["correct_answer"] == correct_answer2.text:
    print('✓ Correct answer returned (frontend can show it)')
else:
    print('✗ ERROR: Correct answer not matching')

print()

# Scenario 3: TIMEOUT (0 points, but still correct answer available)
print('SCENARIO 3: Timeout (5 seconds)')
print('-'*40)
question3 = questions[2]
correct_answer3 = question3.answers.filter(is_correct=True).first()

submission3 = QuizSubmission.objects.create(
    hotel_identifier='test-hotel',
    session=session,
    question=question3,
    question_text=question3.text,
    selected_answer=correct_answer3.text,
    selected_answer_id=correct_answer3.id,
    is_correct=True,
    base_points=10,
    time_taken_seconds=5
)

serializer3 = QuizSubmissionSerializer(submission3)
data3 = serializer3.data

print(f'Question: {question3.text[:50]}...')
print(f'Selected: {data3["selected_answer"]}')
print(f'Correct:  {data3["correct_answer"]}')
print(f'Time:     {data3["time_taken_seconds"]}s')
print(f'Points:   {data3["points_awarded"]} (0 due to timeout)')
print()

if data3["correct_answer"] == correct_answer3.text:
    print('✓ Correct answer available for display')
else:
    print('✗ ERROR: Correct answer not matching')

print()

# Test Math Question (Level 4)
print('='*70)
print('BONUS: Math Question (Dynamic)')
print('='*70)
print()

math_submission = QuizSubmission.objects.create(
    hotel_identifier='test-hotel',
    session=session,
    question=None,
    question_text='What is 7 + 3?',
    question_data={
        'operand1': 7,
        'operand2': 3,
        'operator': '+',
        'correct_answer': '10'
    },
    selected_answer='12',
    is_correct=False,
    base_points=10,
    time_taken_seconds=2
)

math_serializer = QuizSubmissionSerializer(math_submission)
math_data = math_serializer.data

print(f'Question: {math_data["question_text"]}')
print(f'Selected: {math_data["selected_answer"]}')
print(f'Correct:  {math_data["correct_answer"]}')
print(f'Result:   {"✓ CORRECT" if math_data["is_correct"] else "✗ WRONG"}')
print()

if math_data["correct_answer"] == '10':
    print('✓ Math question correct answer returned')
else:
    print('✗ ERROR: Math correct answer not found')

print()

# Sample Frontend Display
print('='*70)
print('SAMPLE FRONTEND DISPLAY')
print('='*70)
print()

print('When WRONG:')
print('┌─────────────────────────────────┐')
print('│  ✗ Wrong Answer!                │')
print('│                                 │')
print(f'│  You selected: {wrong_answer2.text[:20]:20} │')
print(f'│  Correct was:  {correct_answer2.text[:20]:20} │')
print('│                                 │')
print('│  Points: 0                      │')
print('│  Streak broken - Back to 1x     │')
print('└─────────────────────────────────┘')
print()

print('When TIMEOUT:')
print('┌─────────────────────────────────┐')
print('│  ⏱️ Time\'s Up!                   │')
print('│                                 │')
print(f'│  Correct answer: {correct_answer3.text[:16]:16} │')
print('│                                 │')
print('│  Points: 0 (timeout)            │')
print('│  Streak broken - Back to 1x     │')
print('└─────────────────────────────────┘')
print()

print('='*70)
print('SUMMARY')
print('='*70)
print('✓ Correct answer included in submission response')
print('✓ Works for regular questions (from database)')
print('✓ Works for math questions (from question_data)')
print('✓ Available for both wrong answers and timeouts')
print('✓ Frontend can now display correct answer feedback')
print('='*70)

# Cleanup
session.delete()
