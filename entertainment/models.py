from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
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
    For anonymous players in kids tournaments
    """
    # Anonymous player data
    player_name = models.CharField(
        max_length=100,
        help_text="Anonymous player name with token (e.g., 'Alice|player_123')"
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
            models.Index(fields=['player_name', 'difficulty']),
            models.Index(fields=['hotel', 'created_at']),
            models.Index(fields=['tournament', 'score']),
        ]

    def __str__(self):
        # Extract clean player name from "PlayerName|token" format
        player = (self.player_name.split('|')[0] if self.player_name
                  else "Anonymous")
        return (f"{player} - {self.difficulty} - "
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
        """Generate QR code pointing to tournament page"""
        if not self.hotel:
            return False
            
        hotel_slug = self.hotel.slug
        # QR codes point directly to tournaments page
        base_url = "https://hotelsmates.com/games/memory-match/tournaments"
        url = f"{base_url}?hotel={hotel_slug}"
        
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

    def get_leaderboard(self, limit=None):
                """Get tournament leaderboard.

                By default this returns the full ordered set of completed sessions for
                the tournament. Callers may pass `limit` to cap results if desired.
                """
                qs = (self.sessions
                            .filter(completed=True)
                            .order_by('-score', 'time_seconds'))

                if limit:
                        return qs[:limit]
                return qs


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


# ============================================================================
# GUESSTICULATOR QUIZ GAME MODELS
# Clean implementation - no hotel tracking, session token based
# ============================================================================


class QuizCategory(models.Model):
    """
    Quiz categories for the slot machine system
    10 main categories, 5 randomly selected per quiz
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., 'History', 'Science', 'Sports')"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of the category"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icon/emoji for the category"
    )
    color = models.CharField(
        max_length=7,
        default='#4F46E5',
        help_text="Hex color code for UI"
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Whether this category is available for "
            "slot machine selection"
        )
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for display in admin/UI"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = "Quiz Categories"
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return f"{self.icon} {self.name}" if self.icon else self.name

    def clean(self):
        """Validate color is valid hex code"""
        if self.color and not self.color.startswith('#'):
            raise ValidationError({
                'color': 'Color must be a hex code starting with #'
            })
        if self.color and len(self.color) not in [4, 7]:
            raise ValidationError({
                'color': 'Color must be in format #RGB or #RRGGBB'
            })

    @classmethod
    def get_random_categories(cls, count=5):
        """
        Slot machine: randomly select categories for a quiz session
        Default is 5 from all active categories
        """
        import random
        active_categories = list(cls.objects.filter(is_active=True))
        
        if len(active_categories) < count:
            # If fewer than requested, return all
            return active_categories
        
        return random.sample(active_categories, count)

    @property
    def question_count(self):
        """Get total number of active questions in this category"""
        return self.questions.filter(is_active=True).count()


class QuizQuestion(models.Model):
    """
    Quiz questions linked to categories with difficulty levels
    """
    class DifficultyLevel(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    category = models.ForeignKey(
        QuizCategory,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="Category this question belongs to"
    )
    question_text = models.TextField(
        help_text="The question text"
    )
    difficulty = models.CharField(
        max_length=6,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        help_text="Question difficulty level"
    )
    
    # Multiple choice options
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    
    # Correct answer (A, B, C, or D)
    correct_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        help_text="The correct option (A, B, C, or D)"
    )
    
    # Optional explanation
    explanation = models.TextField(
        blank=True,
        help_text="Explanation of the correct answer"
    )
    
    # Points awarded
    points = models.PositiveIntegerField(
        default=10,
        help_text="Base points for this question"
    )
    
    # Active status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this question is available for quizzes"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_questions'
    )

    class Meta:
        ordering = ['category', 'difficulty', 'question_text']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['difficulty', 'is_active']),
        ]

    def __str__(self):
        return f"[{self.category.name}] {self.question_text[:50]}..."

    def clean(self):
        """Validate question has all required fields"""
        all_options = [
            self.option_a, self.option_b, self.option_c, self.option_d
        ]
        if not all(all_options):
            raise ValidationError(
                'All four options (A, B, C, D) must be provided'
            )
        if self.correct_answer not in ['A', 'B', 'C', 'D']:
            raise ValidationError({
                'correct_answer': 'Must be A, B, C, or D'
            })

    def get_difficulty_multiplier(self):
        """Get score multiplier based on difficulty"""
        multipliers = {
            self.DifficultyLevel.EASY: 1.0,
            self.DifficultyLevel.MEDIUM: 1.5,
            self.DifficultyLevel.HARD: 2.0,
        }
        return multipliers.get(self.difficulty, 1.0)

    @property
    def correct_option_text(self):
        """Get the text of the correct answer"""
        options = {
            'A': self.option_a,
            'B': self.option_b,
            'C': self.option_c,
            'D': self.option_d,
        }
        return options.get(self.correct_answer, '')


class QuizSession(models.Model):
    """
    Individual quiz session - tracks player, selected categories, score
    Supports both casual and tournament play
    """
    # Anonymous player data
    player_name = models.CharField(
        max_length=150,
        help_text=(
            "Player name with token: 'PlayerName|token' "
            "(e.g., 'Alice|player_abc123')"
        )
    )
    
    # Hotel (optional for multi-hotel support)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Hotel where quiz was played (optional)"
    )
    
    # Tournament link (null for casual play)
    tournament = models.ForeignKey(
        'QuizTournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        help_text="Tournament this session belongs to (null for casual play)"
    )
    
    # Slot machine: selected categories for this session
    selected_categories = models.JSONField(
        help_text=(
            "List of category IDs selected for this quiz "
            "(5 random from 10)"
        )
    )
    
    # Game results
    total_questions = models.PositiveIntegerField(
        default=0,
        help_text="Total number of questions in this quiz"
    )
    correct_answers = models.PositiveIntegerField(
        default=0,
        help_text="Number of correct answers"
    )
    score = models.IntegerField(
        default=0,
        help_text="Final calculated score"
    )
    time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total time taken in seconds"
    )
    
    # Session status
    completed = models.BooleanField(
        default=False,
        help_text="Whether the quiz was completed"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the quiz was completed"
    )
    
    # Session state (for resuming incomplete quizzes)
    current_question_index = models.PositiveIntegerField(
        default=0,
        help_text="Current question index (for resuming)"
    )
    session_state = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional state data for resuming quiz"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['player_name', 'completed']),
            models.Index(fields=['tournament', 'score']),
            models.Index(fields=['completed', '-score']),
        ]

    def __str__(self):
        player = self.get_player_display_name()
        return (
            f"{player} - {self.score} pts "
            f"({self.correct_answers}/{self.total_questions})"
        )

    def get_player_display_name(self):
        """Extract display name from 'PlayerName|token' format"""
        if '|' in self.player_name:
            return self.player_name.split('|')[0]
        return self.player_name

    def get_player_token(self):
        """Extract token from 'PlayerName|token' format"""
        if '|' in self.player_name:
            parts = self.player_name.split('|')
            return parts[1] if len(parts) > 1 else None
        return None

    def clean(self):
        """Validate session data"""
        if not self.player_name or '|' not in self.player_name:
            raise ValidationError({
                'player_name': 'Must be in format PlayerName|token'
            })
        if self.selected_categories:
            if not isinstance(self.selected_categories, list):
                raise ValidationError({
                    'selected_categories': 'Must be a list of category IDs'
                })

    def calculate_score(self):
        """
        Calculate final score based on answers
        This will be called after all answers are submitted
        """
        total_score = 0
        
        # Sum up points from all answers
        for answer in self.answers.all():
            if answer.is_correct:
                # Base points * difficulty multiplier
                question = answer.question
                points = question.points * question.get_difficulty_multiplier()
                
                # Optional: time bonus (if answer_time is tracked)
                if answer.time_seconds:
                    # Bonus for quick answers (e.g., under 10 seconds)
                    if answer.time_seconds < 10:
                        points *= 1.2
                    elif answer.time_seconds < 20:
                        points *= 1.1
                
                total_score += int(points)
        
        self.score = total_score
        return total_score

    def complete_session(self):
        """Mark session as complete and calculate final score"""
        self.completed = True
        self.completed_at = timezone.now()
        self.calculate_score()
        self.save()
        
        # Update leaderboard if not in tournament
        if not self.tournament:
            QuizLeaderboard.update_or_create_entry(self)

    @classmethod
    def get_questions_for_categories(
        cls, category_ids, questions_per_category=4
    ):
        """
        Fetch questions evenly from selected categories
        Default: 4 questions per category * 5 categories = 20 questions
        """
        import random
        all_questions = []
        
        for cat_id in category_ids:
            # Get all active questions for this category
            questions = list(
                QuizQuestion.objects.filter(
                    category_id=cat_id,
                    is_active=True
                )
            )
            
            # Randomly select questions
            if len(questions) >= questions_per_category:
                selected = random.sample(questions, questions_per_category)
            else:
                # If not enough questions, take all and shuffle
                selected = questions
                random.shuffle(selected)
            
            all_questions.extend(selected)
        
        # Shuffle all questions together
        random.shuffle(all_questions)
        return all_questions


class QuizAnswer(models.Model):
    """
    Player's answer to a specific question in a quiz session
    """
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='answers',
        help_text="Quiz session this answer belongs to"
    )
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='player_answers',
        help_text="Question being answered"
    )
    
    # Player's answer
    selected_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        help_text="Player's selected answer (A, B, C, or D)"
    )
    
    # Answer validation
    is_correct = models.BooleanField(
        default=False,
        help_text="Whether the answer is correct"
    )
    
    # Timing
    time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time taken to answer this question (seconds)"
    )
    
    # Metadata
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'answered_at']
        unique_together = ('session', 'question')
        indexes = [
            models.Index(fields=['session', 'is_correct']),
        ]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        player = self.session.get_player_display_name()
        return f"{status} {player} - Q{self.question.id}"

    def save(self, *args, **kwargs):
        """Auto-validate answer on save"""
        if not self.pk:  # Only on creation
            self.is_correct = (
                self.selected_answer == self.question.correct_answer
            )
        super().save(*args, **kwargs)


class QuizLeaderboard(models.Model):
    """
    General leaderboard - stores BEST score per player
    One entry per player (identified by token)
    """
    player_name = models.CharField(
        max_length=150,
        help_text="Player name with token: 'PlayerName|token'"
    )
    player_token = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique player token extracted from player_name"
    )
    
    # Best score data
    best_score = models.IntegerField(
        help_text="Player's best score across all casual play sessions"
    )
    best_session = models.ForeignKey(
        QuizSession,
        on_delete=models.SET_NULL,
        null=True,
        related_name='leaderboard_entries',
        help_text="Session where best score was achieved"
    )
    
    # Stats
    total_games_played = models.PositiveIntegerField(
        default=1,
        help_text="Total number of casual games played"
    )
    
    # Timestamps
    first_played_at = models.DateTimeField(auto_now_add=True)
    last_played_at = models.DateTimeField(auto_now=True)
    best_score_achieved_at = models.DateTimeField(
        help_text="When the best score was achieved"
    )

    class Meta:
        ordering = ['-best_score']
        indexes = [
            models.Index(fields=['-best_score']),
            models.Index(fields=['player_token']),
        ]

    def __str__(self):
        if '|' in self.player_name:
            player = self.player_name.split('|')[0]
        else:
            player = self.player_name
        return f"{player} - {self.best_score} pts"

    @classmethod
    def update_or_create_entry(cls, session):
        """
        Update leaderboard with new session
        Only updates if new score is better than existing
        """
        if session.tournament:
            # Tournament sessions don't affect general leaderboard
            return None
        
        player_token = session.get_player_token()
        if not player_token:
            return None
        
        try:
            entry = cls.objects.get(player_token=player_token)
            
            # Update total games played
            entry.total_games_played += 1
            entry.last_played_at = timezone.now()
            
            # Update best score if new score is higher
            if session.score > entry.best_score:
                entry.best_score = session.score
                entry.best_session = session
                # Update name in case it changed
                entry.player_name = session.player_name
                entry.best_score_achieved_at = (
                    session.completed_at or timezone.now()
                )
            
            entry.save()
            return entry
            
        except cls.DoesNotExist:
            # Create new leaderboard entry
            entry = cls.objects.create(
                player_name=session.player_name,
                player_token=player_token,
                best_score=session.score,
                best_session=session,
                total_games_played=1,
                best_score_achieved_at=session.completed_at or timezone.now()
            )
            return entry

    @classmethod
    def get_player_rank(cls, player_token):
        """Get player's current rank on leaderboard"""
        try:
            entry = cls.objects.get(player_token=player_token)
            better_scores = cls.objects.filter(
                best_score__gt=entry.best_score
            ).count()
            rank = better_scores + 1
            return rank
        except cls.DoesNotExist:
            return None


class QuizTournament(models.Model):
    """
    Quiz tournaments with active/completed status
    Tournament leaderboard shows ALL plays during active period
    """
    class TournamentStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    # Hotel (optional)
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quiz_tournaments',
        help_text="Hotel hosting this tournament (optional)"
    )
    
    # Tournament details
    name = models.CharField(
        max_length=200,
        help_text="Tournament name"
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="URL-friendly identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Tournament description and rules"
    )
    
    # Configuration
    max_participants = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of participants"
    )
    questions_per_quiz = models.PositiveIntegerField(
        default=20,
        help_text="Total questions per quiz session"
    )
    
    # Age restrictions
    min_age = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Minimum age for participation"
    )
    max_age = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum age for participation"
    )
    
    # Schedule
    start_date = models.DateTimeField(
        help_text="Tournament start date/time"
    )
    end_date = models.DateTimeField(
        help_text="Tournament end date/time"
    )
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last date for registration (optional)"
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=TournamentStatus.choices,
        default=TournamentStatus.UPCOMING
    )
    
    # QR Code
    qr_code_url = models.URLField(
        blank=True,
        null=True,
        help_text="QR code URL for tournament access"
    )
    qr_generated_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Prizes
    first_prize = models.CharField(
        max_length=200,
        blank=True,
        help_text="First place prize"
    )
    second_prize = models.CharField(
        max_length=200,
        blank=True,
        help_text="Second place prize"
    )
    third_prize = models.CharField(
        max_length=200,
        blank=True,
        help_text="Third place prize"
    )
    
    # Rules and info
    rules = models.TextField(
        blank=True,
        help_text="Tournament rules and regulations"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_quiz_tournaments'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['hotel', 'status']),
        ]

    def __str__(self):
        hotel_str = f" @ {self.hotel.name}" if self.hotel else ""
        return f"{self.name}{hotel_str} ({self.status})"

    def generate_qr_code(self):
        """Generate QR code for tournament access"""
        base_url = "https://hotelsmates.com/games/quiz/tournaments"
        url = f"{base_url}/{self.slug}"
        
        if self.hotel:
            url += f"?hotel={self.hotel.slug}"
        
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        hotel_prefix = self.hotel.slug if self.hotel else 'global'
        public_id = f"quiz_tournament_qr/{hotel_prefix}_{self.slug}"
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=public_id,
            overwrite=True
        )
        
        self.qr_code_url = upload_result['secure_url']
        self.qr_generated_at = timezone.now()
        self.save()
        return True

    @property
    def is_registration_open(self):
        """Check if registration is open"""
        now = timezone.now()
        if self.registration_deadline:
            return (
                self.status == self.TournamentStatus.UPCOMING and
                now <= self.registration_deadline
            )
        return self.status == self.TournamentStatus.UPCOMING

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
        """Get total number of unique participants"""
        # Count unique player tokens
        unique_tokens = set()
        for session in self.sessions.all():
            token = session.get_player_token()
            if token:
                unique_tokens.add(token)
        return len(unique_tokens)

    def get_leaderboard(self, limit=None):
        """
        Get tournament leaderboard - ALL plays during tournament
        Ordered by score (desc), then time (asc)
        """
        qs = (
            self.sessions
            .filter(completed=True)
            .order_by('-score', 'time_seconds')
        )
        
        if limit:
            return qs[:limit]
        return qs

    def get_top_players(self, limit=3):
        """Get top N players with their best scores"""
        leaderboard = self.get_leaderboard()
        
        # Group by player token and get best score
        player_scores = {}
        for session in leaderboard:
            token = session.get_player_token()
            if token:
                is_new_or_better = (
                    token not in player_scores or
                    session.score > player_scores[token]['score']
                )
                if is_new_or_better:
                    player_scores[token] = {
                        'session': session,
                        'score': session.score,
                        'name': session.get_player_display_name()
                    }
        
        # Sort by score and return top N
        sorted_players = sorted(
            player_scores.values(),
            key=lambda x: (-x['score'], x['session'].time_seconds or 999999)
        )
        
        return sorted_players[:limit]
