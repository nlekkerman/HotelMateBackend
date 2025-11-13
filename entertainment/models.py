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


# QUIZ GAME MODELS

class QuizCategory(models.Model):
    """
    GLOBAL quiz categories (not tied to any hotel)
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Quiz Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]

    def __str__(self):
        return self.name


class Quiz(models.Model):
    """
    GLOBAL quiz configuration
    Each quiz has a difficulty level (1-5) with specific characteristics
    """
    class DifficultyLevel(models.IntegerChoices):
        CLASSIC_TRIVIA = 1, 'Classic Trivia (Easy)'
        ODD_ONE_OUT = 2, 'Odd One Out (Moderate)'
        FILL_THE_BLANK = 3, 'Fill the Blank (Challenging)'
        DYNAMIC_MATH = 4, 'Dynamic Math (Mid-Hard)'
        KNOWLEDGE_TRAP = 5, 'Knowledge Trap (Hard)'

    class SoundTheme(models.TextChoices):
        DEFAULT = 'default', 'Default'
        TENSE = 'tense', 'Tense'
        CHILL = 'chill', 'Chill'

    # Basic Info
    category = models.ForeignKey(
        QuizCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quizzes'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Difficulty
    difficulty_level = models.IntegerField(
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.CLASSIC_TRIVIA,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_daily = models.BooleanField(
        default=False,
        help_text="Mark as daily quiz (featured)"
    )
    
    # Configuration
    max_questions = models.PositiveIntegerField(
        default=10,
        help_text="Maximum number of questions in this quiz"
    )
    
    # Timing Configuration (optional overrides, defaults based on difficulty)
    time_per_question_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Time per question (default based on difficulty: "
            "L1=20, L2=18, L3=15, L4=12, L5=10)"
        )
    )
    total_time_limit_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional total time limit for entire quiz"
    )
    
    # Audio Configuration
    enable_background_music = models.BooleanField(default=True)
    enable_sound_effects = models.BooleanField(default=True)
    sound_theme = models.CharField(
        max_length=10,
        choices=SoundTheme.choices,
        default=SoundTheme.DEFAULT
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['difficulty_level', 'title']
        indexes = [
            models.Index(fields=['is_active', 'difficulty_level']),
            models.Index(fields=['is_daily', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.title} (Level {self.difficulty_level})"

    @property
    def is_math_quiz(self):
        """Check if this is a dynamic math quiz (Level 4)"""
        return self.difficulty_level == self.DifficultyLevel.DYNAMIC_MATH

    def get_time_per_question(self):
        """Get time per question with defaults based on difficulty"""
        if self.time_per_question_seconds:
            return self.time_per_question_seconds
        
        # Default times based on difficulty level (all 5 seconds for fast-paced turbo mode)
        defaults = {
            1: 5,  # Classic Trivia
            2: 5,  # Odd One Out
            3: 5,  # Fill the Blank
            4: 5,  # Dynamic Math
            5: 5,  # Knowledge Trap
        }
        return defaults.get(self.difficulty_level, 5)

    @property
    def question_count(self):
        """Get actual number of questions (excluding math which is dynamic)"""
        if self.is_math_quiz:
            return self.max_questions
        return self.questions.filter(is_active=True).count()


class QuizQuestion(models.Model):
    """
    GLOBAL quiz questions (NOT used for Level 4 - Dynamic Math)
    All questions use 4-option multiple choice format
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField(help_text="Question text")
    image_url = CloudinaryField(
        'quiz_question_image',
        blank=True,
        null=True,
        folder="quiz_questions/",
        help_text="Optional image for question"
    )
    
    # Ordering
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    
    # Scoring
    base_points = models.PositiveIntegerField(
        default=10,
        help_text="Base points for correct answer (reduced by time taken)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['quiz', 'order', 'id']
        indexes = [
            models.Index(fields=['quiz', 'is_active', 'order']),
        ]
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.text[:50]}"

    def clean(self):
        """Validate that math quizzes don't have questions"""
        if self.quiz and self.quiz.is_math_quiz:
            raise ValidationError(
                "Cannot add questions to Dynamic Math quizzes (Level 4). "
                "Math questions are generated at runtime."
            )

    @property
    def correct_answer(self):
        """Get the correct answer for this question"""
        return self.answers.filter(is_correct=True).first()


class QuizAnswer(models.Model):
    """
    GLOBAL quiz answers (NOT used for Level 4 - Dynamic Math)
    Each question must have exactly 4 answers (1 correct, 3 incorrect)
    """
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(
        default=False,
        help_text="Mark as the correct answer"
    )
    
    # Ordering (for display)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in answer list"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        correct = "✓" if self.is_correct else "✗"
        return f"{correct} {self.text[:50]}"

    def clean(self):
        """Validate answer constraints"""
        # Ensure only one correct answer per question
        if self.is_correct:
            existing_correct = QuizAnswer.objects.filter(
                question=self.question,
                is_correct=True
            ).exclude(pk=self.pk)
            
            if existing_correct.exists():
                raise ValidationError(
                    "Each question can have only ONE correct answer"
                )


class QuizSession(models.Model):
    """
    HOTEL-SCOPED quiz session (started via QR code)
    Tracks player progress through a quiz
    """
    # Unique session identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Hotel context (from QR code)
    hotel_identifier = models.CharField(
        max_length=100,
        help_text="Hotel identifier from QR code (hotel slug)"
    )
    
    # Quiz reference
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Player info (anonymous)
    player_name = models.CharField(
        max_length=100,
        help_text="Player's display name"
    )
    room_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Room number for tournament submissions (required for leaderboard)"
    )
    external_player_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Optional external player identifier (e.g., device ID)"
    )
    
    # Game mode
    is_practice_mode = models.BooleanField(
        default=False,
        help_text="If True, score won't appear on tournament leaderboard"
    )
    
    # Session state
    score = models.IntegerField(
        default=0,
        help_text="Total accumulated score"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Total time spent on quiz"
    )
    
    # Current question tracking
    current_question_index = models.PositiveIntegerField(
        default=0,
        help_text="Index of current question (0-based)"
    )
    
    # Turbo Mode fields
    consecutive_correct = models.PositiveIntegerField(
        default=0,
        help_text="Consecutive correct answers for turbo mode multiplier"
    )
    current_multiplier = models.PositiveIntegerField(
        default=1,
        help_text="Current score multiplier (doubles with each correct answer: 1x, 2x, 4x, 8x...)"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['hotel_identifier', 'quiz', '-started_at']),
            models.Index(fields=['quiz', '-score']),
            models.Index(fields=['is_completed', '-started_at']),
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "..."
        return f"{status} {self.player_name} - {self.quiz.title} ({self.score} pts)"

    def complete_session(self):
        """Mark session as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.finished_at = timezone.now()
            if self.started_at:
                delta = self.finished_at - self.started_at
                self.time_spent_seconds = int(delta.total_seconds())
            self.save()

    @property
    def duration_formatted(self):
        """Get formatted duration string"""
        if not self.time_spent_seconds:
            return "0s"
        minutes = self.time_spent_seconds // 60
        seconds = self.time_spent_seconds % 60
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"


class QuizSubmission(models.Model):
    """
    HOTEL-SCOPED answer submission
    Used for ALL difficulties including dynamic math (Level 4)
    """
    # Submission identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Hotel context
    hotel_identifier = models.CharField(
        max_length=100,
        help_text="Hotel identifier from QR code"
    )
    
    # Session reference
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    # Question reference (nullable for math)
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="Null for dynamic math questions"
    )
    
    # Dynamic question data (required for math)
    question_text = models.TextField(
        blank=True,
        help_text="Question text (for math or reference)"
    )
    question_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Additional question data (e.g., math operands, correct answer)"
    )
    
    # Answer data
    selected_answer = models.CharField(
        max_length=500,
        help_text="Text of selected answer"
    )
    selected_answer_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of selected QuizAnswer (null for math)"
    )
    
    # Result
    is_correct = models.BooleanField(default=False)
    base_points = models.PositiveIntegerField(
        default=10,
        help_text="Base points for this question"
    )
    points_awarded = models.IntegerField(
        default=0,
        help_text="Actual points awarded (base minus time penalty)"
    )
    time_taken_seconds = models.PositiveIntegerField(
        default=0,
        help_text="Time taken to answer (seconds)"
    )
    multiplier_used = models.PositiveIntegerField(
        default=1,
        help_text="Multiplier that was active when this answer was submitted"
    )
    
    # Timestamp
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'answered_at']
        indexes = [
            models.Index(fields=['session', 'answered_at']),
            models.Index(fields=['hotel_identifier', '-points_awarded']),
            models.Index(fields=['is_correct']),
        ]

    def __str__(self):
        result = "✓" if self.is_correct else "✗"
        q_ref = self.question_text[:30] if self.question_text else "Question"
        return f"{result} {self.session.player_name} - {q_ref} ({self.points_awarded} pts)"

    @property
    def quiz_id(self):
        """Get quiz ID from session"""
        return self.session.quiz_id if self.session else None

    def calculate_points(self):
        """
        Turbo Mode Scoring:
        - Base: 5 points max per question
        - Deduct 1 point per second (5 second timer)
        - Correct streak: multiplier doubles (1x, 2x, 4x, 8x, 16x...)
        - Wrong answer: reset multiplier to 1x
        """
        if not self.is_correct:
            return 0
        
        # Base calculation: 5 - seconds taken (minimum 0, max 5)
        base_points = max(0, min(5, 5 - self.time_taken_seconds))
        
        # Apply multiplier from session
        points = base_points * self.multiplier_used
        
        return points

    def save(self, *args, **kwargs):
        """Auto-calculate points on save with turbo mode logic"""
        session = self.session
        
        # Set multiplier for this submission based on current session state
        # Check if this is a new submission (no id in db yet)
        is_new = self._state.adding
        if is_new:
            self.multiplier_used = session.current_multiplier
        
        # Calculate points
        self.points_awarded = self.calculate_points()
        
        # Save submission first
        super().save(*args, **kwargs)
        
        # Update session state
        if self.is_correct and self.points_awarded > 0:
            # Increase consecutive correct count (only if earned points)
            session.consecutive_correct += 1
            # Double multiplier for next question (cap at 128x)
            session.current_multiplier = min(session.current_multiplier * 2, 128)
        else:
            # Reset turbo mode on wrong answer OR timeout (0 points)
            session.consecutive_correct = 0
            session.current_multiplier = 1
        
        # Update session score (sum of all points)
        session.score = session.submissions.aggregate(
            total=models.Sum('points_awarded')
        )['total'] or 0
        
        session.save()
