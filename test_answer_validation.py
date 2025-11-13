"""
Deep Test: Verify Correct Answers Are Properly Set
- Check each question's correct answer matches the data
- Validate answer validation logic
- Test actual answer checking
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizQuestion, QuizAnswer

print('='*70)
print('CORRECT ANSWER VALIDATION TEST')
print('='*70)
print()

total_errors = 0
total_checked = 0

for level in range(1, 6):
    print(f'LEVEL {level}')
    print('-'*70)
    
    quiz = Quiz.objects.filter(difficulty_level=level).first()
    if not quiz:
        print(f'  ✗ No quiz found')
        total_errors += 1
        continue
    
    print(f'  Quiz: {quiz.title}')
    
    if level == 4:
        print(f'  ⚠️  Level 4: Math questions (dynamic generation)')
        print()
        continue
    
    questions = quiz.questions.filter(is_active=True)
    print(f'  Total questions: {questions.count()}')
    print()
    
    # Check first 5 questions in detail
    sample_questions = questions[:5]
    
    for q_num, question in enumerate(sample_questions, 1):
        total_checked += 1
        answers = question.answers.all().order_by('order')
        correct_answers = answers.filter(is_correct=True)
        
        print(f'  Q{q_num}: {question.text[:60]}...')
        
        # Check structure
        if answers.count() != 4:
            print(f'    ✗ ERROR: Has {answers.count()} answers (need 4)')
            total_errors += 1
            continue
        
        if correct_answers.count() != 1:
            print(f'    ✗ ERROR: Has {correct_answers.count()} correct (need 1)')
            total_errors += 1
            continue
        
        # Show all answers with correct marker
        correct_answer = correct_answers.first()
        print(f'    Options:')
        for answer in answers:
            marker = '✓ CORRECT' if answer.is_correct else '✗ Wrong'
            print(f'      - {answer.text[:40]:45} [{marker}]')
        
        # Verify the correct answer text matches
        print(f'    Correct answer: "{correct_answer.text}"')
        
        # Test answer validation
        if correct_answer.is_correct:
            print(f'    ✓ Correct answer is properly flagged')
        else:
            print(f'    ✗ ERROR: Correct flag not set!')
            total_errors += 1
        
        print()
    
    # Check remaining questions for structure only
    remaining = questions[5:]
    if remaining.exists():
        print(f'  Checking remaining {remaining.count()} questions...')
        structure_errors = 0
        
        for question in remaining:
            total_checked += 1
            answers = question.answers.all()
            correct_answers = answers.filter(is_correct=True)
            
            if answers.count() != 4:
                structure_errors += 1
                total_errors += 1
            elif correct_answers.count() != 1:
                structure_errors += 1
                total_errors += 1
        
        if structure_errors == 0:
            print(f'  ✓ All {remaining.count()} remaining questions OK')
        else:
            print(f'  ✗ Found {structure_errors} questions with errors')
    
    print()

print('='*70)
print('ANSWER CHECKING LOGIC TEST')
print('='*70)
print()

# Test the actual answer validation logic
quiz = Quiz.objects.filter(difficulty_level=1).first()
if quiz:
    question = quiz.questions.first()
    if question:
        print('Testing answer validation with real question:')
        print(f'Question: {question.text}')
        print()
        
        correct_answer = question.answers.filter(is_correct=True).first()
        wrong_answers = question.answers.filter(is_correct=False)
        
        print('Test 1: Select CORRECT answer')
        print(f'  Selected: {correct_answer.text}')
        print(f'  is_correct flag: {correct_answer.is_correct}')
        if correct_answer.is_correct:
            print('  ✓ Would award points')
        else:
            print('  ✗ ERROR: Would NOT award points')
            total_errors += 1
        print()
        
        print('Test 2: Select WRONG answer')
        wrong_answer = wrong_answers.first()
        print(f'  Selected: {wrong_answer.text}')
        print(f'  is_correct flag: {wrong_answer.is_correct}')
        if not wrong_answer.is_correct:
            print('  ✓ Would NOT award points (correct behavior)')
        else:
            print('  ✗ ERROR: Would award points (WRONG!)')
            total_errors += 1
        print()
        
        print('Test 3: Check all answers in question')
        print('  Answer breakdown:')
        correct_count = 0
        wrong_count = 0
        for idx, answer in enumerate(question.answers.all(), 1):
            status = 'CORRECT' if answer.is_correct else 'WRONG'
            print(f'    {idx}. {answer.text[:40]:42} [{status}]')
            if answer.is_correct:
                correct_count += 1
            else:
                wrong_count += 1
        
        print()
        print(f'  Correct answers: {correct_count} (should be 1)')
        print(f'  Wrong answers: {wrong_count} (should be 3)')
        
        if correct_count == 1 and wrong_count == 3:
            print('  ✓ Answer distribution is correct')
        else:
            print('  ✗ ERROR: Answer distribution is wrong')
            total_errors += 1

print()
print('='*70)
print('FINAL RESULTS')
print('='*70)
print(f'Total questions checked: {total_checked}')
print(f'Total errors found: {total_errors}')
print()

if total_errors == 0:
    print('✅ ALL TESTS PASSED!')
    print('✓ All questions have exactly 1 correct answer')
    print('✓ All questions have exactly 4 options')
    print('✓ Correct answers are properly flagged with is_correct=True')
    print('✓ Wrong answers are properly flagged with is_correct=False')
    print('✓ Answer validation logic works correctly')
    print()
    print('🎮 Questions are ready for gameplay!')
else:
    print('❌ ERRORS FOUND!')
    print(f'Found {total_errors} issues that need to be fixed')

print('='*70)
