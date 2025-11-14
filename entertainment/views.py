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
    QuizCategory, Quiz, QuizQuestion, QuizAnswer, QuizSession, QuizSubmission,
    QuizTournament, QuizLeaderboard, TournamentLeaderboard
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
    MemoryGameAchievementSerializer,
    UserAchievementSerializer,
    LeaderboardSerializer,
    DashboardStatsSerializer,
    QuizCategoryListSerializer,
    QuizCategoryDetailSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizSessionCreateSerializer,
    QuizSessionDetailSerializer,
    QuizSessionSummarySerializer,
    QuizSubmissionSerializer,
    SubmitAnswerSerializer,
    QuizLeaderboardSerializer,
    QuizTournamentListSerializer,
    QuizTournamentDetailSerializer,
    TournamentLeaderboardSerializer,
    QuizQuestionSerializer
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


# ============================================================================
# GUESSTICULATOR QUIZ GAME VIEWS
# ============================================================================

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """Quiz endpoints - read-only"""
    permission_classes = [permissions.AllowAny]
    queryset = Quiz.objects.filter(is_active=True)
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizListSerializer
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, slug=None):
        """Generate QR code for quiz"""
        quiz = self.get_object()
        quiz.generate_qr_code()
        return Response({
            'success': True,
            'qr_code_url': quiz.qr_code_url,
            'generated_at': quiz.qr_generated_at
        })


class QuizCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Category endpoints - read-only"""
    permission_classes = [permissions.AllowAny]
    queryset = QuizCategory.objects.filter(is_active=True).order_by('order')
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizCategoryDetailSerializer
        return QuizCategoryListSerializer


class QuizGameViewSet(viewsets.ViewSet):
    """Main game logic endpoints"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def start_session(self, request):
        """Start a new game session"""
        import time
        import logging
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        player_name = request.data.get('player_name')
        session_token = request.data.get('session_token')
        is_tournament_mode = request.data.get('is_tournament_mode', False)
        tournament_slug = request.data.get('tournament_slug')
        
        logger.info(f"Quiz session start requested by {player_name}")
        
        if not player_name or not session_token:
            return Response(
                {'error': 'player_name and session_token are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quiz = Quiz.objects.get(slug='guessticulator', is_active=True)
        except Quiz.DoesNotExist:
            return Response(
                {'error': 'Quiz not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tournament = None
        if is_tournament_mode:
            if not tournament_slug:
                return Response(
                    {'error': 'tournament_slug required for tournament mode'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            tournament = get_object_or_404(
                QuizTournament,
                slug=tournament_slug
            )
            
            if not tournament.is_active:
                return Response(
                    {'error': 'Tournament is not currently active'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # NO RESUME - Always start fresh game
        # Delete any existing session with this token
        QuizSession.objects.filter(session_token=session_token).delete()
        
        # Get or create player progress tracker
        from .models import QuizPlayerProgress
        player_progress, _ = QuizPlayerProgress.objects.get_or_create(
            session_token=session_token,
            quiz=quiz
        )
        
        # Create new session
        session = QuizSession.objects.create(
            quiz=quiz,
            session_token=session_token,
            player_name=player_name,
            is_tournament_mode=is_tournament_mode,
            tournament=tournament
        )
        
        # Fetch categories
        categories = list(QuizCategory.objects.filter(
            is_active=True
        ).order_by('order'))
        
        if not categories:
            return Response(
                {'error': 'No categories available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuizSessionDetailSerializer(session)
        
        elapsed_time = time.time() - start_time
        logger.info(
            f"Quiz session created in {elapsed_time:.2f}s - "
            f"Player: {player_name}"
        )
        
        return Response({
            'session': serializer.data,
            'categories': QuizCategoryListSerializer(
                categories, many=True
            ).data,
            'total_categories': len(categories),
            'questions_per_category': quiz.questions_per_category,
            'game_rules': self._get_game_rules(quiz, categories)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def fetch_category_questions(self, request):
        """Fetch questions for a specific category"""
        session_id = request.query_params.get('session_id')
        category_slug = request.query_params.get('category_slug')
        
        if not session_id or not category_slug:
            return Response(
                {'error': 'session_id and category_slug are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = QuizSession.objects.get(id=session_id)
        except QuizSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            category = QuizCategory.objects.get(
                slug=category_slug,
                is_active=True
            )
        except QuizCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create player progress tracker
        from .models import QuizPlayerProgress
        player_progress, _ = QuizPlayerProgress.objects.get_or_create(
            session_token=session.session_token,
            quiz=session.quiz
        )
        
        count = session.quiz.questions_per_category
        
        if category.is_math_category:
            # Generate math questions
            questions = self._generate_math_questions_tracked(
                count,
                player_progress
            )
        else:
            # Get regular questions with tracking
            category_slug = category.slug
            seen_ids = set(
                player_progress.seen_question_ids.get(category_slug, [])
            )
            
            # Fetch questions
            all_questions = list(QuizQuestion.objects.filter(
                category=category,
                is_active=True
            ).prefetch_related('answers').order_by('?'))
            
            # Filter unseen questions
            unseen_questions = [
                q for q in all_questions
                if q.id not in seen_ids
            ]
            
            # If not enough unseen questions, reset
            if len(unseen_questions) < count:
                player_progress.seen_question_ids[category_slug] = []
                seen_ids = set()
                unseen_questions = all_questions
            
            # Take only the needed count
            selected_questions = unseen_questions[:count]
            
            # Serialize questions
            questions = []
            for q in selected_questions:
                questions.append({
                    'id': q.id,
                    'category_slug': q.category.slug,
                    'category_name': q.category.name,
                    'category_order': q.category.order,
                    'text': q.text,
                    'image_url': q.image_url,
                    'answers': [
                        {
                            'id': a.id,
                            'text': a.text,
                            'order': a.order
                        } for a in q.answers.all()
                    ]
                })
            
            # Mark as seen
            for q in selected_questions:
                if category_slug not in player_progress.seen_question_ids:
                    player_progress.seen_question_ids[category_slug] = []
                seen_list = player_progress.seen_question_ids[category_slug]
                if q.id not in seen_list:
                    seen_list.append(q.id)
            
            player_progress.save()
        
        return Response({
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'order': category.order,
                'is_math_category': category.is_math_category
            },
            'questions': questions,
            'question_count': len(questions)
        })
    
    def _generate_tracked_questions(self, categories, count, player_progress):
        """
        Generate questions with tracking to avoid repeats
        Player must see ALL questions before ANY repeat
        OPTIMIZED: Batch database queries to reduce DB round trips
        """
        all_questions = []
        
        # Batch fetch all questions for non-math categories at once
        non_math_categories = [
            c for c in categories if not c.is_math_category
        ]
        
        # Build a map of category_id -> questions for efficient lookup
        if non_math_categories:
            category_ids = [c.id for c in non_math_categories]
            # Fetch all questions at once with select_related to avoid N+1
            all_db_questions = QuizQuestion.objects.filter(
                category_id__in=category_ids,
                is_active=True
            ).select_related('category').prefetch_related(
                'answers'
            ).order_by('?')
            
            # Group questions by category
            questions_by_category = {}
            for question in all_db_questions:
                cat_id = question.category_id
                if cat_id not in questions_by_category:
                    questions_by_category[cat_id] = []
                questions_by_category[cat_id].append(question)
        else:
            questions_by_category = {}
        
        # Process each category
        for category in categories:
            if category.is_math_category:
                # Generate math questions from unseen pool
                math_questions = self._generate_math_questions_tracked(
                    count,
                    player_progress
                )
                category_questions = math_questions
            else:
                # Get seen IDs for this category
                category_slug = category.slug
                seen_ids = set(
                    player_progress.seen_question_ids.get(
                        category_slug, []
                    )
                )
                
                # Get questions from pre-fetched data
                available_questions = questions_by_category.get(
                    category.id, []
                )
                
                # Filter unseen questions
                unseen_questions = [
                    q for q in available_questions
                    if q.id not in seen_ids
                ]
                
                # If not enough unseen questions, reset
                if len(unseen_questions) < count:
                    player_progress.seen_question_ids[category_slug] = []
                    seen_ids = set()
                    unseen_questions = available_questions
                
                # Take only the needed count
                selected_questions = unseen_questions[:count]
                
                # Serialize questions (avoid N+1 by using prefetched data)
                category_questions = []
                for q in selected_questions:
                    category_questions.append({
                        'id': q.id,
                        'category_slug': q.category.slug,
                        'text': q.text,
                        'image_url': q.image_url,
                        'answers': [
                            {
                                'id': a.id,
                                'text': a.text,
                                'order': a.order
                            } for a in q.answers.all()
                        ]
                    })
                
                # Mark as seen
                new_seen_ids = [q['id'] for q in category_questions]
                if category_slug not in player_progress.seen_question_ids:
                    player_progress.seen_question_ids[category_slug] = []
                player_progress.seen_question_ids[category_slug].extend(
                    new_seen_ids
                )
            
            # Add category info
            for question in category_questions:
                question['category_name'] = category.name
                question['category_order'] = category.order
            
            all_questions.extend(category_questions)
        
        # Save progress once at the end
        player_progress.save()
        
        return all_questions
    
    def _get_game_rules(self, quiz, categories):
        """Get game rules object"""
        return {
            'time_per_question': quiz.time_per_question_seconds,
            'turbo_mode_threshold': quiz.turbo_mode_threshold,
            'turbo_multiplier': float(quiz.turbo_multiplier),
            'scoring': {
                'normal': {
                    '0s': 5, '1s': 5, '2s': 4, '3s': 3, '4s': 2, '5s': 0
                },
                'turbo': {
                    '0s': 10, '1s': 10, '2s': 8, '3s': 6, '4s': 4, '5s': 0
                }
            },
            'instructions': [
                f'Answer {quiz.questions_per_category} questions '
                f'from each of the {len(categories)} categories',
                f'You have {quiz.time_per_question_seconds} seconds '
                f'per question',
                f'Get {quiz.turbo_mode_threshold} correct answers '
                f'in a row to activate TURBO MODE (2x points)',
                'Wrong answer breaks your streak and deactivates '
                'Turbo Mode',
                'Faster answers = more points (5-4-3-2-0 points)',
                'Complete all 50 questions to finish the game'
            ]
        }
    
    def _get_category_questions(self, category, count=10):
        """Get questions for a category"""
        if category.is_math_category:
            return self._generate_math_questions(count)
        else:
            questions = QuizQuestion.objects.filter(
                category=category,
                is_active=True
            ).prefetch_related('answers').order_by('?')[:count]
            
            return QuizQuestionSerializer(questions, many=True).data
    
    def _generate_math_questions_tracked(self, count, player_progress):
        """
        Generate math questions with tracking
        Pool of 100 unique combinations - must exhaust before repeats
        """
        import random
        
        # Generate pool of 100 unique math questions
        all_possible = []
        operators = ['+', '-', '*', '/']
        operator_symbols = {'+': '+', '-': '-', '*': '×', '/': '÷'}
        
        # Generate predictable pool (0-10 range, 4 operators)
        for num1 in range(0, 11):
            for num2 in range(1, 11):
                for operator in operators:
                    if operator == '/':
                        # Only include if divisible
                        if num1 % num2 == 0:
                            all_possible.append((num1, num2, operator))
                    else:
                        all_possible.append((num1, num2, operator))
                    
                    if len(all_possible) >= 100:
                        break
                if len(all_possible) >= 100:
                    break
            if len(all_possible) >= 100:
                break
        
        # Filter out seen questions
        seen_set = {tuple(q[:3]) for q in player_progress.seen_math_questions}
        unseen = [q for q in all_possible if q not in seen_set]
        
        # Reset if we've seen all
        if len(unseen) < count:
            player_progress.seen_math_questions = []
            player_progress.save()
            unseen = all_possible
        
        # Pick random unseen questions
        selected = random.sample(unseen, min(count, len(unseen)))
        
        # Generate question objects
        questions = []
        for num1, num2, operator in selected:
            if operator == '+':
                correct_answer = num1 + num2
            elif operator == '-':
                correct_answer = num1 - num2
            elif operator == '*':
                correct_answer = num1 * num2
            else:
                correct_answer = num1 // num2
            
            wrong_answers = set()
            while len(wrong_answers) < 3:
                offset = random.choice([-3, -2, -1, 1, 2, 3])
                wrong = correct_answer + offset
                if wrong != correct_answer and wrong >= 0:
                    wrong_answers.add(int(wrong))
            
            answers = [
                {'id': 1, 'text': str(int(correct_answer)), 'order': 0},
                {'id': 2, 'text': str(list(wrong_answers)[0]), 'order': 1},
                {'id': 3, 'text': str(list(wrong_answers)[1]), 'order': 2},
                {'id': 4, 'text': str(list(wrong_answers)[2]), 'order': 3}
            ]
            
            random.shuffle(answers)
            for idx, ans in enumerate(answers):
                ans['order'] = idx
            
            question_text = f"{num1} {operator_symbols[operator]} {num2} = ?"
            
            questions.append({
                'id': None,
                'category_slug': 'dynamic-math',
                'text': question_text,
                'image_url': None,
                'answers': answers,
                'question_data': {
                    'num1': num1,
                    'num2': num2,
                    'operator': operator,
                    'correct_answer': int(correct_answer)
                }
            })
        
        # Mark as seen
        player_progress.mark_math_questions_seen(
            [(q['question_data']['num1'],
              q['question_data']['num2'],
              q['question_data']['operator']) for q in questions]
        )
        
        return questions
    
    @action(detail=False, methods=['post'])
    def submit_answer(self, request):
        """Submit an answer"""
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            session = QuizSession.objects.get(id=data['session_id'])
        except QuizSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if session.is_completed:
            return Response(
                {'error': 'Session already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        category = get_object_or_404(
            QuizCategory,
            slug=data['category_slug']
        )
        
        if category.is_math_category:
            question_data = data.get('question_data', {})
            correct_answer_value = str(question_data.get('correct_answer', ''))
        else:
            question = get_object_or_404(
                QuizQuestion,
                id=data.get('question_id')
            )
            correct_ans = question.correct_answer
            if not correct_ans:
                return Response(
                    {'error': 'Question has no correct answer defined'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            correct_answer_value = correct_ans.text
        
        is_correct = data['selected_answer'].strip() == correct_answer_value.strip()
        
        submission = QuizSubmission.objects.create(
            session=session,
            category=category,
            question=None if category.is_math_category else QuizQuestion.objects.get(id=data.get('question_id')),
            question_text=data['question_text'],
            question_data=data.get('question_data'),
            selected_answer=data['selected_answer'],
            selected_answer_id=data.get('selected_answer_id'),
            correct_answer=correct_answer_value,
            is_correct=is_correct,
            time_taken_seconds=data['time_taken_seconds'],
            was_turbo_active=session.is_turbo_active
        )
        
        points = submission.calculate_points()
        submission.points_awarded = points
        submission.save()
        
        session.score += points
        
        if is_correct and points > 0:
            session.consecutive_correct += 1
            
            turbo_threshold = session.quiz.turbo_mode_threshold
            if session.consecutive_correct >= turbo_threshold:
                session.is_turbo_active = True
        else:
            session.consecutive_correct = 0
            session.is_turbo_active = False
        
        session.save()
        session.refresh_from_db()
        
        return Response({
            'success': True,
            'submission': QuizSubmissionSerializer(submission).data,
            'session_updated': {
                'score': session.score,
                'consecutive_correct': session.consecutive_correct,
                'is_turbo_active': session.is_turbo_active
            }
        })
    
    @action(detail=False, methods=['post'])
    def complete_session(self, request):
        """Complete a game session and update leaderboards"""
        session_id = request.data.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = QuizSession.objects.get(id=session_id)
        except QuizSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if session.is_completed:
            return Response(
                {'error': 'Session already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.complete_session()
        
        leaderboard_entry, created = QuizLeaderboard.objects.get_or_create(
            quiz=session.quiz,
            session_token=session.session_token,
            defaults={
                'player_name': session.player_name,
                'best_score': session.score,
                'best_session': session,
                'games_played': 1
            }
        )
        
        if not created:
            if session.score > leaderboard_entry.best_score:
                leaderboard_entry.best_score = session.score
                leaderboard_entry.best_session = session
                leaderboard_entry.player_name = session.player_name
            leaderboard_entry.games_played += 1
            leaderboard_entry.save()
        
        if session.is_tournament_mode and session.tournament:
            tournament_entry, t_created = TournamentLeaderboard.objects.get_or_create(
                tournament=session.tournament,
                session_token=session.session_token,
                defaults={
                    'player_name': session.player_name,
                    'best_score': session.score,
                    'best_session': session
                }
            )
            
            if not t_created and session.score > tournament_entry.best_score:
                tournament_entry.best_score = session.score
                tournament_entry.best_session = session
                tournament_entry.player_name = session.player_name
                tournament_entry.save()
        
        all_time_rank = QuizLeaderboard.objects.filter(
            quiz=session.quiz,
            best_score__gt=session.score
        ).count() + 1
        
        tournament_rank = None
        if session.is_tournament_mode and session.tournament:
            tournament_rank = TournamentLeaderboard.objects.filter(
                tournament=session.tournament,
                best_score__gt=session.score
            ).count() + 1
        
        return Response({
            'success': True,
            'session': QuizSessionDetailSerializer(session).data,
            'rankings': {
                'all_time_rank': all_time_rank,
                'tournament_rank': tournament_rank
            },
            'is_new_best': created or (not created and session.score == leaderboard_entry.best_score)
        })
    
    @action(detail=False, methods=['get'])
    def get_session(self, request):
        """Get session details"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'session_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = QuizSession.objects.get(id=session_id)
        except QuizSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuizSessionDetailSerializer(session)
        return Response(serializer.data)


class QuizLeaderboardViewSet(viewsets.ViewSet):
    """Leaderboard endpoints"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'])
    def all_time(self, request):
        """Get all-time leaderboard"""
        limit = int(request.query_params.get('limit', 100))
        
        entries = QuizLeaderboard.objects.select_related(
            'quiz', 'best_session'
        ).order_by('-best_score', 'last_played')[:limit]
        
        for idx, entry in enumerate(entries, 1):
            entry.rank = idx
        
        serializer = QuizLeaderboardSerializer(entries, many=True)
        return Response({
            'count': entries.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def player_stats(self, request):
        """Get player's stats"""
        session_token = request.query_params.get('session_token')
        
        if not session_token:
            return Response(
                {'error': 'session_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            entry = QuizLeaderboard.objects.get(session_token=session_token)
        except QuizLeaderboard.DoesNotExist:
            return Response(
                {'error': 'No stats found for this player'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        rank = QuizLeaderboard.objects.filter(
            quiz=entry.quiz,
            best_score__gt=entry.best_score
        ).count() + 1
        
        entry.rank = rank
        
        serializer = QuizLeaderboardSerializer(entry)
        return Response(serializer.data)


class QuizTournamentViewSet(viewsets.ReadOnlyModelViewSet):
    """Tournament endpoints"""
    permission_classes = [permissions.AllowAny]
    queryset = QuizTournament.objects.all().order_by('-start_date')
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizTournamentDetailSerializer
        return QuizTournamentListSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get currently active tournament"""
        now = timezone.now()
        tournament = QuizTournament.objects.filter(
            status=QuizTournament.TournamentStatus.ACTIVE,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        if not tournament:
            return Response(
                {'error': 'No active tournament'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuizTournamentDetailSerializer(tournament)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, slug=None):
        """Get tournament leaderboard"""
        tournament = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        
        entries = TournamentLeaderboard.objects.filter(
            tournament=tournament
        ).select_related('best_session').order_by(
            '-best_score', 'updated_at'
        )[:limit]
        
        for idx, entry in enumerate(entries, 1):
            entry.rank = idx
        
        serializer = TournamentLeaderboardSerializer(entries, many=True)
        return Response({
            'tournament': tournament.name,
            'count': entries.count(),
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, slug=None):
        """Generate QR code for tournament"""
        tournament = self.get_object()
        tournament.generate_qr_code()
        return Response({
            'success': True,
            'qr_code_url': tournament.qr_code_url,
            'generated_at': tournament.qr_generated_at
        })
