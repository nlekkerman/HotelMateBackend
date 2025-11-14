from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GameViewSet, GameHighScoreViewSet, GameQRCodeViewSet,
    MemoryGameCardViewSet, MemoryGameSessionViewSet,
    MemoryGameTournamentViewSet,
    MemoryGameAchievementViewSet, DashboardViewSet,
    # Quiz Game Views
    QuizViewSet, QuizCategoryViewSet, QuizGameViewSet,
    QuizLeaderboardViewSet, QuizTournamentViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'games', GameViewSet, basename='games')
router.register(r'memory-cards', MemoryGameCardViewSet, basename='memory-cards')
router.register(r'memory-sessions', MemoryGameSessionViewSet, basename='memory-sessions')
router.register(r'tournaments', MemoryGameTournamentViewSet, basename='tournaments')
router.register(r'achievements', MemoryGameAchievementViewSet, basename='achievements')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# Quiz Game ViewSets - register BEFORE creating urlpatterns
router.register(r'quizzes', QuizViewSet, basename='quizzes')
router.register(r'quiz-categories', QuizCategoryViewSet, basename='quiz-categories')
router.register(r'quiz-tournaments', QuizTournamentViewSet, basename='quiz-tournaments')

# Legacy URL patterns for backward compatibility
game_list = GameViewSet.as_view({'get': 'list'})
highscore_list_create = GameHighScoreViewSet.as_view({'get': 'list', 'post': 'create'})
qrcode_list = GameQRCodeViewSet.as_view({'get': 'list'})

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Legacy endpoints (keep for backward compatibility)
    path("games/", game_list, name="games_list"),
    path("games/highscores/", highscore_list_create, name="games_highscores"),
    path("games/qrcodes/", qrcode_list, name="games_qrcodes"),
    
    # Memory Game specific endpoints
    path('memory-sessions/practice/',
         MemoryGameSessionViewSet.as_view({'post': 'practice'}),
         name='memory-practice'),
    path('memory-sessions/my-stats/',
         MemoryGameSessionViewSet.as_view({'get': 'my_stats'}),
         name='memory-my-stats'),
    path('memory-sessions/leaderboard/',
         MemoryGameSessionViewSet.as_view({'get': 'leaderboard'}),
         name='memory-leaderboard'),
    
    # Tournament specific endpoints
    path('tournaments/active/',
         MemoryGameTournamentViewSet.as_view({'get': 'active_for_hotel'}),
         name='tournaments-active-for-hotel'),
    path('tournaments/summary/',
         MemoryGameTournamentViewSet.as_view({'get': 'summary'}),
         name='tournaments-summary'),
    path('tournaments/<int:pk>/submit_score/',
         MemoryGameTournamentViewSet.as_view({'post': 'submit_score'}),
         name='tournament-submit-score'),
    path('tournaments/<int:pk>/generate_qr_code/',
         MemoryGameTournamentViewSet.as_view({'post': 'generate_qr_code'}),
         name='tournament-generate-qr-code'),
    path('tournaments/<int:pk>/leaderboard/',
         MemoryGameTournamentViewSet.as_view({'get': 'leaderboard'}),
         name='tournament-leaderboard'),
    path('tournaments/<int:pk>/participants/',
         MemoryGameTournamentViewSet.as_view({'get': 'participants'}),
         name='tournament-participants'),
    path('tournaments/<int:pk>/start/',
         MemoryGameTournamentViewSet.as_view({'post': 'start'}),
         name='tournament-start'),
    path('tournaments/<int:pk>/end/',
         MemoryGameTournamentViewSet.as_view({'post': 'end'}),
         name='tournament-end'),
    
    # Achievement endpoints
    path('achievements/my-achievements/',
         MemoryGameAchievementViewSet.as_view({'get': 'my_achievements'}),
         name='my-achievements'),

    # Dashboard endpoints
    path('dashboard/stats/',
         DashboardViewSet.as_view({'get': 'stats'}),
         name='dashboard-stats'),
]

# ============================================================================
# GUESSTICULATOR QUIZ GAME URLS
# ============================================================================

# Quiz game action URLs
quiz_game_urls = [
    path('quiz/game/start_session/',
         QuizGameViewSet.as_view({'post': 'start_session'}),
         name='quiz-game-start-session'),
    path('quiz/game/submit_answer/',
         QuizGameViewSet.as_view({'post': 'submit_answer'}),
         name='quiz-game-submit-answer'),
    path('quiz/game/complete_session/',
         QuizGameViewSet.as_view({'post': 'complete_session'}),
         name='quiz-game-complete-session'),
    path('quiz/game/get_session/',
         QuizGameViewSet.as_view({'get': 'get_session'}),
         name='quiz-game-get-session'),
]

# Quiz leaderboard URLs
quiz_leaderboard_urls = [
    path('quiz/leaderboard/all-time/',
         QuizLeaderboardViewSet.as_view({'get': 'all_time'}),
         name='quiz-leaderboard-all-time'),
    path('quiz/leaderboard/player-stats/',
         QuizLeaderboardViewSet.as_view({'get': 'player_stats'}),
         name='quiz-leaderboard-player-stats'),
]

# Add quiz URLs to main urlpatterns
urlpatterns += quiz_game_urls + quiz_leaderboard_urls
