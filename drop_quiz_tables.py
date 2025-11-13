"""
Drop old quiz tables and recreate with new schema
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.db import connection

def drop_old_quiz_tables():
    """Drop old quiz tables to allow fresh migration"""
    
    tables_to_drop = [
        'entertainment_tournamentleaderboard',
        'entertainment_quiztournament',
        'entertainment_quizleaderboard',
        'entertainment_quizsubmission',
        'entertainment_quizsession',
        'entertainment_quizanswer',
        'entertainment_quizquestion',
        'entertainment_quizcategory',
        'entertainment_quiz',
    ]
    
    with connection.cursor() as cursor:
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                print(f"✓ Dropped table: {table}")
            except Exception as e:
                print(f"⚠ Could not drop {table}: {e}")
    
    print("\n✓ All old quiz tables dropped successfully!")
    print("\nNow run:")
    print("  1. python manage.py migrate entertainment")
    print("  2. python setup_quiz_game.py")
    print("  3. python load_quiz_questions.py")


if __name__ == '__main__':
    print("=" * 60)
    print("DROPPING OLD QUIZ TABLES")
    print("=" * 60)
    print("\n⚠ WARNING: This will delete all existing quiz data!")
    response = input("Continue? (yes/no): ")
    
    if response.lower() == 'yes':
        drop_old_quiz_tables()
    else:
        print("Cancelled.")
