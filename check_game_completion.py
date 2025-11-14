import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizCategory

quiz = Quiz.objects.get(slug='guessticulator')
active_categories = QuizCategory.objects.filter(is_active=True).count()
questions_per_category = quiz.questions_per_category
total_questions = questions_per_category * active_categories

print("=" * 70)
print("GAME COMPLETION CHECK")
print("=" * 70)
print(f"Questions per category: {questions_per_category}")
print(f"Active categories: {active_categories}")
print(f"Total questions expected: {total_questions}")
print("=" * 70)

# The issue: The backend should return game_completed: true when 
# total_submissions >= total_questions (which is 50)
# But frontend is checking for move_to_next_question, which backend ALWAYS returns True

print("\nBACKEND LOGIC:")
print("- When total_submissions >= 50:")
print("  - game_completed = True")
print("  - session.is_completed = True")
print("  - move_to_next_question = True (always)")
print("\nFRONTEND SHOULD CHECK:")
print("- if (response.game_completed === true) { completeGame(); }")
print("- NOT: if (response.move_to_next_question) { moveNext(); }")
