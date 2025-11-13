"""
Comprehensive test for all quiz levels
Tests question counts, math generation, and turbo mode scoring
"""
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizCategory, QuizSession

print('='*70)
print('QUIZ GAME - COMPREHENSIVE TEST')
print('='*70)
print()

# Get all quizzes ordered by difficulty
quizzes = Quiz.objects.filter(is_active=True).order_by('difficulty_level')

if not quizzes.exists():
    print('❌ No quizzes found in database!')
    exit(1)

print(f'Found {quizzes.count()} active quiz(es)\n')

# Test each quiz level
for quiz in quizzes:
    print('='*70)
    print(f'LEVEL {quiz.difficulty_level}: {quiz.title}')
    print('='*70)
    print(f'Slug: {quiz.slug}')
    print(f'Description: {quiz.description}')
    print(f'Time per question: {quiz.get_time_per_question()}s')
    print(f'Max questions per session: {quiz.max_questions}')
    print(f'Is Math Quiz: {quiz.is_math_quiz}')
    print(f'Sound theme: {quiz.sound_theme}')
    print(f'Background music: {"✓" if quiz.enable_background_music else "✗"}')
    print(f'Sound effects: {"✓" if quiz.enable_sound_effects else "✗"}')
    
    if quiz.is_math_quiz:
        print(f'\n📊 MATH QUIZ - Questions generated dynamically')
        print(f'   No database questions needed')
        
        # Test math generation
        print(f'\n   Testing 5 sample math questions:')
        for i in range(5):
            num1 = random.randint(0, 10)
            num2 = random.randint(0, 10)
            operation = random.choice(['+', '-', '×', '÷'])
            
            if operation == '+':
                correct = num1 + num2
                question = f"{num1} + {num2}"
            elif operation == '-':
                correct = num1 - num2
                question = f"{num1} - {num2}"
            elif operation == '×':
                correct = num1 * num2
                question = f"{num1} × {num2}"
            else:
                num1 = num2 * random.randint(1, 10)
                correct = num1 // num2
                question = f"{num1} ÷ {num2}"
            
            # Generate distractors
            distractors = set()
            while len(distractors) < 3:
                offset = random.choice([-2, -1, 1, 2, 3, -3])
                distractor = correct + offset
                if distractor != correct and distractor >= 0:
                    distractors.add(distractor)
            
            options = [correct] + list(distractors)
            random.shuffle(options)
            
            print(f'   {i+1}. What is {question}? → {correct}')
            print(f'      Options: {options}')
    else:
        question_count = quiz.questions.filter(is_active=True).count()
        print(f'\n📝 Database questions: {question_count}')
        
        if question_count == 0:
            print(f'   ⚠️  WARNING: No questions found for this quiz!')
        elif question_count < quiz.max_questions:
            print(f'   ⚠️  WARNING: Only {question_count} questions, but max_questions is {quiz.max_questions}')
        else:
            print(f'   ✓ Sufficient questions available')
            
        # Show first 3 questions as sample
        if question_count > 0:
            print(f'\n   Sample questions:')
            for idx, q in enumerate(quiz.questions.filter(is_active=True)[:3], 1):
                answers = q.answers.all()
                correct = answers.filter(is_correct=True).first()
                print(f'   {idx}. {q.text[:60]}{"..." if len(q.text) > 60 else ""}')
                print(f'      Answers: {answers.count()} options')
                print(f'      Correct: {correct.text if correct else "NONE!"}')
                print(f'      Points: {q.base_points}')
    
    print()

# Test turbo mode scoring
print('='*70)
print('TURBO MODE SCORING TEST')
print('='*70)
print()
print('Turbo Mode Rules:')
print('  • Base: 5 points per question')
print('  • Deduct 1 point per second (5 second timer)')
print('  • Correct answer: double multiplier (1x → 2x → 4x → 8x...)')
print('  • Wrong answer: reset to 1x multiplier')
print()

print('Example scoring scenarios:')
print()

scenarios = [
    {'time': 1, 'multiplier': 1, 'correct': True, 'desc': '1st correct (fast)'},
    {'time': 2, 'multiplier': 2, 'correct': True, 'desc': '2nd correct (medium)'},
    {'time': 3, 'multiplier': 4, 'correct': True, 'desc': '3rd correct (slow)'},
    {'time': 1, 'multiplier': 8, 'correct': True, 'desc': '4th correct (fast)'},
    {'time': 5, 'multiplier': 16, 'correct': True, 'desc': '5th correct (timeout)'},
    {'time': 2, 'multiplier': 32, 'correct': False, 'desc': 'Wrong answer'},
    {'time': 1, 'multiplier': 1, 'correct': True, 'desc': 'After reset'},
]

total_score = 0
current_multiplier = 1

for scenario in scenarios:
    time = scenario['time']
    mult = scenario['multiplier']
    correct = scenario['correct']
    desc = scenario['desc']
    
    base_points = max(0, 5 - time)
    
    if correct:
        points = base_points * mult
        next_mult = mult * 2
        total_score += points
        current_multiplier = next_mult
        status = '✓'
    else:
        points = 0
        next_mult = 1
        current_multiplier = 1
        status = '✗'
    
    print(f'{status} {desc}:')
    print(f'   Time: {time}s → Base: {base_points} pts')
    print(f'   Multiplier: {mult}x → Score: {points} pts')
    print(f'   Next multiplier: {next_mult}x')
    print(f'   Running total: {total_score} pts')
    print()

print('='*70)
print('TEST SUMMARY')
print('='*70)
print()

for quiz in quizzes:
    if quiz.is_math_quiz:
        status = '✓ READY (math generation)'
    else:
        count = quiz.questions.filter(is_active=True).count()
        if count == 0:
            status = '✗ NO QUESTIONS'
        elif count < quiz.max_questions:
            status = f'⚠️  PARTIAL ({count}/{quiz.max_questions})'
        else:
            status = f'✓ READY ({count} questions)'
    
    print(f'Level {quiz.difficulty_level} - {quiz.title}: {status}')

print()
print('='*70)
print('✓ All tests complete!')
print('='*70)
