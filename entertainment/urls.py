from django.urls import path
from .views import GameViewSet, GameHighScoreViewSet, GameQRCodeViewSet

game_list = GameViewSet.as_view({'get': 'list'})
highscore_list_create = GameHighScoreViewSet.as_view({'get': 'list', 'post': 'create'})
qrcode_list = GameQRCodeViewSet.as_view({'get': 'list'})

urlpatterns = [
    # List all games
    path("games/", game_list, name="games_list"),

    # List highscores or submit a new one
    path("games/highscores/", highscore_list_create, name="games_highscores"),

    # List QR codes
    path("games/qrcodes/", qrcode_list, name="games_qrcodes"),
]
