"""
Fetch all quizzes from the database
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizQuestion

print("=" * 80)
print("ALL QUIZZES IN DATABASE")
print("=" * 80)
print()

quizzes = Quiz.objects.all().select_related('category').prefetch_related('questions', 'questions__answers')

if not quizzes.exists():
    print("✗ No quizzes found in database!")
    print("\nTo create quizzes, use Django admin or shell:")
    print("  python manage.py shell")
    print("  >>> from entertainment.models import Quiz, QuizCategory")
else:
    print(f"Found {quizzes.count()} quiz(zes)\n")
    
    for quiz in quizzes:
        print("=" * 80)
        print(f"QUIZ ID: {quiz.id}")
        print("=" * 80)
        print(f"Title: {quiz.title}")
        print(f"Slug: {quiz.slug}")
        print(f"Category: {quiz.category.name if quiz.category else 'None'}")
        print(f"Description: {quiz.description}")
        print(f"Difficulty Level: {quiz.difficulty_level} ({quiz.get_difficulty_level_display()})")
        print(f"Is Active: {quiz.is_active}")
        print(f"Is Daily Quiz: {quiz.is_daily}")
        print(f"Max Questions: {quiz.max_questions}")
        print(f"Time per Question: {quiz.get_time_per_question()} seconds")
        print(f"Is Math Quiz: {quiz.is_math_quiz}")
        print(f"Enable Background Music: {quiz.enable_background_music}")
        print(f"Enable Sound Effects: {quiz.enable_sound_effects}")
        print(f"Sound Theme: {quiz.sound_theme}")
        print(f"QR Code URL: {quiz.qr_code_url or 'Not generated'}")
        print(f"Created At: {quiz.created_at}")
        print(f"Updated At: {quiz.updated_at}")
        
        # Get questions
        questions = quiz.questions.filter(is_active=True)
        question_count = questions.count()
        
        if quiz.is_math_quiz:
            print(f"\nQuestions: Dynamic (generated at runtime)")
        else:
            print(f"\nQuestions: {question_count}")
            
            if question_count > 0:
                print("\n--- Questions ---")
                for i, question in enumerate(questions, 1):
                    print(f"\n  Q{i}. {question.text[:100]}{'...' if len(question.text) > 100 else ''}")
                    print(f"     Order: {question.order}")
                    print(f"     Base Points: {question.base_points}")
                    print(f"     Difficulty: {question.difficulty_level}")
                    
                    # Get answers
                    answers = question.answers.all()
                    if answers.exists():
                        print(f"     Answers ({answers.count()}):")
                        for answer in answers:
                            correct_mark = "✓" if answer.is_correct else "✗"
                            print(f"       {correct_mark} {answer.text[:80]}{'...' if len(answer.text) > 80 else ''}")
        
        print()

print("\n" + "=" * 80)
print("END OF QUIZ LIST")
print("=" * 80)
