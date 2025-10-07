from rest_framework import viewsets, permissions, mixins
from rest_framework.response import Response
from .models import Game, GameHighScore, GameQRCode
from .serializers import (
    GameSerializer,
    GameHighScoreSerializer,
    GameHighScoreCreateSerializer,
    GameQRCodeSerializer
)


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """List all games or retrieve a single game."""
    queryset = Game.objects.filter(active=True)
    serializer_class = GameSerializer
    permission_classes = [permissions.AllowAny]


class GameHighScoreViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin):
    """List highscores or submit a new highscore, limited to top 100."""
    queryset = GameHighScore.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # Disable DRF pagination

    def get_serializer_class(self):
        if self.action == 'create':
            return GameHighScoreCreateSerializer
        return GameHighScoreSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        game_slug = self.request.query_params.get('game')
        hotel_slug = self.request.query_params.get('hotel')

        if game_slug:
            qs = qs.filter(game__slug=game_slug.strip())
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug.strip())

        # Order by score descending and limit to top 100
        return qs.order_by('-score')[:100]

    def create(self, request, *args, **kwargs):
        game_slug = request.data.get('game', '').strip()
        if not game_slug:
            return Response({'detail': 'Game slug is required.'}, status=400)

        # Create the game if it doesn't exist
        game, _ = Game.objects.get_or_create(
            slug=game_slug,
            defaults={'title': game_slug, 'active': True}
        )

        # Replace 'game' field with the actual Game instance ID
        data = request.data.copy()
        data['game'] = game.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

class GameQRCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """List QR codes (optionally filtered by hotel)."""
    queryset = GameQRCode.objects.all()
    serializer_class = GameQRCodeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_slug = self.request.query_params.get('hotel')
        if hotel_slug:
            hotel_slug = hotel_slug.strip()
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs
