"""Utility script to drop and recreate quiz tables.

Usage:
    python manage.py runscript reset_quiz_tables

Alternatively, copy the logic into a custom management command.
"""
from django.core.management import call_command
from django.db import connection

QUIZ_TABLES = [
    "entertainment_quizanswer",
    "entertainment_quizleaderboard",
    "entertainment_quizsession",
    "entertainment_quizquestion",
    "entertainment_quizcategory",
    "entertainment_quiztournament",
]


def run():
    """Drop quiz tables and reapply migrations."""
    with connection.cursor() as cursor:
        for table in QUIZ_TABLES:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')

    call_command("migrate", "entertainment", "0008")
