"""
Simple script to drop and recreate quiz tables
Run in terminal with the venv activated
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

from django.db import connection

print("=" * 60)
print("FIXING QUIZ TABLES")
print("=" * 60)

with connection.cursor() as cursor:
    # Drop tables in reverse dependency order
    tables = [
        'entertainment_tournamentleaderboard',
        'entertainment_quizsubmission',
        'entertainment_quizleaderboard',
        'entertainment_quizsession',
        'entertainment_quiztournament',
        'entertainment_quizanswer',
        'entertainment_quizquestion',
        'entertainment_quiz',
        'entertainment_quizcategory',
    ]
    
    print("\nDropping old tables...")
    for table in tables:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
            print(f"  ✓ Dropped: {table}")
        except Exception as e:
            print(f"  - Skip: {table} ({e})")

print("\nNow creating tables with correct schema...")
from django.core.management import call_command

# Unapply migration 0008
try:
    print("\n  Rolling back migration 0008...")
    call_command('migrate', 'entertainment', '0007', '--fake')
    print("  ✓ Rolled back")
except Exception as e:
    print(f"  - Could not rollback: {e}")

# Reapply migration 0008
try:
    print("\n  Applying migration 0008...")
    call_command('migrate', 'entertainment')
    print("  ✓ Migration applied")
except Exception as e:
    print(f"  ✗ Migration failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ TABLES RECREATED SUCCESSFULLY!")
print("=" * 60)
print("\nNow run:")
print("  1. python setup_quiz_game.py")
print("  2. python load_quiz_questions.py")
print()
