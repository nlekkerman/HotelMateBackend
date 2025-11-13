"""
Examine existing questions by category
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizQuestion

print("=" * 70)
print("EXAMINING EXISTING QUESTIONS BY QUIZ AND CATEGORY")
print("=" * 70)

# Get all quizzes
quizzes = Quiz.objects.filter(is_active=True)

for quiz in quizzes:
    print(f"\nQuiz: {quiz.title} (slug: {quiz.slug})")
    print(f"  Quiz difficulty_level: {quiz.difficulty_level}")
    
    # Count questions by difficulty_level
    total = 0
    for level in range(1, 6):
        count = QuizQuestion.objects.filter(
            quiz=quiz,
            difficulty_level=level,
            is_active=True
        ).count()
        if count > 0:
            print(f"  Category {level}: {count} questions")
            total += count
    
    print(f"  Total: {total} questions")

# Check if Guessticulator exists
print("\n" + "=" * 70)
guessticulator = Quiz.objects.filter(slug='guessticulator-the-quizculator').first()
if guessticulator:
    print("GUESSTICULATOR QUIZ EXISTS")
    print("=" * 70)
    print(f"Title: {guessticulator.title}")
    
    for level in range(1, 6):
        count = QuizQuestion.objects.filter(
            quiz=guessticulator,
            difficulty_level=level,
            is_active=True
        ).count()
        print(f"Category {level}: {count} questions")
    
    total = QuizQuestion.objects.filter(
        quiz=guessticulator,
        is_active=True
    ).count()
    print(f"Total: {total} questions")
else:
    print("Guessticulator quiz does not exist yet")
