from django.db import connection

tables = [
    "entertainment_quizanswer",
    "entertainment_quizleaderboard",
    "entertainment_quizsession",
    "entertainment_quizquestion",
    "entertainment_quizcategory",
    "entertainment_quiztournament",
]

with connection.cursor() as cursor:
    for table in tables:
        cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
        print(f"Dropped {table}")

print("\nAll quiz tables dropped successfully!")
