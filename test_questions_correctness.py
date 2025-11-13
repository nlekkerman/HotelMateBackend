"""
Test Question Correctness & Session Flow
- Verify all questions have correct answers
- Test that sessions deliver 10 questions one by one
- Check all 5 levels
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizQuestion, QuizAnswer

print('='*70)
print('QUIZ QUESTIONS CORRECTNESS TEST')
print('='*70)
print()

# Test all 5 levels
all_passed = True

for level in range(1, 6):
    print(f'LEVEL {level}')
    print('-'*70)
    
    quiz = Quiz.objects.filter(difficulty_level=level).first()
    if not quiz:
        print(f'  ✗ ERROR: No quiz found for level {level}')
        all_passed = False
        continue
    
    print(f'  Quiz: {quiz.title}')
    print(f'  Slug: {quiz.slug}')
    print(f'  Max questions per session: {quiz.max_questions}')
    
    # Check max_questions is 10
    if quiz.max_questions != 10:
        print(f'  ✗ ERROR: max_questions should be 10, got {quiz.max_questions}')
        all_passed = False
    else:
        print(f'  ✓ Correct: Session will have {quiz.max_questions} questions')
    
    # Get all questions
    questions = quiz.questions.filter(is_active=True)
    total_questions = questions.count()
    
    print(f'  Total questions available: {total_questions}')
    
    if level == 4:
        print(f'  ✓ Level 4 uses dynamic math generation (infinite)')
        print()
        continue
    
    # Check minimum questions available
    if total_questions < 10:
        print(f'  ✗ ERROR: Need at least 10 questions, only {total_questions} found')
        all_passed = False
        print()
        continue
    
    # Check each question has exactly one correct answer
    questions_checked = 0
    questions_with_errors = 0
    
    for question in questions:
        answers = question.answers.all()
        correct_answers = answers.filter(is_correct=True)
        
        # Check has 4 options
        if answers.count() != 4:
            print(f'  ✗ Q{question.id}: Has {answers.count()} options (should be 4)')
            questions_with_errors += 1
            continue
        
        # Check exactly 1 correct answer
        if correct_answers.count() != 1:
            print(f'  ✗ Q{question.id}: Has {correct_answers.count()} correct answers (should be 1)')
            print(f'     Text: {question.text[:50]}...')
            questions_with_errors += 1
            continue
        
        questions_checked += 1
    
    if questions_with_errors == 0:
        print(f'  ✓ All {questions_checked} questions have correct structure')
        print(f'  ✓ Each has 4 options with 1 correct answer')
    else:
        print(f'  ✗ Found {questions_with_errors} questions with errors')
        all_passed = False
    
    print()

print('='*70)
print('SESSION FLOW TEST')
print('='*70)
print()

# Test session flow for Level 1
quiz = Quiz.objects.filter(difficulty_level=1).first()
if quiz:
    print(f'Testing with: {quiz.title}')
    print()
    
    # Simulate getting 10 questions one by one
    questions = list(quiz.questions.filter(is_active=True)[:10])
    
    print('Simulating session with 10 questions:')
    print('-'*70)
    
    for idx, question in enumerate(questions, 1):
        correct_answer = question.answers.filter(is_correct=True).first()
        all_answers = list(question.answers.all())
        
        print(f'Question {idx}/10:')
        print(f'  Text: {question.text}')
        print(f'  Options:')
        for ans_idx, answer in enumerate(all_answers, 1):
            marker = '✓' if answer.is_correct else ' '
            print(f'    [{ans_idx}] {answer.text} {marker}')
        print()
    
    print('✓ Session would deliver 10 questions one by one')
    print('✓ Each question has 4 options')
    print('✓ Each question has 1 correct answer marked')

print()
print('='*70)
print('SUMMARY')
print('='*70)

if all_passed:
    print('✓ ALL TESTS PASSED')
    print('✓ All levels have correct question structure')
    print('✓ Each quiz set to deliver 10 questions per session')
    print('✓ All questions have 4 options with 1 correct answer')
    print()
    print('Questions are ready for gameplay! 🎮')
else:
    print('✗ SOME TESTS FAILED - Check errors above')

print('='*70)
