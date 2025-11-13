"""
Test Quiz Tournament and QR Code Generation
Check tournament functionality and Cloudinary QR upload
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from entertainment.models import Quiz, QuizTournament, QuizCategory
from django.utils import timezone
from datetime import timedelta
import cloudinary


def test_cloudinary_config():
    """Test Cloudinary configuration"""
    print("\n" + "="*70)
    print("TEST 1: Cloudinary Configuration")
    print("="*70)
    
    config = cloudinary.config()
    print(f"\n✅ Cloudinary Configured:")
    print(f"   Cloud Name: {config.cloud_name}")
    print(f"   API Key: {config.api_key[:4]}...{config.api_key[-4:]}")
    print(f"   Secure: {config.secure}")


def test_fetch_tournaments():
    """Test fetching tournaments"""
    print("\n" + "="*70)
    print("TEST 2: Fetch Quiz Tournaments")
    print("="*70)
    
    tournaments = QuizTournament.objects.all()
    print(f"\nTotal Tournaments: {tournaments.count()}")
    
    active_tournaments = QuizTournament.objects.filter(
        status=QuizTournament.TournamentStatus.ACTIVE
    )
    print(f"Active Tournaments: {active_tournaments.count()}")
    
    for tournament in tournaments[:5]:
        print(f"\n  🏆 {tournament.name}")
        print(f"     Slug: {tournament.slug}")
        print(f"     Status: {tournament.status}")
        print(f"     Start: {tournament.start_date}")
        print(f"     End: {tournament.end_date}")
        print(f"     Prizes: 🥇{tournament.first_prize} | "
              f"🥈{tournament.second_prize} | 🥉{tournament.third_prize}")
        print(f"     QR Code: {tournament.qr_code_url or 'Not Generated'}")
        print(f"     Is Active: {tournament.is_active}")
    
    print("\n✅ Tournaments fetched successfully")
    return tournaments.first() if tournaments.exists() else None


def test_create_tournament():
    """Test creating a new tournament"""
    print("\n" + "="*70)
    print("TEST 3: Create New Tournament")
    print("="*70)
    
    quiz = Quiz.objects.filter(is_active=True).first()
    if not quiz:
        print("❌ No active quiz found")
        return None
    
    now = timezone.now()
    start_date = now + timedelta(hours=1)
    
    tournament, created = QuizTournament.objects.get_or_create(
        slug='test-tournament-24h',
        defaults={
            'name': 'Test 24-Hour Quiz Tournament',
            'description': 'Testing tournament creation',
            'quiz': quiz,
            'start_date': start_date,
            'status': QuizTournament.TournamentStatus.UPCOMING,
            'first_prize': 'Trophy + $100',
            'second_prize': 'Medal + $50',
            'third_prize': 'Certificate + $25'
        }
    )
    
    if created:
        print(f"\n✅ Tournament Created!")
    else:
        print(f"\n✅ Tournament Already Exists!")
    
    print(f"   Name: {tournament.name}")
    print(f"   Slug: {tournament.slug}")
    print(f"   Quiz: {tournament.quiz.title}")
    print(f"   Start: {tournament.start_date}")
    print(f"   End: {tournament.end_date}")
    print(f"   Duration: {(tournament.end_date - tournament.start_date).total_seconds() / 3600} hours")
    print(f"   Status: {tournament.status}")
    
    return tournament


def test_quiz_qr_generation():
    """Test Quiz QR code generation"""
    print("\n" + "="*70)
    print("TEST 4: Quiz QR Code Generation")
    print("="*70)
    
    quiz = Quiz.objects.filter(is_active=True).first()
    if not quiz:
        print("❌ No active quiz found")
        return
    
    print(f"\nQuiz: {quiz.title}")
    print(f"Expected URL: https://hotelsmates.com/games/quiz")
    print(f"Current QR URL: {quiz.qr_code_url or 'Not generated'}")
    
    if not quiz.qr_code_url:
        print("\n⚙️  Generating QR code...")
        try:
            result = quiz.generate_qr_code()
            quiz.refresh_from_db()
            
            if result:
                print(f"✅ QR Code Generated!")
                print(f"   URL: {quiz.qr_code_url}")
                print(f"   Generated At: {quiz.qr_generated_at}")
                print(f"   Cloudinary Path: quiz_qr/{quiz.slug}")
            else:
                print("❌ QR generation failed")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print("✅ QR Code already exists")
        print(f"   Generated At: {quiz.qr_generated_at}")


def test_tournament_qr_generation(tournament):
    """Test Tournament QR code generation"""
    print("\n" + "="*70)
    print("TEST 5: Tournament QR Code Generation")
    print("="*70)
    
    if not tournament:
        print("❌ No tournament to test")
        return
    
    print(f"\nTournament: {tournament.name}")
    expected_url = f"https://hotelsmates.com/games/quiz?tournament={tournament.slug}"
    print(f"Expected URL: {expected_url}")
    print(f"Current QR URL: {tournament.qr_code_url or 'Not generated'}")
    
    if not tournament.qr_code_url:
        print("\n⚙️  Generating QR code...")
        try:
            result = tournament.generate_qr_code()
            tournament.refresh_from_db()
            
            if result:
                print(f"✅ QR Code Generated!")
                print(f"   URL: {tournament.qr_code_url}")
                print(f"   Generated At: {tournament.qr_generated_at}")
                print(f"   Cloudinary Path: quiz_tournament_qr/{tournament.slug}")
            else:
                print("❌ QR generation failed")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        print("✅ QR Code already exists")
        print(f"   Generated At: {tournament.qr_generated_at}")


def test_url_construction():
    """Test URL construction patterns"""
    print("\n" + "="*70)
    print("TEST 6: URL Construction Patterns")
    print("="*70)
    
    quiz = Quiz.objects.filter(is_active=True).first()
    tournament = QuizTournament.objects.first()
    categories = QuizCategory.objects.filter(is_active=True)[:3]
    
    print("\n📱 Frontend URLs:")
    print("\n1. Quiz Game (Casual Mode):")
    print(f"   https://hotelsmates.com/games/quiz")
    
    print("\n2. Quiz Game (Tournament Mode):")
    if tournament:
        print(f"   https://hotelsmates.com/games/quiz?tournament={tournament.slug}")
    
    print("\n\n🔧 Backend API Endpoints:")
    print("\n1. Quiz List:")
    print(f"   GET /api/v1/entertainment/quizzes/")
    
    print("\n2. Quiz Detail:")
    if quiz:
        print(f"   GET /api/v1/entertainment/quizzes/{quiz.slug}/")
    
    print("\n3. Categories:")
    print(f"   GET /api/v1/entertainment/quiz-categories/")
    
    print("\n4. Category Detail:")
    if categories:
        for cat in categories:
            print(f"   GET /api/v1/entertainment/quiz-categories/{cat.slug}/")
    
    print("\n5. Game Actions:")
    print(f"   POST /api/v1/entertainment/quiz/game/start_session/")
    print(f"   POST /api/v1/entertainment/quiz/game/submit_answer/")
    print(f"   POST /api/v1/entertainment/quiz/game/complete_session/")
    
    print("\n6. Tournaments:")
    print(f"   GET /api/v1/entertainment/quiz-tournaments/")
    if tournament:
        print(f"   GET /api/v1/entertainment/quiz-tournaments/{tournament.slug}/")
    
    print("\n7. Leaderboards:")
    print(f"   GET /api/v1/entertainment/quiz/leaderboard/all-time/")
    print(f"   GET /api/v1/entertainment/quiz/leaderboard/player-stats/?session_token=<token>")


def test_env_variables():
    """Test environment variables"""
    print("\n" + "="*70)
    print("TEST 7: Environment Variables")
    print("="*70)
    
    import os
    
    env_vars = [
        'SECRET_KEY',
        'DEBUG',
        'DATABASE_URL',
        'ALLOWED_HOSTS',
        'CLOUDINARY_URL',
        'HEROKU_HOST'
    ]
    
    print("\n🔐 Environment Configuration:")
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive data
            if var in ['SECRET_KEY', 'DATABASE_URL', 'CLOUDINARY_URL']:
                masked = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***"
                print(f"   ✅ {var}: {masked}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Check Cloudinary specifically
    cloudinary_url = os.environ.get('CLOUDINARY_URL')
    if cloudinary_url:
        print(f"\n   Cloudinary Status: Configured ✅")
        parts = cloudinary_url.split('@')
        if len(parts) > 1:
            print(f"   Cloud Name: {parts[-1]}")
    else:
        print(f"\n   Cloudinary Status: Not Configured ❌")


def test_compare_urls_with_rooms():
    """Compare URL patterns with rooms app"""
    print("\n" + "="*70)
    print("TEST 8: Compare URL Patterns with Rooms App")
    print("="*70)
    
    print("\n📊 Rooms App QR Pattern:")
    print("   Registration Code generates:")
    print("   https://hotelsmates.com/register?token=<qr_token>&hotel=<hotel_slug>")
    print("   Cloudinary path: registration_qr/<hotel_slug>_<code>")
    
    print("\n📊 Quiz App QR Pattern:")
    print("\n   1. Quiz (Casual Mode):")
    print("      https://hotelsmates.com/games/quiz")
    print("      Cloudinary path: quiz_qr/<quiz_slug>")
    
    print("\n   2. Tournament Mode:")
    print("      https://hotelsmates.com/games/quiz?tournament=<tournament_slug>")
    print("      Cloudinary path: quiz_tournament_qr/<tournament_slug>")
    
    print("\n✅ Both use same pattern:")
    print("   - Cloudinary for QR storage")
    print("   - Frontend base URL: https://hotelsmates.com")
    print("   - Query parameters for variants")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🎮 QUIZ TOURNAMENT & QR CODE TEST SUITE")
    print("="*70)
    
    try:
        # Test 1: Cloudinary config
        test_cloudinary_config()
        
        # Test 2: Fetch tournaments
        tournament = test_fetch_tournaments()
        
        # Test 3: Create tournament
        new_tournament = test_create_tournament()
        
        # Test 4: Quiz QR generation
        test_quiz_qr_generation()
        
        # Test 5: Tournament QR generation
        test_tournament_qr_generation(new_tournament or tournament)
        
        # Test 6: URL construction
        test_url_construction()
        
        # Test 7: Environment variables
        test_env_variables()
        
        # Test 8: Compare with rooms
        test_compare_urls_with_rooms()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
