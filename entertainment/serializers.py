from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from .models import (
    Game, GameHighScore, GameQRCode,
    MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament,
    TournamentParticipation, MemoryGameAchievement, UserAchievement
)

User = get_user_model()

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'title', 'slug', 'description', 'thumbnail', 'active']


class GameHighScoreSerializer(serializers.ModelSerializer):
    player = serializers.SerializerMethodField()
    game = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GameHighScore
        fields = ['id', 'player', 'game', 'hotel', 'score', 'achieved_at']

    def get_player(self, obj):
        return obj.player_name or (obj.user.username if obj.user else "Anonymous")


class GameHighScoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameHighScore
        fields = ['game', 'hotel', 'score', 'player_name']

    # create() no longer needs to handle get-or-create, handled in view
    def create(self, validated_data):
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        return GameHighScore.objects.create(user=user, **validated_data)


class GameQRCodeSerializer(serializers.ModelSerializer):
    game = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GameQRCode
        fields = ['id', 'game', 'hotel', 'qr_url', 'generated_at']


class MemoryGameCardSerializer(serializers.ModelSerializer):
    """Serializer for Memory Game Card images/emojis"""
    image_url = serializers.SerializerMethodField()
    available_difficulties = serializers.SerializerMethodField()
    
    class Meta:
        model = MemoryGameCard
        fields = [
            'id', 'name', 'slug', 'image_url', 'description', 
            'is_active', 'difficulty_levels', 'available_difficulties'
        ]
        read_only_fields = ['id', 'image_url', 'available_difficulties']

    def get_image_url(self, obj):
        """Get the full URL of the card image"""
        return obj.image_url

    def get_available_difficulties(self, obj):
        """Get list of difficulty levels this card is available for"""
        if not obj.difficulty_levels:
            return []
        return [level.strip() for level in obj.difficulty_levels.split(',')]


# MEMORY MATCH GAME SERIALIZERS

class MemoryGameSessionSerializer(serializers.ModelSerializer):
    """Serializer for memory game sessions"""
    user = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)
    tournament = serializers.StringRelatedField(read_only=True)
    difficulty_display = serializers.CharField(
        source='get_difficulty_display',
        read_only=True
    )
    cards_used = MemoryGameCardSerializer(many=True, read_only=True)
    player_display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MemoryGameSession
        fields = [
            'id', 'user', 'hotel', 'tournament', 'difficulty',
            'difficulty_display', 'time_seconds', 'moves_count',
            'score', 'completed', 'cards_used', 'created_at', 'updated_at',
            'player_name', 'room_number', 'is_anonymous', 'player_display_name'
        ]
        read_only_fields = [
            'id', 'user', 'score', 'created_at', 'updated_at',
            'cards_used', 'player_display_name'
        ]

    def get_player_display_name(self, obj):
        """Get display name for player (anonymous or user)"""
        if obj.is_anonymous and obj.player_name:
            return obj.player_name
        elif obj.user:
            return obj.user.username
        return "Anonymous Player"

    def validate_time_seconds(self, value):
        """Validate time is reasonable (not negative, not too large)"""
        if value < 1:
            raise serializers.ValidationError(
                "Time must be at least 1 second"
            )
        if value > 7200:  # 2 hours max
            raise serializers.ValidationError(
                "Time cannot exceed 2 hours"
            )
        return value

    def validate_moves_count(self, value):
        """Validate moves count is reasonable"""
        if value < 1:
            raise serializers.ValidationError(
                "Moves count must be at least 1"
            )
        if value > 1000:  # Reasonable max
            raise serializers.ValidationError(
                "Moves count seems unreasonably high"
            )
        return value


class MemoryGameSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating memory game sessions"""
    
    class Meta:
        model = MemoryGameSession
        fields = [
            'difficulty', 'time_seconds', 'moves_count',
            'completed', 'game_state', 'player_name',
            'room_number', 'is_anonymous'
        ]

    def validate(self, data):
        """Validate anonymous player requirements"""
        is_anonymous = data.get('is_anonymous', False)
        player_name = data.get('player_name')
        room_number = data.get('room_number')
        
        if is_anonymous:
            if not player_name:
                raise serializers.ValidationError({
                    'player_name': 'Player name required for anonymous players'
                })
            if not room_number:
                raise serializers.ValidationError({
                    'room_number': 'Room number required for anonymous players'
                })
        
        return data

    def create(self, validated_data):
        """Create session with authenticated user or anonymous player"""
        request = self.context['request']
        is_anonymous = validated_data.get('is_anonymous', False)
        
        # For anonymous players, don't set user
        if not is_anonymous and request.user.is_authenticated:
            validated_data['user'] = request.user
        
        # Get hotel from request context (from staff profile or URL)
        if request.user.is_authenticated:
            hotel = getattr(request.user, 'staff_profile', None)
            if hotel and hasattr(hotel, 'hotel'):
                validated_data['hotel'] = hotel.hotel
        else:
            # For anonymous users, try to get hotel from tournament context
            tournament_id = self.context.get('tournament_id')
            if tournament_id:
                try:
                    tournament = MemoryGameTournament.objects.get(
                        id=tournament_id,
                        status='active'
                    )
                    validated_data['hotel'] = tournament.hotel
                except MemoryGameTournament.DoesNotExist:
                    pass
            
        # Check if this is for a tournament
        tournament_id = self.context.get('tournament_id')
        if tournament_id:
            try:
                tournament = MemoryGameTournament.objects.get(
                    id=tournament_id,
                    status='active'
                )
                validated_data['tournament'] = tournament
            except MemoryGameTournament.DoesNotExist:
                pass
                
        return super().create(validated_data)


class MemoryGameStatsSerializer(serializers.ModelSerializer):
    """Serializer for user memory game statistics"""
    user = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = MemoryGameStats
        fields = [
            'user', 'hotel', 'total_games', 'games_won',
            'best_time_easy', 'best_time_intermediate', 'best_time_hard',
            'best_score_easy', 'best_score_intermediate', 'best_score_hard',
            'total_score', 'total_time_played', 'average_moves_per_game',
            'first_game_at', 'last_game_at'
        ]


class MemoryGameTournamentSerializer(serializers.ModelSerializer):
    """Serializer for memory game tournaments"""
    hotel = serializers.StringRelatedField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    participant_count = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    grid_size = serializers.SerializerMethodField()
    
    class Meta:
        model = MemoryGameTournament
        fields = [
            'id', 'hotel', 'name', 'slug', 'description', 'grid_size',
            'max_participants', 'min_age', 'max_age',
            'start_date', 'end_date', 'registration_deadline', 'status',
            'status_display', 'qr_code_url', 'first_prize', 'second_prize',
            'third_prize', 'rules', 'created_at', 'created_by',
            'participant_count', 'is_registration_open', 'is_active'
        ]
        read_only_fields = [
            'id', 'slug', 'qr_code_url', 'created_at', 'created_by'
        ]

    def get_grid_size(self, obj):
        """Return fixed grid size for all tournaments"""
        return "3x4 (6 pairs)"

    def validate(self, data):
        """Validate tournament dates"""
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "End date must be after start date"
            )
        if data['registration_deadline'] >= data['start_date']:
            raise serializers.ValidationError(
                "Registration deadline must be before start date"
            )
        if data['min_age'] >= data['max_age']:
            raise serializers.ValidationError(
                "Maximum age must be greater than minimum age"
            )
        return data


class TournamentParticipationSerializer(serializers.ModelSerializer):
    """Serializer for tournament participation"""
    user = serializers.StringRelatedField(read_only=True)
    tournament = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = TournamentParticipation
        fields = [
            'id', 'tournament', 'user', 'participant_name',
            'participant_age', 'registered_at', 'status', 'status_display',
            'best_score', 'best_time', 'final_rank', 'games_played',
            'total_score'
        ]
        read_only_fields = [
            'id', 'registered_at', 'best_score', 'best_time',
            'final_rank', 'games_played', 'total_score'
        ]

    def validate_participant_age(self, value):
        """Validate age against tournament requirements"""
        tournament = self.context.get('tournament')
        if tournament:
            if value < tournament.min_age:
                raise serializers.ValidationError(
                    f"Participant must be at least {tournament.min_age} years old"
                )
            if value > tournament.max_age:
                raise serializers.ValidationError(
                    f"Participant must be no older than {tournament.max_age} years old"
                )
        return value

    def create(self, validated_data):
        """Create participation with user and tournament context"""
        request = self.context['request']
        tournament = self.context['tournament']
        
        validated_data['user'] = request.user
        validated_data['tournament'] = tournament
        
        return super().create(validated_data)


class TournamentLeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for tournament leaderboard entries"""
    user = serializers.StringRelatedField(read_only=True)
    participant_name = serializers.SerializerMethodField()
    participant_age = serializers.IntegerField(
        source='tournament_participation.participant_age',
        read_only=True
    )
    rank = serializers.SerializerMethodField()
    
    class Meta:
        model = MemoryGameSession
        fields = [
            'id', 'user', 'participant_name', 'participant_age',
            'score', 'time_seconds', 'moves_count', 'created_at', 'rank',
            'room_number', 'is_anonymous'
        ]

    def get_participant_name(self, obj):
        """Get participant name (anonymous or from participation)"""
        if obj.is_anonymous and obj.player_name:
            return obj.player_name
        elif hasattr(obj, 'tournament_participation'):
            return obj.tournament_participation.participant_name
        elif obj.user:
            return obj.user.username
        return "Anonymous Player"

    def get_rank(self, obj):
        """Calculate rank based on score and time"""
        tournament = obj.tournament
        better_sessions = MemoryGameSession.objects.filter(
            tournament=tournament,
            completed=True
        ).filter(
            models.Q(score__gt=obj.score) |
            (models.Q(score=obj.score) & models.Q(time_seconds__lt=obj.time_seconds))
        ).count()
        return better_sessions + 1


class MemoryGameAchievementSerializer(serializers.ModelSerializer):
    """Serializer for memory game achievements"""
    type_display = serializers.CharField(
        source='get_achievement_type_display',
        read_only=True
    )
    difficulty_display = serializers.CharField(
        source='get_difficulty_display',
        read_only=True
    )
    
    class Meta:
        model = MemoryGameAchievement
        fields = [
            'id', 'name', 'description', 'achievement_type',
            'type_display', 'required_value', 'difficulty',
            'difficulty_display', 'icon_url', 'badge_color'
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    user = serializers.StringRelatedField(read_only=True)
    achievement = MemoryGameAchievementSerializer(read_only=True)
    session = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'unlocked_at', 'session']


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for various leaderboard views"""
    rank = serializers.IntegerField()
    user = serializers.CharField()
    score = serializers.IntegerField()
    time_seconds = serializers.IntegerField()
    difficulty = serializers.CharField()
    achieved_at = serializers.DateTimeField()
    hotel = serializers.CharField(required=False)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_players = serializers.IntegerField()
    total_games_played = serializers.IntegerField()
    average_score = serializers.FloatField()
    top_score_today = serializers.IntegerField()
    active_tournaments = serializers.IntegerField()
    recent_achievements = UserAchievementSerializer(many=True)
    popular_difficulty = serializers.CharField()
    completion_rate = serializers.FloatField()
