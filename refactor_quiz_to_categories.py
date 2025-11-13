"""
Refactor Quiz System:
- Convert current quizzes (Level 1-5) into QuizCategory entries
- Keep their slugs as category slugs
- Create one main quiz: "Guessticulator The Quizculator Quiz game"
- Migrate all questions to be associated with categories
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizCategory, QuizQuestion

print("=" * 80)
print("QUIZ REFACTORING - STEP 1: DATA MIGRATION")
print("=" * 80)
print()

# Step 1: Get all existing quizzes
existing_quizzes = Quiz.objects.all()

print(f"Found {existing_quizzes.count()} existing quiz(zes)")
print()

# Step 2: Create categories from existing quizzes
print("Creating categories from existing quizzes...")
print("-" * 80)

category_mapping = {}  # Map old quiz ID to new category

for quiz in existing_quizzes:
    print(f"\nProcessing: {quiz.title}")
    print(f"  Slug: {quiz.slug}")
    print(f"  Difficulty Level: {quiz.difficulty_level}")
    print(f"  Questions: {quiz.questions.count()}")
    
    # Create category from quiz
    category, created = QuizCategory.objects.get_or_create(
        name=quiz.slug,  # Use slug as category name for now
        defaults={
            'description': quiz.description,
            'is_active': quiz.is_active,
        }
    )
    
    category_mapping[quiz.id] = category
    
    action = "Created" if created else "Found existing"
    print(f"  {action} category: {category.name}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Categories created/found: {len(category_mapping)}")
print()

# Display category mapping
print("Quiz -> Category Mapping:")
for quiz_id, category in category_mapping.items():
    quiz = Quiz.objects.get(id=quiz_id)
    print(f"  {quiz.title} -> {category.name}")

print()
print("=" * 80)
print("Next Steps:")
print("  1. Review the categories created")
print("  2. Update the Quiz model to remove difficulty_level")
print("  3. Link QuizQuestion to QuizCategory instead of Quiz")
print("  4. Create single main 'Guessticulator' quiz")
print("=" * 80)
