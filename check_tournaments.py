"""
Quick check for existing tournaments
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizTournament

print("\n" + "="*70)
print("CHECKING TOURNAMENTS")
print("="*70)

# Check quizzes
quizzes = Quiz.objects.all()
print(f"\n📝 Quizzes: {quizzes.count()}")
for quiz in quizzes:
    print(f"   - {quiz.title} ({quiz.slug}) - Active: {quiz.is_active}")

# Check tournaments
tournaments = QuizTournament.objects.all()
print(f"\n🏆 Tournaments: {tournaments.count()}")

if tournaments.exists():
    for t in tournaments:
        print(f"\n   Tournament: {t.name}")
        print(f"   Slug: {t.slug}")
        print(f"   Status: {t.status}")
        print(f"   Start: {t.start_date}")
        print(f"   End: {t.end_date}")
        print(f"   QR Code: {'✅ Generated' if t.qr_code_url else '❌ Not Generated'}")
        if t.qr_code_url:
            print(f"   QR URL: {t.qr_code_url}")
else:
    print("\n   ❌ No tournaments found")
    print("\n   Would you like to create one? (This script just checks)")
