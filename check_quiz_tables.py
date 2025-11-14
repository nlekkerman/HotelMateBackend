import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename LIKE 'entertainment_quiz%' 
    ORDER BY tablename;
""")

tables = cursor.fetchall()
print("\nExisting quiz tables:")
for table in tables:
    print(f"  - {table[0]}")
print(f"\nTotal: {len(tables)} tables")
