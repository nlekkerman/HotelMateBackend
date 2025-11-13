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
    TournamentParticipation, MemoryGameAchievement, UserAchievement,
    QuizCategory, Quiz, QuizSession, QuizSubmission
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
    DashboardStatsSerializer,
    QuizCategorySerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizSessionCreateSerializer,
    QuizSessionSerializer,
    QuizSubmissionCreateSerializer,
    QuizSubmissionSerializer,
    QuizLeaderboardSerializer
)


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """List all games or retrieve a single game."""
    queryset = Game.objects.filter(active=True)
    serializer_class = GameSerializer
    permission_classes = [permissions.AllowAny]


class GameHighScoreViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin):
    """List highscores or submit a new highscore."""
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

        # Order by score descending
        return qs.order_by('-score')

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
        - pairs: number of pairs needed (default: 6 for 3x4 grid)
        - grid_size: grid size (default: 3x4)
        """
        # Fixed 3x4 grid = 12 cards = 6 pairs (no more difficulty levels)
        grid_size = request.query_params.get('grid_size', '3x4')
        pairs_needed = int(request.query_params.get('pairs', 6))  # Default 6 pairs for 3x4
        
        # Ensure we don't exceed reasonable limits
        if pairs_needed > 50:  # Max 50 pairs for safety
            pairs_needed = 50
        elif pairs_needed < 1:
            pairs_needed = 6
        
        try:
            # Get random cards (all active cards, no difficulty filtering)
            cards = MemoryGameCard.get_random_cards_for_game('easy', pairs_needed)
            serializer = self.get_serializer(cards, many=True)
            
            return Response({
                'grid_size': grid_size,
                'pairs_needed': pairs_needed,
                'cards_count': len(cards),
                'total_cards': pairs_needed * 2,  # Each card appears twice
                'cards': serializer.data,
                'game_config': {
                    'grid_type': '3x4 grid (6 pairs)',
                    'optimal_moves': 12,  # 6 pairs * 2 moves each
                    'scoring': {
                        'base_score': 1000,
                        'time_penalty': 2,  # -2 points per second
                        'move_penalty': 5   # -5 points per extra move
                    }
                }
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
        """Get all anonymous tournament sessions"""
        # All sessions are now anonymous - no user filtering needed
        qs = MemoryGameSession.objects.all()
        
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
        """Create session for anonymous players"""
        # Simply save the session - no user stats needed for anonymous players
        session = serializer.save()
    
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
        # Always return the full ordered leaderboard (ignore any 'limit' param)
        # Build base queryset
        qs = MemoryGameSession.objects.filter(
            completed=True,
            difficulty=difficulty
        ).select_related('hotel')
        
        # Filter by hotel if specified
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        
        # Get full ordered sessions
        top_sessions = qs.order_by('-score', 'time_seconds')
        
        # Build leaderboard data
        leaderboard_data = []
        for rank, session in enumerate(top_sessions, 1):
            # Get clean player name from token format
            player_name = (session.player_name.split('|')[0]
                           if session.player_name else "Anonymous")
            
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
    permission_classes = [permissions.AllowAny]  # Allow anonymous access for tournament info
    
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
        """Submit score to tournament - uses player_token for tracking"""
        tournament = self.get_object()
        
        # Check if tournament is active
        if not tournament.is_active:
            return Response(
                {'error': 'Tournament is not currently active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get required data
        player_token = request.data.get('player_token')
        player_name = request.data.get('player_name')
        room_number = request.data.get('room_number')
        time_seconds = request.data.get('time_seconds')
        moves_count = request.data.get('moves_count')
        
        if not all([player_token, player_name, room_number, time_seconds, moves_count]):
            return Response({
                'error': 'All fields (token, name, room, time, moves) are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate score for this game
        calculated_score = self.calculate_score(int(time_seconds), int(moves_count))
        
        # Check if player (by token) already has a score in this tournament
        # We store the token in player_name field as "name|token"
        existing_session = MemoryGameSession.objects.filter(
            tournament=tournament,
            player_name__endswith=f"|{player_token}"
        ).first()
        
        is_new_personal_best = False
        
        if existing_session:
            # Player exists - update only if new score is better
            if calculated_score > existing_session.score:
                # Update the session with new data
                existing_session.player_name = f"{player_name}|{player_token}"
                existing_session.room_number = room_number
                existing_session.time_seconds = int(time_seconds)
                existing_session.moves_count = int(moves_count)
                existing_session.score = calculated_score
                existing_session.save()
                session = existing_session
                is_new_personal_best = True
                message = f'New personal best! Your score: {calculated_score}'
            else:
                # Not better than existing score
                return Response({
                    'message': f'Good try! Your best remains {existing_session.score}',
                    'score': calculated_score,
                    'best_score': existing_session.score,
                    'is_personal_best': False,
                    'rank': self.get_player_rank_by_score(tournament, existing_session.score),
                    'player_token': player_token,
                    'updated': False
                }, status=status.HTTP_200_OK)
        else:
            # New player - create new session
            session_data = {
                'player_name': f"{player_name}|{player_token}",
                'room_number': room_number,
                'is_anonymous': True,
                'difficulty': 'intermediate',  # Fixed for 3x4 grid
                'time_seconds': int(time_seconds),
                'moves_count': int(moves_count),
                'completed': True,
                'tournament': tournament,
                'hotel': tournament.hotel
            }
            
            session = MemoryGameSession.objects.create(**session_data)
            is_new_personal_best = True
            message = f'Welcome to the tournament! Your score: {calculated_score}'
        
        # Extract clean name for response
        clean_name = player_name
        
        return Response({
            'message': message,
            'session_id': session.id,
            'score': calculated_score,
            'best_score': session.score,
            'player_name': clean_name,
            'player_token': player_token,
            'rank': self.get_player_rank_by_score(tournament, session.score),
            'is_personal_best': is_new_personal_best,
            'updated': True
        }, status=status.HTTP_201_CREATED)
    
    def calculate_score(self, time_seconds, moves_count):
        """Calculate score for 3x4 grid (6 pairs = 12 cards)"""
        base_score = 1000
        optimal_moves = 12  # Perfect game = 6 pairs × 2 moves
        
        # Penalties
        time_penalty = time_seconds * 2      # 2 points per second
        extra_moves = max(0, moves_count - optimal_moves)
        moves_penalty = extra_moves * 5      # 5 points per extra move
        
        calculated_score = int(base_score - time_penalty - moves_penalty)
        return max(0, calculated_score)  # Never negative
    
    def is_high_score(self, tournament, score):
        """Check if score qualifies as a high score worth saving"""
        # Get current top scores (limit to top 50 to keep leaderboard manageable)
        top_scores = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True
        ).order_by('-score')[:50]
        
        # If less than 50 scores, always save
        if top_scores.count() < 50:
            return True
        
        # Check if score beats the 50th best score
        lowest_top_score = top_scores.last().score
        return score > lowest_top_score
    
    def get_leaderboard_threshold(self, tournament):
        """Get the minimum score needed to make the leaderboard"""
        top_scores = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True
        ).order_by('-score')[:50]
        
        if top_scores.count() < 50:
            return 0  # Any score qualifies
        
        return top_scores.last().score

    def get_player_best_score(self, tournament, player_name):
        """Get a player's best score in this tournament"""
        best_session = MemoryGameSession.objects.filter(
            tournament=tournament,
            player_name=player_name,
            completed=True
        ).order_by('-score').first()
        
        return best_session.score if best_session else 0

    def get_player_rank_by_score(self, tournament, player_score):
        """Calculate rank based on a specific score"""
        better_scores = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True,
            score__gt=player_score
        ).count()
        
        return better_scores + 1

    def get_player_rank(self, tournament, session):
        """Calculate player's current rank in tournament"""
        return self.get_player_rank_by_score(tournament, session.score)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def generate_qr_code(self, request, pk=None):
        """Generate QR code pointing to game dashboard"""
        tournament = self.get_object()
        
        success = tournament.generate_qr_code()
        
        if success:
            base_url = "https://hotelsmates.com/games/memory-match/tournaments"
            tournament_url = f"{base_url}?hotel={tournament.hotel.slug}"
            return Response({
                'message': 'QR code generated successfully',
                'qr_code_url': tournament.qr_code_url,
                'tournament_url': tournament_url,
                'generated_at': tournament.qr_generated_at
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to generate QR code'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def active_for_hotel(self, request):
        """Get active tournaments for a specific hotel"""
        hotel_slug = request.query_params.get('hotel')
        if not hotel_slug:
            return Response({
                'error': 'Hotel parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        tournaments = self.get_queryset().filter(
            hotel__slug=hotel_slug,
            status='active'
        ).order_by('start_date')
        
        serializer = self.get_serializer(tournaments, many=True)
        return Response({
            'tournaments': serializer.data,
            'count': tournaments.count()
        })

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.AllowAny]
    )
    def summary(self, request):
        """Return a compact summary for frontend: active, next (upcoming), previous (most recent completed).

        Query params:
        - hotel: hotel slug (required)

        Response shape:
        {
          "active": {id, name, start_date, end_date} | null,
          "next": {id, name, start_date} | null,
          "previous": {id, name, end_date} | null
        }
        """
        hotel_slug = request.query_params.get('hotel')
        if not hotel_slug:
            return Response({'error': 'hotel parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()

        # Currently active tournament (if any)
        active = MemoryGameTournament.objects.filter(
            hotel__slug=hotel_slug,
            status=MemoryGameTournament.TournamentStatus.ACTIVE,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('start_date').first()

        # Next upcoming tournament (earliest start_date in future)
        next_t = MemoryGameTournament.objects.filter(
            hotel__slug=hotel_slug,
            status=MemoryGameTournament.TournamentStatus.UPCOMING,
            start_date__gt=now
        ).order_by('start_date').first()

        # Most recent completed tournament
        previous = MemoryGameTournament.objects.filter(
            hotel__slug=hotel_slug,
            status=MemoryGameTournament.TournamentStatus.COMPLETED,
            end_date__lt=now
        ).order_by('-end_date').first()

        def short(t, include_start=False, include_end=False):
            if not t:
                return None
            data = {'id': t.id, 'name': t.name}
            if include_start and getattr(t, 'start_date', None):
                data['start_date'] = t.start_date
            if include_end and getattr(t, 'end_date', None):
                data['end_date'] = t.end_date
            return data

        payload = {
            'active': short(active, include_start=True, include_end=True),
            'next': short(next_t, include_start=True),
            'previous': short(previous, include_end=True)
        }

        return Response(payload)
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """Get tournament leaderboard with clean player names"""
        tournament = self.get_object()

        # Always return the full ordered tournament leaderboard (ignore 'limit')
        sessions = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True
        ).order_by('-score', 'time_seconds')
        
        leaderboard_data = []
        for session in sessions:
            # Extract clean player name (before the | token separator)
            clean_name = session.player_name.split('|')[0] if '|' in session.player_name else session.player_name
            
            leaderboard_data.append({
                'session_id': session.id,
                'player_name': clean_name,
                'room_number': session.room_number,
                'score': session.score,
                'time_seconds': session.time_seconds,
                'moves_count': session.moves_count,
                'created_at': session.created_at
            })
        
        return Response(leaderboard_data)
    
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
            # Create session for anonymous tournament players
            session = serializer.save()
            
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


# QUIZ GAME VIEWS

class QuizCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for quiz categories (read-only, global)
    """
    queryset = QuizCategory.objects.filter(is_active=True)
    serializer_class = QuizCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """Filter active categories"""
        return QuizCategory.objects.filter(is_active=True).order_by('name')


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for quizzes (read-only, global)
    Supports filtering by difficulty, category, and daily status
    """
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        """Filter quizzes by various parameters"""
        qs = Quiz.objects.filter(is_active=True)

        # Filter by difficulty level
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            try:
                difficulty_int = int(difficulty)
                qs = qs.filter(difficulty_level=difficulty_int)
            except ValueError:
                pass

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__id=category)

        # Filter by daily status
        is_daily = self.request.query_params.get('is_daily')
        if is_daily is not None:
            is_daily_bool = is_daily.lower() in ['true', '1', 'yes']
            qs = qs.filter(is_daily=is_daily_bool)

        return qs.select_related('category').order_by('difficulty_level',
                                                      'title')

    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list for list"""
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizListSerializer

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.AllowAny])
    def generate_math_question(self, request, slug=None):
        """
        Generate a dynamic math question for Level 4 quizzes
        Returns question with 4 shuffled options (1 correct, 3 distractors)
        """
        import random

        quiz = self.get_object()

        # Verify this is a math quiz
        if not quiz.is_math_quiz:
            return Response({
                'error': 'This endpoint is only for Dynamic Math quizzes'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate random math problem
        num1 = random.randint(0, 10)
        num2 = random.randint(0, 10)
        operation = random.choice(['+', '-', '×', '÷'])

        # Calculate correct answer
        if operation == '+':
            correct_answer = num1 + num2
            question_text = f"What is {num1} + {num2}?"
        elif operation == '-':
            correct_answer = num1 - num2
            question_text = f"What is {num1} - {num2}?"
        elif operation == '×':
            correct_answer = num1 * num2
            question_text = f"What is {num1} × {num2}?"
        else:  # ÷
            # Ensure whole number division
            num1 = num2 * random.randint(1, 10)
            correct_answer = num1 // num2
            question_text = f"What is {num1} ÷ {num2}?"

        # Generate 3 believable distractors
        distractors = set()
        while len(distractors) < 3:
            # Generate distractors close to correct answer
            offset = random.choice([-2, -1, 1, 2, 3, -3])
            distractor = correct_answer + offset
            if distractor != correct_answer and distractor >= 0:
                distractors.add(distractor)

        # Create answer options (1 correct + 3 distractors)
        answers = [str(correct_answer)] + \
            [str(d) for d in list(distractors)[:3]]

        # Shuffle answers
        random.shuffle(answers)

        return Response({
            'question_text': question_text,
            'answers': answers,
            'question_data': {
                'num1': num1,
                'num2': num2,
                'operation': operation,
                'correct_answer': correct_answer
            },
            'base_points': 10,
            'time_limit': quiz.get_time_per_question()
        })


class QuizSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quiz sessions
    Handles session creation, answer submission, and completion
    """
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        """Filter sessions by hotel and quiz"""
        qs = QuizSession.objects.all()

        # Filter by hotel
        hotel = self.request.query_params.get('hotel')
        if hotel:
            qs = qs.filter(hotel_identifier=hotel)

        # Filter by quiz
        quiz_slug = self.request.query_params.get('quiz')
        if quiz_slug:
            qs = qs.filter(quiz__slug=quiz_slug)

        # Filter by completion status
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            is_completed_bool = is_completed.lower() in ['true', '1', 'yes']
            qs = qs.filter(is_completed=is_completed_bool)

        return qs.select_related('quiz').order_by('-started_at')

    def get_serializer_class(self):
        """Use create serializer for create action"""
        if self.action == 'create':
            return QuizSessionCreateSerializer
        return QuizSessionSerializer

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.AllowAny])
    def submit_answer(self, request, id=None):
        """
        Submit an answer to a quiz question
        Auto-validates and calculates score
        """
        session = self.get_object()

        # Create submission
        serializer = QuizSubmissionCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            submission = serializer.save()

            # Check if quiz is complete
            quiz = session.quiz
            total_questions = quiz.max_questions
            completed_count = session.submissions.count()

            if completed_count >= total_questions:
                session.complete_session()

            return Response({
                'submission': QuizSubmissionSerializer(submission).data,
                'session': QuizSessionSerializer(session).data,
                'quiz_completed': session.is_completed
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'],
            permission_classes=[permissions.AllowAny])
    def complete(self, request, id=None):
        """
        Manually complete a quiz session
        Useful for timeout or early exit scenarios
        """
        session = self.get_object()

        if session.is_completed:
            return Response({
                'message': 'Session already completed',
                'session': QuizSessionSerializer(session).data
            })

        session.complete_session()

        return Response({
            'message': 'Session completed',
            'session': QuizSessionSerializer(session).data
        })

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.AllowAny])
    def general_leaderboard(self, request):
        """
        GENERAL LEADERBOARD - All completed sessions (practice + tournament)
        Query params:
        - quiz: quiz slug (required)
        - hotel: hotel identifier (required)
        - period: 'daily', 'weekly', 'all' (default: 'all')
        - limit: number of results (default: 50)
        """
        quiz_slug = request.query_params.get('quiz')
        hotel = request.query_params.get('hotel')
        period = request.query_params.get('period', 'all')
        limit = int(request.query_params.get('limit', 50))

        if not quiz_slug or not hotel:
            return Response({
                'error': 'Both quiz and hotel parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build queryset - ALL completed sessions
        qs = QuizSession.objects.filter(
            quiz__slug=quiz_slug,
            hotel_identifier=hotel,
            is_completed=True
        ).select_related('quiz')

        # Apply period filter
        if period == 'daily':
            qs = qs.filter(finished_at__date=timezone.now().date())
        elif period == 'weekly':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            qs = qs.filter(finished_at__gte=week_ago)

        # Order and limit
        top_sessions = qs.order_by('-score', 'time_spent_seconds')[:limit]

        # Build leaderboard
        leaderboard_data = []
        for rank, session in enumerate(top_sessions, 1):
            leaderboard_data.append({
                'rank': rank,
                'player_name': session.player_name,
                'room_number': session.room_number,
                'score': session.score,
                'time_spent_seconds': session.time_spent_seconds,
                'duration_formatted': session.duration_formatted,
                'finished_at': session.finished_at,
                'is_practice_mode': session.is_practice_mode,
                'hotel_identifier': session.hotel_identifier
            })

        serializer = QuizLeaderboardSerializer(leaderboard_data, many=True)
        return Response({
            'quiz': quiz_slug,
            'hotel': hotel,
            'period': period,
            'leaderboard_type': 'general',
            'description': 'All players (practice + tournament mode)',
            'count': len(leaderboard_data),
            'leaderboard': serializer.data
        })

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.AllowAny])
    def tournament_leaderboard(self, request):
        """
        TOURNAMENT LEADERBOARD - Only tournament mode sessions
        (is_practice_mode=False AND has room_number)
        Query params:
        - quiz: quiz slug (required)
        - hotel: hotel identifier (required)
        - period: 'daily', 'weekly', 'all' (default: 'all')
        - limit: number of results (default: 50)
        """
        quiz_slug = request.query_params.get('quiz')
        hotel = request.query_params.get('hotel')
        period = request.query_params.get('period', 'all')
        limit = int(request.query_params.get('limit', 50))

        if not quiz_slug or not hotel:
            return Response({
                'error': 'Both quiz and hotel parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build queryset - ONLY tournament mode sessions
        qs = QuizSession.objects.filter(
            quiz__slug=quiz_slug,
            hotel_identifier=hotel,
            is_completed=True,
            is_practice_mode=False,
            room_number__isnull=False
        ).exclude(room_number='').select_related('quiz')

        # Apply period filter
        if period == 'daily':
            qs = qs.filter(finished_at__date=timezone.now().date())
        elif period == 'weekly':
            week_ago = timezone.now() - timezone.timedelta(days=7)
            qs = qs.filter(finished_at__gte=week_ago)

        # Order and limit
        top_sessions = qs.order_by('-score', 'time_spent_seconds')[:limit]

        # Build leaderboard
        leaderboard_data = []
        for rank, session in enumerate(top_sessions, 1):
            leaderboard_data.append({
                'rank': rank,
                'player_name': session.player_name,
                'room_number': session.room_number,
                'score': session.score,
                'time_spent_seconds': session.time_spent_seconds,
                'duration_formatted': session.duration_formatted,
                'finished_at': session.finished_at,
                'is_practice_mode': session.is_practice_mode,
                'hotel_identifier': session.hotel_identifier
            })

        serializer = QuizLeaderboardSerializer(leaderboard_data, many=True)
        return Response({
            'quiz': quiz_slug,
            'hotel': hotel,
            'period': period,
            'leaderboard_type': 'tournament',
            'description': 'Tournament players only (with room numbers)',
            'count': len(leaderboard_data),
            'leaderboard': serializer.data
        })

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.AllowAny])
    def leaderboard(self, request):
        """
        DEPRECATED: Use general_leaderboard or tournament_leaderboard instead
        This redirects to general_leaderboard for backwards compatibility
        """
        return self.general_leaderboard(request)
