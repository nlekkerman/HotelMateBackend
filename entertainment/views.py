from rest_framework import viewsets, permissions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import (
    Game, GameHighScore, GameQRCode,
    MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament,
    TournamentParticipation, MemoryGameAchievement, UserAchievement
)
from .serializers import (
    GameSerializer,
    GameHighScoreSerializer,
    GameHighScoreCreateSerializer,
    GameQRCodeSerializer,
    MemoryGameCardSerializer,
    MemoryGameSessionSerializer,
    MemoryGameSessionCreateSerializer,
    MemoryGameStatsSerializer,
    MemoryGameTournamentSerializer,
    TournamentParticipationSerializer,
    TournamentLeaderboardSerializer,
    MemoryGameAchievementSerializer,
    UserAchievementSerializer,
    LeaderboardSerializer,
    DashboardStatsSerializer
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


class MemoryGameCardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Memory Game Cards - provides card images for games
    """
    serializer_class = MemoryGameCardSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get active cards, optionally filtered by difficulty"""
        qs = MemoryGameCard.objects.filter(is_active=True)
        
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            qs = qs.filter(difficulty_levels__icontains=difficulty)
            
        return qs.order_by('name')
    
    @action(detail=False, methods=['get'], url_path='for-game')
    def cards_for_game(self, request):
        """
        Get random cards for a memory game session
        Query params:
        - difficulty: easy/intermediate/hard
        - pairs: number of pairs needed (default based on difficulty)
        """
        difficulty = request.query_params.get('difficulty', 'easy')
        
        # Default pairs based on difficulty
        default_pairs = {
            'easy': 8,        # 4x4 = 16 cards = 8 pairs
            'intermediate': 18,  # 6x6 = 36 cards = 18 pairs
            'hard': 32        # 8x8 = 64 cards = 32 pairs
        }
        
        pairs_needed = int(request.query_params.get('pairs', default_pairs.get(difficulty, 8)))
        
        try:
            cards = MemoryGameCard.get_random_cards_for_game(difficulty, pairs_needed)
            serializer = self.get_serializer(cards, many=True)
            
            return Response({
                'difficulty': difficulty,
                'pairs_needed': pairs_needed,
                'cards_count': len(cards),
                'cards': serializer.data
            })
        except Exception as e:
            return Response(
                {'error': f'Error getting cards: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# MEMORY MATCH GAME VIEWS

class MemoryGameSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for memory game sessions
    """
    serializer_class = MemoryGameSessionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Filter sessions by user and optionally by hotel/tournament"""
        # For authenticated users, show their sessions
        if self.request.user.is_authenticated:
            qs = MemoryGameSession.objects.filter(user=self.request.user)
        else:
            # For anonymous users, only show anonymous sessions
            # This prevents anonymous users from seeing other users' data
            qs = MemoryGameSession.objects.filter(
                is_anonymous=True,
                user__isnull=True
            )
        
        # Filter by hotel
        hotel_slug = self.request.query_params.get('hotel')
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
            
        # Filter by tournament
        tournament_id = self.request.query_params.get('tournament')
        if tournament_id:
            qs = qs.filter(tournament_id=tournament_id)
            
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
            
        return qs.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MemoryGameSessionCreateSerializer
        return MemoryGameSessionSerializer
    
    def perform_create(self, serializer):
        """Create session and update user stats"""
        with transaction.atomic():
            session = serializer.save()
            
            # Update or create user stats only for authenticated users
            if session.user:
                stats, created = MemoryGameStats.objects.get_or_create(
                    user=session.user,
                    defaults={'hotel': session.hotel}
                )
                stats.update_stats_from_session(session)
                
                # Update tournament participation if applicable
                if session.tournament:
                    try:
                        participation = TournamentParticipation.objects.get(
                            tournament=session.tournament,
                            user=session.user
                        )
                        participation.update_from_session(session)
                    except TournamentParticipation.DoesNotExist:
                        pass
    
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def practice(self, request):
        """Create practice session (returns score only, not saved)"""
        # Validate the practice data
        time_seconds = request.data.get('time_seconds')
        moves_count = request.data.get('moves_count')
        difficulty = request.data.get('difficulty', 'intermediate')
        
        if not time_seconds or not moves_count:
            return Response({
                'error': 'time_seconds and moves_count are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate score using the same logic as the model
        multipliers = {'easy': 1.0, 'intermediate': 1.5, 'hard': 2.0}
        optimal_moves = {'easy': 16, 'intermediate': 24, 'hard': 32}
        
        base_score = multipliers[difficulty] * 1000
        time_penalty = int(time_seconds) * 2
        extra_moves = max(0, int(moves_count) - optimal_moves[difficulty])
        moves_penalty = extra_moves * 5
        
        calculated_score = int(base_score - time_penalty - moves_penalty)
        final_score = max(0, calculated_score)
        
        return Response({
            'score': final_score,
            'difficulty': difficulty,
            'time_seconds': int(time_seconds),
            'moves_count': int(moves_count),
            'is_practice': True,
            'base_score': base_score,
            'time_penalty': time_penalty,
            'moves_penalty': moves_penalty
        })

    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Get current user's memory game statistics"""
        try:
            stats = MemoryGameStats.objects.get(user=request.user)
            serializer = MemoryGameStatsSerializer(stats)
            return Response(serializer.data)
        except MemoryGameStats.DoesNotExist:
            return Response({
                'user': request.user.username,
                'total_games': 0,
                'message': 'No games played yet'
            })
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard for memory game"""
        difficulty = request.query_params.get('difficulty', 'easy')
        hotel_slug = request.query_params.get('hotel')
        limit = min(int(request.query_params.get('limit', 10)), 100)
        
        # Build base queryset
        qs = MemoryGameSession.objects.filter(
            completed=True,
            difficulty=difficulty
        ).select_related('user', 'hotel')
        
        # Filter by hotel if specified
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        
        # Get top scores
        top_sessions = qs.order_by('-score', 'time_seconds')[:limit]
        
        # Build leaderboard data
        leaderboard_data = []
        for rank, session in enumerate(top_sessions, 1):
            # Get player name (anonymous or user)
            player_name = session.player_name if session.is_anonymous else (
                session.user.username if session.user else "Anonymous"
            )
            
            leaderboard_data.append({
                'rank': rank,
                'user': player_name,
                'score': session.score,
                'time_seconds': session.time_seconds,
                'difficulty': session.difficulty,
                'achieved_at': session.created_at,
                'hotel': session.hotel.name if session.hotel else None
            })
        
        serializer = LeaderboardSerializer(leaderboard_data, many=True)
        return Response(serializer.data)


class MemoryGameTournamentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for memory game tournaments
    """
    serializer_class = MemoryGameTournamentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tournaments by hotel and status"""
        qs = MemoryGameTournament.objects.all()
        
        # Filter by hotel
        hotel_slug = self.request.query_params.get('hotel')
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
            
        return qs.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create tournament with current user as creator"""
        tournament = serializer.save(created_by=self.request.user)
        # Generate QR code for tournament
        tournament.generate_qr_code()
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def submit_score(self, request, pk=None):
        """Submit score to tournament after completing the game"""
        tournament = self.get_object()
        
        # Check if tournament is active
        if not tournament.is_active:
            return Response(
                {'error': 'Tournament is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get required data
        player_name = request.data.get('player_name')
        room_number = request.data.get('room_number')
        time_seconds = request.data.get('time_seconds')
        moves_count = request.data.get('moves_count')
        
        if not all([player_name, room_number, time_seconds, moves_count]):
            return Response({
                'error': 'All fields (name, room, time, moves) are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create tournament session with score
        session_data = {
            'player_name': player_name,
            'room_number': room_number,
            'is_anonymous': True,
            'difficulty': tournament.difficulty,
            'time_seconds': int(time_seconds),
            'moves_count': int(moves_count),
            'completed': True,
            'tournament': tournament,
            'hotel': tournament.hotel
        }
        
        session = MemoryGameSession.objects.create(**session_data)
        
        return Response({
            'message': 'Score submitted successfully!',
            'session_id': session.id,
            'score': session.score,
            'player_name': session.player_name,
            'rank': self.get_player_rank(tournament, session)
        }, status=status.HTTP_201_CREATED)
    
    def get_player_rank(self, tournament, session):
        """Calculate player's current rank in tournament"""
        better_sessions = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True,
            score__gt=session.score
        ).count()
        return better_sessions + 1
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get tournament leaderboard"""
        tournament = self.get_object()
        limit = min(int(request.query_params.get('limit', 20)), 100)
        
        leaderboard = tournament.get_leaderboard(limit)
        serializer = TournamentLeaderboardSerializer(leaderboard, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get tournament participants"""
        tournament = self.get_object()
        participants = tournament.participants.filter(
            status='registered'
        ).order_by('registered_at')
        
        serializer = TournamentParticipationSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start tournament (admin only)"""
        tournament = self.get_object()
        
        # Check permissions (admin or tournament creator)
        if not (request.user.is_staff or tournament.created_by == request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if tournament.status != 'upcoming':
            return Response(
                {'error': 'Tournament cannot be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tournament.status = 'active'
        tournament.save()
        
        return Response({'message': 'Tournament started successfully'})
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End tournament and calculate final rankings"""
        tournament = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or tournament.created_by == request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if tournament.status != 'active':
            return Response(
                {'error': 'Tournament is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update tournament status
            tournament.status = 'completed'
            tournament.save()
            
            # Calculate final rankings
            participants = TournamentParticipation.objects.filter(
                tournament=tournament
            ).order_by('-best_score', 'best_time')
            
            for rank, participant in enumerate(participants, 1):
                participant.final_rank = rank
                participant.save()
        
        return Response({'message': 'Tournament ended and rankings calculated'})

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def play_session(self, request, pk=None):
        """Create a game session for tournament (allows anonymous players)"""
        tournament = self.get_object()
        
        # Check if tournament is active
        if tournament.status != 'active':
            return Response(
                {'error': 'Tournament is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add tournament context to serializer
        serializer = MemoryGameSessionCreateSerializer(
            data=request.data,
            context={'request': request, 'tournament_id': tournament.id}
        )
        
        if serializer.is_valid():
            with transaction.atomic():
                session = serializer.save()
                
                # Update user stats only for authenticated users
                if session.user:
                    stats, created = MemoryGameStats.objects.get_or_create(
                        user=session.user,
                        defaults={'hotel': session.hotel}
                    )
                    stats.update_stats_from_session(session)
            
            return Response(
                MemoryGameSessionSerializer(session).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MemoryGameAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for memory game achievements
    """
    queryset = MemoryGameAchievement.objects.filter(is_active=True)
    serializer_class = MemoryGameAchievementSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        """Get current user's unlocked achievements"""
        achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement').order_by('-unlocked_at')
        
        serializer = UserAchievementSerializer(achievements, many=True)
        return Response(serializer.data)


class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard statistics for memory game
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        hotel_slug = request.query_params.get('hotel')
        
        # Build base queryset
        sessions_qs = MemoryGameSession.objects.filter(completed=True)
        if hotel_slug:
            sessions_qs = sessions_qs.filter(hotel__slug=hotel_slug)
        
        # Calculate statistics
        stats = {
            'total_players': sessions_qs.values('user').distinct().count(),
            'total_games_played': sessions_qs.count(),
            'average_score': sessions_qs.aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0,
            'top_score_today': sessions_qs.filter(
                created_at__date=timezone.now().date()
            ).aggregate(
                max_score=Max('score')
            )['max_score'] or 0,
            'active_tournaments': MemoryGameTournament.objects.filter(
                status='active'
            ).count(),
            'recent_achievements': UserAchievement.objects.select_related(
                'achievement', 'user'
            ).order_by('-unlocked_at')[:5],
            'popular_difficulty': sessions_qs.values('difficulty').annotate(
                count=Count('difficulty')
            ).order_by('-count').first(),
            'completion_rate': (
                sessions_qs.filter(completed=True).count() /
                max(MemoryGameSession.objects.count(), 1) * 100
            )
        }
        
        # Format popular difficulty
        if stats['popular_difficulty']:
            stats['popular_difficulty'] = stats['popular_difficulty']['difficulty']
        else:
            stats['popular_difficulty'] = 'easy'
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
