"""
Create Real Tournament and Generate QR Code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.utils import timezone
from entertainment.models import Quiz, QuizTournament
from datetime import timedelta


def create_real_tournament():
    """Create a real tournament with QR code"""
    print("\n=== Creating Real Tournament ===")
    
    # List available quizzes
    quizzes = Quiz.objects.filter(is_active=True)
    print(f"\nAvailable Quizzes ({quizzes.count()}):")
    for idx, quiz in enumerate(quizzes, 1):
        q_count = quiz.questions.filter(is_active=True).count()
        print(f"  {idx}. {quiz.title} ({q_count} questions, Level {quiz.difficulty_level})")
    
    if not quizzes.exists():
        print("\n❌ No quizzes available. Please create a quiz first.")
        return None
    
    # Use first quiz or create test quiz
    quiz_slug = input("\nEnter quiz slug (or press Enter for first quiz): ").strip()
    
    if quiz_slug:
        try:
            quiz = Quiz.objects.get(slug=quiz_slug)
        except Quiz.DoesNotExist:
            print(f"❌ Quiz '{quiz_slug}' not found")
            return None
    else:
        quiz = quizzes.first()
    
    print(f"\n✅ Using quiz: {quiz.title}")
    
    # Tournament details
    tournament_name = input("Tournament name: ").strip() or "Winter Championship 2025"
    tournament_slug = input("Tournament slug: ").strip() or "winter-championship-2025"
    
    # Create tournament
    now = timezone.now()
    tournament, created = QuizTournament.objects.get_or_create(
        slug=tournament_slug,
        defaults={
            'name': tournament_name,
            'quiz': quiz,
            'start_date': now,
            'end_date': now + timedelta(days=30),
            'status': QuizTournament.TournamentStatus.ACTIVE,
            'first_prize': '$500 + Trophy',
            'second_prize': '$300',
            'third_prize': '$150',
            'rules': 'Play through all 5 levels (10 questions each). Best score wins! You can play multiple times, only your best result counts.',
            'description': 'Test your knowledge across 5 difficulty levels!'
        }
    )
    
    if created:
        print(f"\n✅ Tournament created: {tournament.name}")
    else:
        print(f"\n⚠️  Tournament already exists: {tournament.name}")
    
    print(f"   Status: {tournament.status}")
    print(f"   Quiz: {tournament.quiz.title}")
    print(f"   Period: {tournament.start_date.date()} to {tournament.end_date.date()}")
    print(f"   Prizes: 1st={tournament.first_prize}, 2nd={tournament.second_prize}, 3rd={tournament.third_prize}")
    
    return tournament


def generate_tournament_qr(tournament):
    """Generate QR code for tournament"""
    print(f"\n=== Generating QR Code for {tournament.name} ===")
    
    try:
        success = tournament.generate_qr_code()
        
        if success:
            print("✅ QR Code generated successfully!")
            print(f"\n   QR Code URL: {tournament.qr_code_url}")
            print(f"   Tournament URL: https://hotelsmates.com/games/quiz/tournament/{tournament.slug}")
            print(f"   Generated at: {tournament.qr_generated_at}")
            print("\n   You can now:")
            print("   1. Download and print the QR code")
            print("   2. Share the tournament URL")
            print("   3. Display QR code on screens/posters")
            return True
        else:
            print("❌ Failed to generate QR code")
            return False
            
    except Exception as e:
        print(f"❌ Error generating QR code: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def show_tournament_info(tournament):
    """Display tournament information"""
    print("\n" + "=" * 70)
    print(f"TOURNAMENT: {tournament.name}")
    print("=" * 70)
    print(f"Slug: {tournament.slug}")
    print(f"Quiz: {tournament.quiz.title}")
    print(f"Status: {tournament.status}")
    print(f"Period: {tournament.start_date.strftime('%Y-%m-%d %H:%M')} to {tournament.end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"\nPrizes:")
    print(f"  🥇 1st Place: {tournament.first_prize}")
    print(f"  🥈 2nd Place: {tournament.second_prize}")
    print(f"  🥉 3rd Place: {tournament.third_prize}")
    print(f"\nRules:")
    print(f"  {tournament.rules}")
    print(f"\nParticipants: {tournament.participant_count}")
    
    if tournament.qr_code_url:
        print(f"\n✅ QR Code: {tournament.qr_code_url}")
    else:
        print("\n⚠️  No QR code generated yet")
    
    print("=" * 70)


def main():
    print("=" * 70)
    print("CREATE REAL TOURNAMENT & GENERATE QR CODE")
    print("=" * 70)
    
    # Create tournament
    tournament = create_real_tournament()
    
    if not tournament:
        print("\n❌ Tournament creation failed")
        return
    
    # Generate QR code
    if not tournament.qr_code_url:
        generate = input("\nGenerate QR code now? (y/n): ").strip().lower()
        if generate == 'y':
            generate_tournament_qr(tournament)
    else:
        print(f"\n✅ QR code already exists: {tournament.qr_code_url}")
        regenerate = input("Regenerate QR code? (y/n): ").strip().lower()
        if regenerate == 'y':
            generate_tournament_qr(tournament)
    
    # Show final info
    tournament.refresh_from_db()
    show_tournament_info(tournament)
    
    print("\n✅ Tournament is ready!")
    print(f"\nAPI Endpoints:")
    print(f"  Tournament Details: GET /api/entertainment/quiz-tournaments/{tournament.slug}/")
    print(f"  Leaderboard: GET /api/entertainment/quiz-tournaments/{tournament.slug}/leaderboard/")
    print(f"  Generate QR: POST /api/entertainment/quiz-tournaments/{tournament.slug}/generate_qr_code/")


if __name__ == '__main__':
    main()
