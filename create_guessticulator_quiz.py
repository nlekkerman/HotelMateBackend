"""
Create Guessticulator Quiz with all categories and generate QR code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import Quiz, QuizQuestion, QuizAnswer
from datetime import timedelta


def create_guessticulator_quiz():
    """Create the main Guessticulator quiz"""
    print("\n=== Creating Guessticulator The Quizculator Quiz ===")
    
    quiz, created = Quiz.objects.get_or_create(
        slug='guessticulator-the-quizculator',
        defaults={
            'title': 'Guessticulator The Quizculator',
            'description': (
                'Test your knowledge across 5 categories! '
                'Play 50 questions (10 per category) and compete for the top spot.'
            ),
            'difficulty_level': 3,  # Mixed difficulty
            'is_active': True,
            'max_questions': 50,
            'is_daily': True
        }
    )
    
    if created:
        print(f"✅ Created new quiz: {quiz.title}")
    else:
        print(f"⚠️  Quiz already exists: {quiz.title}")
    
    return quiz


def copy_questions_to_quiz(target_quiz):
    """Copy ALL questions from each category to target quiz"""
    print("\n=== Copying ALL Questions from Each Category ===")
    
    # Map old quizzes to categories
    source_quizzes = [
        ('classic-trivia-easy', 1),
        ('odd-one-out-moderate', 2),
        ('fill-the-blank-challenging', 3),
        ('knowledge-trap-expert', 5)
    ]
    
    total_copied = 0
    current_order = 0
    
    for quiz_slug, category in source_quizzes:
        try:
            source_quiz = Quiz.objects.get(slug=quiz_slug)
            questions = QuizQuestion.objects.filter(
                quiz=source_quiz,
                is_active=True
            )
            
            print(f"\nCategory {category}: Copying {questions.count()} questions")
            
            for question in questions:
                # Check if already copied
                existing = QuizQuestion.objects.filter(
                    quiz=target_quiz,
                    text=question.text,
                    difficulty_level=category
                ).exists()
                
                if existing:
                    continue
                
                # Get answers
                answers = list(question.answers.all())
                
                # Create new question with unique order
                new_question = QuizQuestion.objects.create(
                    quiz=target_quiz,
                    text=question.text,
                    image_url=question.image_url,
                    difficulty_level=category,
                    order=current_order,
                    base_points=10 * category,
                    is_active=True
                )
                current_order += 1
                
                # Copy answers
                for answer in answers:
                    QuizAnswer.objects.create(
                        question=new_question,
                        text=answer.text,
                        is_correct=answer.is_correct,
                        order=answer.order
                    )
                
                total_copied += 1
            
            print(f"  ✅ Copied {questions.count()} questions")
            
        except Quiz.DoesNotExist:
            print(f"  ⚠️  Quiz '{quiz_slug}' not found, skipping...")
    
    print(f"\n✅ Total questions copied: {total_copied}")
    return total_copied


def generate_qr_code(quiz):
    """Generate QR code for the quiz"""
    print("\n=== Generating QR Code ===")
    
    try:
        success = quiz.generate_qr_code()
        
        if success:
            print("✅ QR Code generated successfully!")
            print(f"\n   QR Code URL: {quiz.qr_code_url}")
            print(f"   Game URL: https://hotelsmates.com/games/quiz")
            print(f"   Generated at: {quiz.qr_generated_at}")
            print("\n   📱 Players can scan this QR code to play!")
            return True
        else:
            print("❌ Failed to generate QR code")
            return False
            
    except Exception as e:
        print(f"❌ Error generating QR code: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_quiz_structure(quiz):
    """Verify the quiz has questions in all categories"""
    print("\n=== Verifying Quiz Structure ===")
    print("(Category 4 = Dynamic Math, questions generated at runtime)")
    
    for category in range(1, 6):
        count = QuizQuestion.objects.filter(
            quiz=quiz,
            difficulty_level=category,
            is_active=True
        ).count()
        
        if category == 4:
            print(f"✅ Category {category}: {count} (Math - dynamic)")
        else:
            status = "✅" if count >= 10 else "⚠️"
            print(f"{status} Category {category}: {count} questions")
    
    total = QuizQuestion.objects.filter(quiz=quiz, is_active=True).count()
    print(f"\n✅ Total saved questions: {total}")
    print("   Each session will randomly select 10 per category = 50 total")


def main():
    print("=" * 70)
    print("CREATE GUESSTICULATOR THE QUIZCULATOR")
    print("=" * 70)
    
    # Create quiz
    quiz = create_guessticulator_quiz()
    
    # Check if questions exist
    existing_count = QuizQuestion.objects.filter(quiz=quiz).count()
    
    if existing_count > 0:
        print(f"\n⚠️  Quiz already has {existing_count} questions")
        recopy = input("Copy questions again? (y/n): ").strip().lower()
        if recopy == 'y':
            # Delete existing questions first
            print("Deleting existing questions...")
            QuizAnswer.objects.filter(question__quiz=quiz).delete()
            QuizQuestion.objects.filter(quiz=quiz).delete()
            copy_questions_to_quiz(quiz)
    else:
        copy_questions_to_quiz(quiz)
    
    # Verify structure
    verify_quiz_structure(quiz)
    
    # Generate QR code
    if not quiz.qr_code_url:
        generate = input("\nGenerate QR code? (y/n): ").strip().lower()
        if generate == 'y':
            generate_qr_code(quiz)
    else:
        print(f"\n✅ QR code already exists: {quiz.qr_code_url}")
        regenerate = input("Regenerate QR code? (y/n): ").strip().lower()
        if regenerate == 'y':
            generate_qr_code(quiz)
    
    # Summary
    quiz.refresh_from_db()
    print("\n" + "=" * 70)
    print("QUIZ READY!")
    print("=" * 70)
    print(f"Quiz: {quiz.title}")
    print(f"Slug: {quiz.slug}")
    print(f"Questions: {QuizQuestion.objects.filter(quiz=quiz).count()}")
    print(f"QR Code: {quiz.qr_code_url or 'Not generated'}")
    print(f"\nGame URL: https://hotelsmates.com/games/quiz")
    print("\nAPI Endpoints:")
    print(f"  Start Session: POST /api/entertainment/quiz-sessions/")
    print(f"  Leaderboard: GET /api/entertainment/quiz-sessions/all_time_leaderboard/?quiz={quiz.slug}")
    print("=" * 70)


if __name__ == '__main__':
    main()
