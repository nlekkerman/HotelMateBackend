"""
Fetch all Quiz Categories from the database
Displays category details including name, slug, icon, color, and question count
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import QuizCategory  # noqa: E402


def fetch_quiz_categories():
    """Fetch and display all quiz categories"""
    
    print("=" * 80)
    print("QUIZ CATEGORIES IN DATABASE")
    print("=" * 80)
    
    # Fetch all categories (question_count is a property on the model)
    categories = QuizCategory.objects.all().order_by('display_order', 'name')
    
    if not categories.exists():
        print("\n❌ No quiz categories found in database!")
        print("💡 You may need to create categories via Django admin "
              "or load scripts.")
        return
    
    print(f"\n✅ Found {categories.count()} quiz categories:\n")
    
    # Display all categories
    for idx, category in enumerate(categories, 1):
        print(f"{idx}. {category}")
        print(f"   ID: {category.id}")
        print(f"   Name: {category.name}")
        print(f"   Slug: {category.slug}")
        print(f"   Icon: {category.icon}")
        print(f"   Color: {category.color}")
        print(f"   Active: {'✅ Yes' if category.is_active else '❌ No'}")
        print(f"   Display Order: {category.display_order}")
        print(f"   Questions: {category.question_count}")
        desc = category.description
        if len(desc) > 60:
            print(f"   Description: {desc[:60]}...")
        else:
            print(f"   Description: {desc}")
        created = category.created_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"   Created: {created}")
        updated = category.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"   Updated: {updated}")
        print("-" * 80)
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    active_count = categories.filter(is_active=True).count()
    inactive_count = categories.filter(is_active=False).count()
    total_questions = sum(cat.question_count for cat in categories)
    
    print(f"Total Categories: {categories.count()}")
    print(f"Active Categories: {active_count}")
    print(f"Inactive Categories: {inactive_count}")
    print(f"Total Questions: {total_questions}")
    
    if active_count > 0:
        print(f"\n✅ {active_count} active categories available for "
              f"quiz slot machine!")
    else:
        print("\n⚠️ No active categories! Enable at least one category.")
    
    print("=" * 80)


if __name__ == '__main__':
    try:
        fetch_quiz_categories()
    except Exception as e:
        print(f"\n❌ Error fetching quiz categories: {e}")
        import traceback
        traceback.print_exc()
