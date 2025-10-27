from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Avg, Min, Max, Count
from cloudinary.models import CloudinaryField
import uuid
import qrcode
from io import BytesIO
import cloudinary.uploader

User = get_user_model()


class Game(models.Model):
    """
    Metadata for a game (global, not tied to any hotel)
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    thumbnail = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class GameHighScore(models.Model):
    """
    Persistent highscore per user/game, optionally tied to a hotel.
    Supports anonymous players via player_name.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    player_name = models.CharField(max_length=50, blank=True, null=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='highscores')
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.SET_NULL, null=True, blank=True
    )
    score = models.IntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score']

    def __str__(self):
        name = self.player_name or (self.user.username if self.user else "Anonymous")
        hotel_str = self.hotel.slug if self.hotel else "No Hotel"
        return f"{name} - {self.game.title} @ {hotel_str}: {self.score}"


class GameQRCode(models.Model):
    """
    Optional QR codes for accessing specific games.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    hotel = models.ForeignKey(
        'hotel.Hotel', on_delete=models.SET_NULL, null=True, blank=True
    )
    qr_url = models.URLField(blank=True, null=True)
    generated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('game', 'hotel')

    def __str__(self):
        hotel_str = self.hotel.slug if self.hotel else "Global"
        return f"{hotel_str} / {self.game.slug}"

    def generate_qr(self):
        """
        Generate and upload QR code for this game (optionally for a hotel)
        """
        import qrcode
        from io import BytesIO
        import cloudinary.uploader

        hotel_slug = self.hotel.slug if self.hotel else "global"
        url = f"https://hotelsmates.com/games/{hotel_slug}/{self.game.slug}"

        # Build QR code
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, "PNG")
        img_io.seek(0)

        # Upload to Cloudinary
        upload = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"games_qr/{hotel_slug}_{self.game.slug}"
        )
        self.qr_url = upload.get('secure_url')
        self.generated_at = timezone.now()
        self.save()
        return True


# MEMORY MATCH GAME MODELS

class MemoryGameDifficulty(models.TextChoices):
    """Memory game difficulty levels"""
    EASY = 'easy', 'Easy (4x4)'
    INTERMEDIATE = 'intermediate', 'Intermediate (6x6)'
    HARD = 'hard', 'Hard (8x8)'


class MemoryGameCard(models.Model):
    """
    Card images/emojis used in Memory Match Game
    """
    name = models.CharField(
        max_length=100,
        help_text="Card name/identifier (e.g., 'alien', 'fox', 'smiley')"
    )
    slug = models.SlugField(
        max_length=100, 
        unique=True,
        help_text="URL-friendly identifier"
    )
    image = CloudinaryField(
        'memory_card_image',
        folder="memory_game_cards/",
        transformation={
            "width": 200,
            "height": 200,
            "crop": "fit",
            "quality": "auto"
        },
        help_text="Card image file"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the card"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this card is available for games"
    )
    difficulty_levels = models.CharField(
        max_length=50,
        default="easy,intermediate,hard",
        help_text="Comma-separated difficulty levels where this card appears"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"

    @property
    def image_url(self):
        """Get the full URL of the card image"""
        return str(self.image) if self.image else None

    def is_available_for_difficulty(self, difficulty):
        """Check if card is available for given difficulty level"""
        if not self.is_active:
            return False
        return difficulty in self.difficulty_levels.split(',')

    @classmethod
    def get_cards_for_difficulty(cls, difficulty, count=None):
        """Get active cards available for a specific difficulty level"""
        cards = cls.objects.filter(
            is_active=True,
            difficulty_levels__icontains=difficulty
        ).order_by('name')
        
        if count:
            return cards[:count]
        return cards

    @classmethod
    def get_random_cards_for_game(cls, difficulty, pairs_needed):
        """Get random cards for a memory game session"""
        available_cards = cls.get_cards_for_difficulty(difficulty)
        
        if available_cards.count() < pairs_needed:
            # If not enough cards, repeat some cards
            cards_list = list(available_cards)
            import random
            random.shuffle(cards_list)
            selected_cards = (cards_list * ((pairs_needed // len(cards_list)) + 1))[:pairs_needed]
        else:
            # Randomly select required number of cards
            import random
            selected_cards = random.sample(list(available_cards), pairs_needed)
        
        return selected_cards


class MemoryGameSession(models.Model):
    """
    Individual memory game session with scoring and statistics
    Supports anonymous players for kids tournaments
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='memory_game_sessions',
        null=True,
        blank=True,
        help_text="Registered user (optional for anonymous players)"
    )
    # Anonymous player support for kids tournaments
    player_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Anonymous player name (e.g., 'Player 1234')"
    )
    room_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Room number or 'Kids Tournament' for anonymous"
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="True if this is an anonymous kids tournament entry"
    )
    
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        help_text="Hotel where the game was played"
    )
    tournament = models.ForeignKey(
        'MemoryGameTournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        help_text="Tournament this session belongs to"
    )
    
    # Game Configuration
    difficulty = models.CharField(
        max_length=12,
        choices=MemoryGameDifficulty.choices,
        default=MemoryGameDifficulty.EASY
    )
    
    # Game Results
    time_seconds = models.PositiveIntegerField(
        help_text="Time taken to complete the game in seconds"
    )
    moves_count = models.PositiveIntegerField(
        help_text="Number of moves/flips made"
    )
    score = models.IntegerField(
        default=0,
        help_text="Calculated score based on time, moves, and difficulty"
    )
    completed = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional game state data (for incomplete games)
    game_state = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON data for saving/resuming incomplete games"
    )
    
    # Cards used in this game session
    cards_used = models.ManyToManyField(
        MemoryGameCard,
        blank=True,
        related_name='game_sessions',
        help_text="Cards that were used in this game session"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'difficulty']),
            models.Index(fields=['hotel', 'created_at']),
            models.Index(fields=['tournament', 'score']),
        ]

    def __str__(self):
        return (f"{self.user.username} - {self.difficulty} - "
                f"{self.score} pts ({self.time_seconds}s)")

    def calculate_score(self):
        """
        Calculate score based on time and moves for 3x4 grid (6 pairs)
        Formula: 1000 - time_penalty - moves_penalty
        """
        # Fixed scoring for 3x4 grid tournaments (6 pairs = 12 cards)
        base_score = 1000
        optimal_moves = 12  # 6 pairs * 2 moves (perfect game)
        
        # Penalties
        time_penalty = self.time_seconds * 2  # 2 points per second
        extra_moves = max(0, self.moves_count - optimal_moves)
        moves_penalty = extra_moves * 5  # 5 points per extra move
        
        calculated_score = int(base_score - time_penalty - moves_penalty)
        return max(0, calculated_score)  # Ensure score is not negative

    def save(self, *args, **kwargs):
        """Auto-calculate score on save"""
        if self.completed and self.time_seconds and self.moves_count:
            self.score = self.calculate_score()
        super().save(*args, **kwargs)


class MemoryGameStats(models.Model):
    """
    Aggregate statistics for a user's memory game performance
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='memory_game_stats'
    )
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Primary hotel for this user's stats"
    )
    
    # Game counts
    total_games = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    
    # Best times by difficulty (in seconds)
    best_time_easy = models.PositiveIntegerField(null=True, blank=True)
    best_time_intermediate = models.PositiveIntegerField(null=True, blank=True)
    best_time_hard = models.PositiveIntegerField(null=True, blank=True)
    
    # Best scores by difficulty
    best_score_easy = models.IntegerField(default=0)
    best_score_intermediate = models.IntegerField(default=0)
    best_score_hard = models.IntegerField(default=0)
    
    # Aggregate stats
    total_score = models.IntegerField(default=0)
    total_time_played = models.PositiveIntegerField(default=0)  # seconds
    average_moves_per_game = models.FloatField(default=0.0)
    
    # Timestamps
    first_game_at = models.DateTimeField(null=True, blank=True)
    last_game_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Memory Game Stats"

    def __str__(self):
        return f"{self.user.username} - {self.total_games} games - {self.total_score} pts"

    def update_stats_from_session(self, session):
        """Update stats based on a new game session"""
        self.total_games += 1
        self.games_won += 1 if session.completed else 0
        self.total_score += session.score
        self.total_time_played += session.time_seconds
        
        # Update best times
        if session.difficulty == 'easy':
            if not self.best_time_easy or session.time_seconds < self.best_time_easy:
                self.best_time_easy = session.time_seconds
            if session.score > self.best_score_easy:
                self.best_score_easy = session.score
                
        elif session.difficulty == 'intermediate':
            if not self.best_time_intermediate or session.time_seconds < self.best_time_intermediate:
                self.best_time_intermediate = session.time_seconds
            if session.score > self.best_score_intermediate:
                self.best_score_intermediate = session.score
                
        elif session.difficulty == 'hard':
            if not self.best_time_hard or session.time_seconds < self.best_time_hard:
                self.best_time_hard = session.time_seconds
            if session.score > self.best_score_hard:
                self.best_score_hard = session.score
        
        # Update average moves
        all_sessions = MemoryGameSession.objects.filter(user=self.user, completed=True)
        total_moves = sum(s.moves_count for s in all_sessions)
        self.average_moves_per_game = total_moves / self.total_games if self.total_games > 0 else 0
        
        # Update timestamps
        if not self.first_game_at:
            self.first_game_at = session.created_at
        self.last_game_at = session.created_at
        
        self.save()


class MemoryGameTournament(models.Model):
    """
    Hotel tournaments for memory game competitions
    """
    class TournamentStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='memory_tournaments'
    )
    
    # Tournament Details
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # Tournament Configuration
    # Fixed 3x4 grid (6 pairs) for all tournaments
    max_participants = models.PositiveIntegerField(
        default=50,
        help_text="Maximum number of participants"
    )
    
    # Age restrictions
    min_age = models.PositiveIntegerField(
        default=6,
        help_text="Minimum age for participation"
    )
    max_age = models.PositiveIntegerField(
        default=18,
        help_text="Maximum age for participation"
    )
    
    # Tournament Schedule
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(
        help_text="Last date for registration"
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=TournamentStatus.choices,
        default=TournamentStatus.UPCOMING
    )
    
    # QR Code for registration
    qr_code_url = models.URLField(blank=True, null=True)
    qr_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Prizes and Rules
    first_prize = models.CharField(max_length=200, blank=True)
    second_prize = models.CharField(max_length=200, blank=True)
    third_prize = models.CharField(max_length=200, blank=True)
    rules = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tournaments'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hotel', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} @ {self.hotel.name} ({self.status})"

    def generate_qr_code(self):
        """Generate QR code for direct tournament play"""
        if not self.slug or not self.hotel:
            return False
            
        hotel_slug = self.hotel.slug
        url = (f"https://hotelsmates.com/tournaments/"
               f"{hotel_slug}/{self.slug}/play/")
        
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"tournament_qr/{hotel_slug}_{self.slug}",
            overwrite=True
        )
        
        self.qr_code_url = upload_result['secure_url']
        self.qr_generated_at = timezone.now()
        self.save()
        return True

    @property
    def is_registration_open(self):
        """Check if registration is still open"""
        now = timezone.now()
        return (
            self.status == self.TournamentStatus.UPCOMING and
            now <= self.registration_deadline
        )

    @property
    def is_active(self):
        """Check if tournament is currently active"""
        now = timezone.now()
        return (
            self.status == self.TournamentStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )

    @property
    def participant_count(self):
        """Get current number of participants"""
        return self.participants.filter(status='registered').count()

    def get_leaderboard(self, limit=10):
        """Get tournament leaderboard"""
        return (self.sessions
                .filter(completed=True)
                .select_related('user')
                .order_by('-score', 'time_seconds')[:limit])


class TournamentParticipation(models.Model):
    """
    Track user participation in tournaments
    """
    class ParticipationStatus(models.TextChoices):
        REGISTERED = 'registered', 'Registered'
        PARTICIPATED = 'participated', 'Participated'
        DISQUALIFIED = 'disqualified', 'Disqualified'
        NO_SHOW = 'no_show', 'No Show'
    
    tournament = models.ForeignKey(
        MemoryGameTournament,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tournament_participations'
    )
    
    # Participant Info
    participant_name = models.CharField(
        max_length=100,
        help_text="Display name for tournament"
    )
    participant_age = models.PositiveIntegerField()
    
    # Registration
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=12,
        choices=ParticipationStatus.choices,
        default=ParticipationStatus.REGISTERED
    )
    
    # Results
    best_score = models.IntegerField(default=0)
    best_time = models.PositiveIntegerField(null=True, blank=True)
    final_rank = models.PositiveIntegerField(null=True, blank=True)
    
    # Participation details
    games_played = models.PositiveIntegerField(default=0)
    total_score = models.IntegerField(default=0)

    class Meta:
        unique_together = ('tournament', 'user')
        ordering = ['-best_score', 'best_time']

    def __str__(self):
        return f"{self.participant_name} in {self.tournament.name}"

    def update_from_session(self, session):
        """Update participation stats from a game session"""
        self.games_played += 1
        self.total_score += session.score
        
        if session.score > self.best_score:
            self.best_score = session.score
            self.best_time = session.time_seconds
        elif session.score == self.best_score and session.time_seconds < (self.best_time or float('inf')):
            self.best_time = session.time_seconds
        
        if self.status == self.ParticipationStatus.REGISTERED:
            self.status = self.ParticipationStatus.PARTICIPATED
            
        self.save()


class MemoryGameAchievement(models.Model):
    """
    Achievement system for memory game
    """
    class AchievementType(models.TextChoices):
        GAMES_PLAYED = 'games_played', 'Games Played'
        HIGH_SCORE = 'high_score', 'High Score'
        FAST_TIME = 'fast_time', 'Fast Time'
        TOURNAMENT = 'tournament', 'Tournament'
        STREAK = 'streak', 'Streak'
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(
        max_length=12,
        choices=AchievementType.choices
    )
    
    # Requirements
    required_value = models.IntegerField(
        help_text="Required value to unlock (games, score, time, etc.)"
    )
    difficulty = models.CharField(
        max_length=12,
        choices=MemoryGameDifficulty.choices,
        blank=True,
        help_text="Specific difficulty level (if applicable)"
    )
    
    # Visual
    icon_url = models.URLField(blank=True)
    badge_color = models.CharField(max_length=7, default='#FFD700')  # Gold
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """
    Track user achievements
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memory_game_achievements'
    )
    achievement = models.ForeignKey(
        MemoryGameAchievement,
        on_delete=models.CASCADE
    )
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    # Context
    session = models.ForeignKey(
        MemoryGameSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Session that triggered this achievement"
    )

    class Meta:
        unique_together = ('user', 'achievement')
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
