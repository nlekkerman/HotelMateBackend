"""Quick check of all quiz question counts"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz

print("="*50)
print("QUIZ QUESTION COUNTS")
print("="*50)

quizzes = Quiz.objects.filter(is_active=True).order_by('difficulty_level')

for quiz in quizzes:
    if quiz.is_math_quiz:
        count_display = "Dynamic (unlimited)"
    else:
        count = quiz.questions.count()
        count_display = f"{count} questions"
    
    print(f"Level {quiz.difficulty_level}: {count_display}")

print("="*50)
