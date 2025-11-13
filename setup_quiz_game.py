"""
Setup script for Guessticulator Quiz Game
Creates categories, quiz, sample questions, and tournament
"""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import (
    Quiz, QuizCategory, QuizQuestion, QuizAnswer, QuizTournament
)

def create_categories():
    """Create the 5 quiz categories"""
    categories = [
        {
            'name': 'Classic Trivia',
            'slug': 'classic-trivia',
            'description': 'Test your general knowledge with classic trivia questions',
            'order': 0,
            'is_math_category': False
        },
        {
            'name': 'Odd One Out',
            'slug': 'odd-one-out',
            'description': 'Find the item that doesn\'t belong',
            'order': 1,
            'is_math_category': False
        },
        {
            'name': 'Fill The Blank',
            'slug': 'fill-the-blank',
            'description': 'Complete the phrase or sentence',
            'order': 2,
            'is_math_category': False
        },
        {
            'name': 'Dynamic Math',
            'slug': 'dynamic-math',
            'description': 'Quick math challenges (questions generated dynamically)',
            'order': 3,
            'is_math_category': True
        },
        {
            'name': 'Knowledge Trap',
            'slug': 'knowledge-trap',
            'description': 'Tricky questions designed to catch you out',
            'order': 4,
            'is_math_category': False
        }
    ]
    
    created_categories = []
    for cat_data in categories:
        category, created = QuizCategory.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        if created:
            print(f"✓ Created category: {category.name}")
        else:
            print(f"- Category already exists: {category.name}")
        created_categories.append(category)
    
    return created_categories


def create_quiz():
    """Create the main quiz instance"""
    quiz, created = Quiz.objects.get_or_create(
        slug='guessticulator',
        defaults={
            'title': 'Guessticulator The Quizculator',
            'description': 'Test your knowledge across 5 categories with 50 questions! '
                          'Answer quickly to score more points. Get 5 correct in a row '
                          'to activate TURBO MODE and double your points!',
            'questions_per_category': 10,
            'time_per_question_seconds': 5,
            'turbo_mode_threshold': 5,
            'turbo_multiplier': 2.0,
            'is_active': True
        }
    )
    
    if created:
        print(f"\n✓ Created quiz: {quiz.title}")
        # Generate QR code
        quiz.generate_qr_code()
        print(f"✓ Generated QR code: {quiz.qr_code_url}")
    else:
        print(f"\n- Quiz already exists: {quiz.title}")
    
    return quiz


def create_sample_questions(categories):
    """Create sample questions for non-math categories"""
    import json
    
    # Classic Trivia questions (Level 1 - General Knowledge)
    classic_trivia = categories[0]
    trivia_questions = [
        {
            'text': 'What is the capital of Canada?',
            'answers': [
                ('Ottawa', True),
                ('Toronto', False),
                ('Vancouver', False),
                ('Montreal', False)
            ]
        },
        {
            'text': 'How many continents are there?',
            'answers': [
                ('7', True),
                ('5', False),
                ('6', False),
                ('8', False)
            ]
        },
        {
            'text': 'What year did World War II end?',
            'answers': [
                ('1945', True),
                ('1944', False),
                ('1946', False),
                ('1943', False)
            ]
        },
        {
            'text': 'What is the largest planet in our solar system?',
            'answers': [
                ('Jupiter', True),
                ('Saturn', False),
                ('Neptune', False),
                ('Earth', False)
            ]
        },
        {
            'text': 'Who painted the Mona Lisa?',
            'answers': [
                ('Leonardo da Vinci', True),
                ('Michelangelo', False),
                ('Raphael', False),
                ('Donatello', False)
            ]
        },
        {
            'text': 'What is the smallest country in the world?',
            'answers': [
                ('Vatican City', True),
                ('Monaco', False),
                ('San Marino', False),
                ('Liechtenstein', False)
            ]
        },
        {
            'text': 'Which ocean is the largest?',
            'answers': [
                ('Pacific Ocean', True),
                ('Atlantic Ocean', False),
                ('Indian Ocean', False),
                ('Arctic Ocean', False)
            ]
        },
        {
            'text': 'What is the speed of light?',
            'answers': [
                ('299,792 km/s', True),
                ('150,000 km/s', False),
                ('400,000 km/s', False),
                ('250,000 km/s', False)
            ]
        },
        {
            'text': 'How many bones are in the human body?',
            'answers': [
                ('206', True),
                ('198', False),
                ('215', False),
                ('220', False)
            ]
        },
        {
            'text': 'What is the currency of Japan?',
            'answers': [
                ('Yen', True),
                ('Won', False),
                ('Yuan', False),
                ('Ringgit', False)
            ]
        }
    ]
    
    create_questions_with_answers(classic_trivia, trivia_questions, "Classic Trivia")
    
    # Odd One Out questions
    odd_one_out = categories[1]
    odd_questions = [
        {
            'text': 'Which one is not a fruit?',
            'answers': [
                ('Carrot', True),
                ('Apple', False),
                ('Banana', False),
                ('Orange', False)
            ]
        },
        {
            'text': 'Which one is not a mammal?',
            'answers': [
                ('Shark', True),
                ('Dolphin', False),
                ('Whale', False),
                ('Bat', False)
            ]
        },
        {
            'text': 'Which one is not a primary color?',
            'answers': [
                ('Green', True),
                ('Red', False),
                ('Blue', False),
                ('Yellow', False)
            ]
        },
        {
            'text': 'Which one is not a programming language?',
            'answers': [
                ('HTML', True),
                ('Python', False),
                ('Java', False),
                ('JavaScript', False)
            ]
        },
        {
            'text': 'Which one is not a planet?',
            'answers': [
                ('Pluto', True),
                ('Mars', False),
                ('Venus', False),
                ('Mercury', False)
            ]
        },
        {
            'text': 'Which one is not a European capital?',
            'answers': [
                ('Toronto', True),
                ('Paris', False),
                ('Rome', False),
                ('Berlin', False)
            ]
        },
        {
            'text': 'Which one is not a type of pasta?',
            'answers': [
                ('Sushi', True),
                ('Spaghetti', False),
                ('Penne', False),
                ('Fusilli', False)
            ]
        },
        {
            'text': 'Which one is not a metal?',
            'answers': [
                ('Wood', True),
                ('Iron', False),
                ('Copper', False),
                ('Gold', False)
            ]
        },
        {
            'text': 'Which one is not a Shakespeare play?',
            'answers': [
                ('The Great Gatsby', True),
                ('Hamlet', False),
                ('Macbeth', False),
                ('Romeo and Juliet', False)
            ]
        },
        {
            'text': 'Which one is not a vowel?',
            'answers': [
                ('Y', True),
                ('A', False),
                ('E', False),
                ('I', False)
            ]
        }
    ]
    
    create_questions_with_answers(odd_one_out, odd_questions, "Odd One Out")
    
    # Fill The Blank questions
    fill_blank = categories[2]
    fill_questions = [
        {
            'text': 'A bird in the hand is worth two in the ___',
            'answers': [
                ('bush', True),
                ('tree', False),
                ('sky', False),
                ('nest', False)
            ]
        },
        {
            'text': 'The early bird catches the ___',
            'answers': [
                ('worm', True),
                ('fish', False),
                ('mouse', False),
                ('seed', False)
            ]
        },
        {
            'text': 'All that glitters is not ___',
            'answers': [
                ('gold', True),
                ('silver', False),
                ('diamond', False),
                ('metal', False)
            ]
        },
        {
            'text': 'Actions speak louder than ___',
            'answers': [
                ('words', True),
                ('sounds', False),
                ('thoughts', False),
                ('feelings', False)
            ]
        },
        {
            'text': 'The pen is mightier than the ___',
            'answers': [
                ('sword', True),
                ('gun', False),
                ('shield', False),
                ('knife', False)
            ]
        },
        {
            'text': 'When in Rome, do as the ___ do',
            'answers': [
                ('Romans', True),
                ('Italians', False),
                ('Europeans', False),
                ('tourists', False)
            ]
        },
        {
            'text': 'You can\'t judge a book by its ___',
            'answers': [
                ('cover', True),
                ('pages', False),
                ('title', False),
                ('author', False)
            ]
        },
        {
            'text': 'The grass is always greener on the other ___',
            'answers': [
                ('side', True),
                ('lawn', False),
                ('field', False),
                ('garden', False)
            ]
        },
        {
            'text': 'Don\'t count your chickens before they ___',
            'answers': [
                ('hatch', True),
                ('grow', False),
                ('lay eggs', False),
                ('die', False)
            ]
        },
        {
            'text': 'A stitch in time saves ___',
            'answers': [
                ('nine', True),
                ('ten', False),
                ('time', False),
                ('money', False)
            ]
        }
    ]
    
    create_questions_with_answers(fill_blank, fill_questions, "Fill The Blank")
    
    # Knowledge Trap questions
    knowledge_trap = categories[4]
    trap_questions = [
        {
            'text': 'How many letters are in "the alphabet"?',
            'answers': [
                ('11', True),
                ('26', False),
                ('12', False),
                ('10', False)
            ]
        },
        {
            'text': 'What month has 28 days?',
            'answers': [
                ('All of them', True),
                ('February', False),
                ('None', False),
                ('January', False)
            ]
        },
        {
            'text': 'If you have 3 apples and take away 2, how many do YOU have?',
            'answers': [
                ('2', True),
                ('1', False),
                ('3', False),
                ('5', False)
            ]
        },
        {
            'text': 'A farmer has 17 sheep, all but 9 die. How many are left?',
            'answers': [
                ('9', True),
                ('8', False),
                ('17', False),
                ('0', False)
            ]
        },
        {
            'text': 'What gets wetter the more it dries?',
            'answers': [
                ('A towel', True),
                ('A sponge', False),
                ('Water', False),
                ('Clothes', False)
            ]
        },
        {
            'text': 'What has hands but cannot clap?',
            'answers': [
                ('A clock', True),
                ('A statue', False),
                ('A doll', False),
                ('A robot', False)
            ]
        },
        {
            'text': 'What can travel around the world while staying in a corner?',
            'answers': [
                ('A stamp', True),
                ('A spider', False),
                ('A GPS', False),
                ('A satellite', False)
            ]
        },
        {
            'text': 'What has a neck but no head?',
            'answers': [
                ('A bottle', True),
                ('A giraffe', False),
                ('A shirt', False),
                ('A guitar', False)
            ]
        },
        {
            'text': 'What is full of holes but still holds water?',
            'answers': [
                ('A sponge', True),
                ('A bucket', False),
                ('A net', False),
                ('A strainer', False)
            ]
        },
        {
            'text': 'What goes up but never comes down?',
            'answers': [
                ('Your age', True),
                ('A balloon', False),
                ('A plane', False),
                ('Temperature', False)
            ]
        }
    ]
    
    create_questions_with_answers(knowledge_trap, trap_questions, "Knowledge Trap")


def create_questions_with_answers(category, questions_data, category_name):
    """Helper to create questions with their answers"""
    for q_data in questions_data:
        question, created = QuizQuestion.objects.get_or_create(
            category=category,
            text=q_data['text'],
            defaults={'is_active': True}
        )
        
        if created:
            # Create answers
            for order, (answer_text, is_correct) in enumerate(q_data['answers']):
                QuizAnswer.objects.create(
                    question=question,
                    text=answer_text,
                    is_correct=is_correct,
                    order=order
                )
            print(f"  ✓ Created question: {q_data['text'][:50]}...")


def create_tournament(quiz):
    """Create a sample tournament"""
    now = timezone.now()
    start_date = now
    end_date = start_date + timedelta(hours=24)
    
    tournament, created = QuizTournament.objects.get_or_create(
        slug='weekend-challenge',
        defaults={
            'name': 'Weekend Challenge',
            'description': 'Compete with other players for 24 hours! '
                          'Top scores win bragging rights.',
            'quiz': quiz,
            'start_date': start_date,
            'end_date': end_date,
            'status': QuizTournament.TournamentStatus.ACTIVE
        }
    )
    
    if created:
        print(f"\n✓ Created tournament: {tournament.name}")
        # Generate QR code
        tournament.generate_qr_code()
        print(f"✓ Generated tournament QR code: {tournament.qr_code_url}")
    else:
        print(f"\n- Tournament already exists: {tournament.name}")
    
    return tournament


def main():
    print("=" * 60)
    print("GUESSTICULATOR QUIZ GAME SETUP")
    print("=" * 60)
    
    # Step 1: Create categories
    print("\n[1/4] Creating quiz categories...")
    categories = create_categories()
    
    # Step 2: Create main quiz
    print("\n[2/4] Creating main quiz...")
    quiz = create_quiz()
    
    # Step 3: Create sample questions
    print("\n[3/4] Creating sample questions...")
    create_sample_questions(categories)
    
    # Step 4: Create tournament
    print("\n[4/4] Creating tournament...")
    tournament = create_tournament(quiz)
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print(f"\n📊 Quiz: {quiz.title}")
    print(f"   Slug: {quiz.slug}")
    print(f"   QR Code: {quiz.qr_code_url}")
    print(f"\n📁 Categories: {QuizCategory.objects.count()}")
    for cat in categories:
        q_count = cat.questions.count()
        cat_type = "🧮 Math (Dynamic)" if cat.is_math_category else f"📝 {q_count} questions"
        print(f"   {cat.order + 1}. {cat.name} - {cat_type}")
    
    print(f"\n❓ Total Questions: {QuizQuestion.objects.count()}")
    print(f"✅ Total Answers: {QuizAnswer.objects.count()}")
    
    print(f"\n🏆 Tournament: {tournament.name}")
    print(f"   Status: {tournament.status}")
    print(f"   Start: {tournament.start_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   End: {tournament.end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   QR Code: {tournament.qr_code_url}")
    
    print("\n" + "=" * 60)
    print("🎮 Game URL: https://hotelsmates.com/games/quiz")
    print("=" * 60)
    print("\n✨ Ready to play!\n")


if __name__ == '__main__':
    main()
