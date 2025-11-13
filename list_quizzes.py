"""
Check what quiz slugs exist in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz

print("=" * 80)
print("QUIZZES IN DATABASE")
print("=" * 80)

quizzes = Quiz.objects.all()

if quizzes.exists():
    for quiz in quizzes:
        question_count = quiz.questions.filter(is_active=True).count()
        print(f"\nSlug: {quiz.slug}")
        print(f"  Title: {quiz.title}")
        print(f"  Level: {quiz.difficulty_level}")
        print(f"  Is Math: {quiz.is_math_quiz}")
        print(f"  Active: {quiz.is_active}")
        print(f"  Questions: {question_count}")
else:
    print("\n✗ No quizzes found in database!")
    print("\nYou may need to create quizzes first using Django admin or shell:")
    print("  python manage.py shell")
    print("  >>> from entertainment.models import Quiz, QuizCategory")
    print("  >>> # Create quizzes...")

print("\n" + "=" * 80)
