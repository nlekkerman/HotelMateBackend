"""
Create Tournament for Guessticulator Quiz
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import Quiz, QuizTournament
from datetime import timedelta


def create_tournament():
    """Create tournament for Guessticulator quiz"""
    print("=" * 70)
    print("CREATE TOURNAMENT FOR GUESSTICULATOR")
    print("=" * 70)
    
    # Get Guessticulator quiz
    try:
        quiz = Quiz.objects.get(slug='guessticulator-the-quizculator')
        print(f"\n✅ Found quiz: {quiz.title}")
        print(f"   Questions: {quiz.questions.count()}")
    except Quiz.DoesNotExist:
        print("\n❌ Guessticulator quiz not found!")
        print("Available quizzes:")
        for q in Quiz.objects.all():
            print(f"  - {q.slug}")
        return None
    
    # Create tournament
    now = timezone.now()
    tournament, created = QuizTournament.objects.get_or_create(
        slug='guessticulator-tournament-24h',
        defaults={
            'name': 'Guessticulator 24-Hour Challenge',
            'quiz': quiz,
            'start_date': now,
            'end_date': now + timedelta(hours=24),
            'status': QuizTournament.TournamentStatus.ACTIVE,
            'first_prize': '$500 + Trophy',
            'second_prize': '$300',
            'third_prize': '$150',
            'description': '24-hour tournament! Play 50 questions across 5 categories. Best score wins!',
            'rules': 'Complete all 50 questions (10 per category). You can play multiple times - only your best score counts. Tournament ends in 24 hours!'
        }
    )
    
    if created:
        print(f"\n✅ Tournament created: {tournament.name}")
    else:
        print(f"\n⚠️  Tournament exists: {tournament.name}")
        print("   Updating dates...")
        tournament.start_date = now
        tournament.end_date = now + timedelta(hours=24)
        tournament.status = QuizTournament.TournamentStatus.ACTIVE
        tournament.save()
        print("   ✅ Updated to active with new 24h period")
    
    print(f"\nTournament Details:")
    print(f"  Name: {tournament.name}")
    print(f"  Quiz: {tournament.quiz.title}")
    print(f"  Status: {tournament.status}")
    print(f"  Start: {tournament.start_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"  End: {tournament.end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Duration: 24 hours")
    print(f"\nPrizes:")
    print(f"  🥇 1st: {tournament.first_prize}")
    print(f"  🥈 2nd: {tournament.second_prize}")
    print(f"  🥉 3rd: {tournament.third_prize}")
    
    return tournament


def generate_qr(tournament):
    """Generate QR code for tournament"""
    print("\n" + "=" * 70)
    print("GENERATING QR CODE")
    print("=" * 70)
    
    try:
        success = tournament.generate_qr_code()
        
        if success:
            print("\n✅ QR Code generated!")
            print(f"   QR URL: {tournament.qr_code_url}")
            print(f"   Tournament URL: https://hotelsmates.com/games/quiz")
            print(f"   Generated: {tournament.qr_generated_at}")
            return True
        else:
            print("\n❌ QR generation failed")
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_api_endpoints(tournament):
    """Show API endpoints"""
    print("\n" + "=" * 70)
    print("API ENDPOINTS")
    print("=" * 70)
    print(f"\nTournament:")
    print(f"  GET /api/entertainment/quiz-tournaments/{tournament.slug}/")
    print(f"  GET /api/entertainment/quiz-tournaments/{tournament.slug}/leaderboard/")
    print(f"\nStart Game Session:")
    print(f"  POST /api/entertainment/quiz-sessions/")
    print(f"  Body: {{'quiz_slug': '{tournament.quiz.slug}', 'player_name': 'YourName', 'is_tournament': true}}")
    print(f"\nLeaderboards:")
    print(f"  All-time: GET /api/entertainment/quiz-sessions/all_time_leaderboard/?quiz={tournament.quiz.slug}")
    print(f"  Tournament: GET /api/entertainment/quiz-sessions/tournament_leaderboard/?quiz={tournament.quiz.slug}")


def main():
    # Create tournament
    tournament = create_tournament()
    
    if not tournament:
        return
    
    # Generate QR
    if not tournament.qr_code_url:
        gen = input("\nGenerate QR code? (y/n): ").strip().lower()
        if gen == 'y':
            generate_qr(tournament)
    else:
        print(f"\n✅ QR exists: {tournament.qr_code_url}")
        regen = input("Regenerate? (y/n): ").strip().lower()
        if regen == 'y':
            generate_qr(tournament)
    
    # Show endpoints
    show_api_endpoints(tournament)
    
    print("\n" + "=" * 70)
    print("🎉 TOURNAMENT IS READY!")
    print("=" * 70)


if __name__ == '__main__':
    main()
