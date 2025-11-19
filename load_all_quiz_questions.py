"""
Master script to load all new quiz questions
Loads Music, Astronomy, and Science categories
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

# Import the loader functions
from load_music_questions import load_music_questions  # noqa: E402
from load_astronomy_questions import (  # noqa: E402
    load_astronomy_questions
)
from load_science_questions import load_science_questions  # noqa: E402


def main():
    """Load all new quiz categories"""
    
    print("\n" + "=" * 70)
    print("🎮 LOADING NEW QUIZ CATEGORIES")
    print("=" * 70)
    
    # Load Music questions
    print("\n🎵 LOADING MUSIC QUESTIONS...")
    print("-" * 70)
    try:
        load_music_questions()
    except Exception as e:
        print(f"❌ Error loading Music questions: {e}")
    
    # Load Astronomy questions
    print("\n🌌 LOADING ASTRONOMY QUESTIONS...")
    print("-" * 70)
    try:
        load_astronomy_questions()
    except Exception as e:
        print(f"❌ Error loading Astronomy questions: {e}")
    
    # Load Science questions
    print("\n🔬 LOADING SCIENCE QUESTIONS...")
    print("-" * 70)
    try:
        load_science_questions()
    except Exception as e:
        print(f"❌ Error loading Science questions: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 ALL CATEGORIES LOADED!")
    print("=" * 70)
    
    # Show updated category count
    from entertainment.models import QuizCategory
    total_categories = QuizCategory.objects.filter(is_active=True).count()
    total_questions = sum(
        cat.question_count
        for cat in QuizCategory.objects.filter(is_active=True)
    )
    
    print(f"\n📊 Total Active Categories: {total_categories}")
    print(f"📝 Total Questions: {total_questions}")
    print("\n✅ Run 'python fetch_quiz_categories.py' to see all "
          "categories\n")


if __name__ == '__main__':
    main()
