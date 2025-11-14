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
    Quiz categories (formerly individual quizzes)
    - classic-trivia
    - odd-one-out
    - fill-the-blank
    - dynamic-math (generates questions dynamically)
    - knowledge-trap
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, default='temp-slug')
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in game (categories played in order)"
    )
    is_math_category = models.BooleanField(
        default=False,
        help_text="True for dynamic math category (generates questions)"
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Quiz Categories"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def question_count(self):
        """Get number of active questions in this category"""
        if self.is_math_category:
            return "Dynamic"
        return self.questions.filter(is_active=True).count()


class Quiz(models.Model):
    """
    The ONE quiz: Guessticulator The Quizculator
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Configuration
    questions_per_category = models.PositiveIntegerField(
        default=10,
        help_text="How many questions from each category (default: 10)"
    )
    time_per_question_seconds = models.PositiveIntegerField(
        default=5,
        help_text="Time limit per question in seconds"
    )
    
    # Turbo Mode Settings
    turbo_mode_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Consecutive correct answers needed for turbo mode"
    )
    turbo_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.0,
        help_text="Score multiplier in turbo mode (default: 2x)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # QR Code
    qr_code_url = models.URLField(blank=True, null=True)
    qr_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Quizzes"
        ordering = ['title']

    def __str__(self):
        return self.title
    
    def generate_qr_code(self):
        """Generate QR code pointing to quiz game"""
        url = "https://hotelsmates.com/games/quiz"
        
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"quiz_qr/{self.slug}",
            overwrite=True
        )
        
        self.qr_code_url = upload_result['secure_url']
        self.qr_generated_at = timezone.now()
        self.save()
        return True


class QuizQuestion(models.Model):
    """
    Questions linked to categories
    NOT used for math category (dynamic generation)
    """
    category = models.ForeignKey(
        QuizCategory,
        on_delete=models.CASCADE,
        related_name='questions',
        default=1
    )
    text = models.TextField(help_text="Question text")
    image_url = CloudinaryField(
        'quiz_question_image',
        blank=True,
        null=True,
        folder="quiz_questions/",
        help_text="Optional image for question"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'id']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.text[:50]}"
    
    def clean(self):
        """Validate that math categories don't have manual questions"""
        if self.category and self.category.is_math_category:
            raise ValidationError(
                "Cannot add questions to math category. "
                "Math questions are generated dynamically."
            )
    
    @property
    def correct_answer(self):
        """Get the correct answer"""
        return self.answers.filter(is_correct=True).first()


class QuizAnswer(models.Model):
    """
    Answer options (4 per question, 1 correct)
    """
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.text[:50]}"
    
    def clean(self):
        """Ensure only one correct answer per question"""
        if self.is_correct:
            existing = QuizAnswer.objects.filter(
                question=self.question,
                is_correct=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    "Question can only have ONE correct answer"
                )


class QuizSession(models.Model):
    """
    Game session - identified by session token
    No hotel/room tracking - fully anonymous
    """
    # Session identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_token = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique session token to identify player across games"
    )
    
    # Quiz reference
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Player info
    player_name = models.CharField(
        max_length=100,
        help_text="Player's display name"
    )
    
    # Game mode
    is_tournament_mode = models.BooleanField(
        default=False,
        help_text="Tournament mode vs Casual mode"
    )
    tournament = models.ForeignKey(
        'QuizTournament',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        help_text="Tournament reference if in tournament mode"
    )
    
    # Session state
    score = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    
    # Turbo mode tracking
    consecutive_correct = models.PositiveIntegerField(
        default=0,
        help_text="Consecutive correct answers"
    )
    is_turbo_active = models.BooleanField(
        default=False,
        help_text="Whether turbo mode is currently active"
    )
    
    # Current progress
    current_category_index = models.PositiveIntegerField(
        default=0,
        help_text="Which category player is on (0-4)"
    )
    current_question_index = models.PositiveIntegerField(
        default=0,
        help_text="Which question within category (0-9)"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['quiz', '-score']),
            models.Index(fields=['is_completed', '-started_at']),
            models.Index(fields=['tournament', '-score']),
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "▶"
        mode = "🏆" if self.is_tournament_mode else "🎮"
        return f"{status} {mode} {self.player_name} - {self.score} pts"
    
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
        """Formatted duration"""
        if not self.time_spent_seconds:
            return "0s"
        minutes = self.time_spent_seconds // 60
        seconds = self.time_spent_seconds % 60
        return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"


class QuizSubmission(models.Model):
    """
    Individual answer submission
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Session reference
    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    # Category and question reference
    category = models.ForeignKey(
        QuizCategory,
        on_delete=models.CASCADE,
        related_name='submissions',
        default=1
    )
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions',
        help_text="Null for math questions"
    )
    
    # Question data (for math or reference)
    question_text = models.TextField(default='Question')
    question_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Math question data: operands, operator, correct_answer"
    )
    
    # Answer data
    selected_answer = models.CharField(max_length=500, default='Answer')
    selected_answer_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="QuizAnswer ID (null for math)"
    )
    correct_answer = models.CharField(
        max_length=500,
        default='Answer',
        help_text="The correct answer (for comparison)"
    )
    
    # Result
    is_correct = models.BooleanField(default=False)
    time_taken_seconds = models.PositiveIntegerField(default=0)
    was_turbo_active = models.BooleanField(
        default=False,
        help_text="Was turbo mode active for this answer?"
    )
    points_awarded = models.IntegerField(default=0)
    
    # Timestamp
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['session', 'answered_at']
        indexes = [
            models.Index(fields=['session', 'answered_at']),
            models.Index(fields=['category', 'is_correct']),
        ]

    def __str__(self):
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.session.player_name} - {self.points_awarded} pts"
    
    def calculate_points(self):
        """
        Calculate points:
        Normal: 5-4-3-2-1-0 (based on seconds 1-5, timeout=0)
        Turbo:  10-8-6-4-2-0 (doubled)
        """
        if not self.is_correct:
            return 0
        
        # Base points calculation
        if self.time_taken_seconds == 0:
            base_points = 5
        elif self.time_taken_seconds >= 5:
            base_points = 0
        else:
            base_points = 5 - (self.time_taken_seconds - 1)
        
        # Apply turbo multiplier
        if self.was_turbo_active:
            return base_points * 2
        else:
            return base_points


class QuizPlayerProgress(models.Model):
    """
    Track which questions each player has seen
    Ensures no repeats until all questions exhausted
    """
    session_token = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Player's unique session token"
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='player_progress'
    )
    
    # Track seen question IDs per category
    seen_question_ids = models.JSONField(
        default=dict,
        help_text="Dict of category_slug: [question_ids] player has seen"
    )
    
    # Track generated math questions (store the actual questions)
    seen_math_questions = models.JSONField(
        default=list,
        help_text="List of math questions player has seen"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['session_token', 'quiz']
        indexes = [
            models.Index(fields=['session_token', 'quiz']),
        ]
    
    def __str__(self):
        return f"{self.session_token} - Quiz Progress"
    
    def get_unseen_questions(self, category, count=10):
        """Get questions this player hasn't seen yet"""
        category_slug = category.slug
        seen_ids = self.seen_question_ids.get(category_slug, [])
        
        # Get all question IDs for this category
        all_questions = QuizQuestion.objects.filter(
            category=category,
            is_active=True
        ).values_list('id', flat=True)
        
        # Get unseen questions
        unseen_ids = [qid for qid in all_questions if qid not in seen_ids]
        
        # If we've seen all questions, reset for this category
        if len(unseen_ids) < count:
            self.seen_question_ids[category_slug] = []
            self.save()
            unseen_ids = list(all_questions)
        
        return unseen_ids[:count]
    
    def mark_questions_seen(self, category_slug, question_ids):
        """Mark questions as seen by this player"""
        if category_slug not in self.seen_question_ids:
            self.seen_question_ids[category_slug] = []
        
        self.seen_question_ids[category_slug].extend(question_ids)
        self.save()
    
    def get_unseen_math_questions_pool(self, total_pool=100):
        """Get count of unseen math questions from pool of 100"""
        seen_count = len(self.seen_math_questions)
        
        # Reset if we've seen all 100
        if seen_count >= total_pool:
            self.seen_math_questions = []
            self.save()
            return total_pool
        
        return total_pool - seen_count
    
    def mark_math_questions_seen(self, math_questions):
        """Mark math questions as seen"""
        self.seen_math_questions.extend(math_questions)
        self.save()


class QuizLeaderboard(models.Model):
    """
    All-time leaderboard - best score per player (session_token)
    Includes both casual and tournament plays
    """
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        default=1
    )
    session_token = models.CharField(max_length=255)
    player_name = models.CharField(max_length=100)
    best_score = models.IntegerField()
    best_session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        null=True
    )
    games_played = models.PositiveIntegerField(default=1)
    last_played = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-best_score', 'last_played']
        unique_together = ['quiz', 'session_token']
        indexes = [
            models.Index(fields=['quiz', '-best_score']),
            models.Index(fields=['session_token']),
        ]

    def __str__(self):
        return f"{self.player_name} - {self.best_score} pts"


class QuizTournament(models.Model):
    """
    24-hour tournaments
    """
    class TournamentStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='tournaments'
    )
    
    # 24-hour duration
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(
        help_text="Automatically set to 24 hours after start"
    )
    
    status = models.CharField(
        max_length=10,
        choices=TournamentStatus.choices,
        default=TournamentStatus.UPCOMING
    )
    
    # Prizes
    first_prize = models.CharField(max_length=200, blank=True)
    second_prize = models.CharField(max_length=200, blank=True)
    third_prize = models.CharField(max_length=200, blank=True)
    
    # QR Code
    qr_code_url = models.URLField(blank=True, null=True)
    qr_generated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Auto-set end_date to 24 hours after start"""
        if self.start_date and not self.end_date:
            from datetime import timedelta
            self.end_date = self.start_date + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        """Generate QR code for tournament"""
        url = f"https://hotelsmates.com/games/quiz?tournament={self.slug}"
        
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"quiz_tournament_qr/{self.slug}",
            overwrite=True
        )
        
        self.qr_code_url = upload_result['secure_url']
        self.qr_generated_at = timezone.now()
        self.save()
        return True
    
    @property
    def is_active(self):
        """Check if tournament is currently active"""
        now = timezone.now()
        return (
            self.status == self.TournamentStatus.ACTIVE and
            self.start_date <= now <= self.end_date
        )
    
    def get_leaderboard(self, limit=10):
        """
        Get tournament leaderboard - best score per player
        Only sessions from this tournament during its timeframe
        """
        from django.db.models import Max
        
        # Get best score for each session_token
        best_scores = (
            QuizSession.objects
            .filter(
                tournament=self,
                is_tournament_mode=True,
                is_completed=True,
                started_at__gte=self.start_date,
                started_at__lte=self.end_date
            )
            .values('session_token')
            .annotate(best_score=Max('score'))
            .order_by('-best_score')[:limit]
        )
        
        # Get the actual session objects
        result = []
        for entry in best_scores:
            session = (
                QuizSession.objects
                .filter(
                    tournament=self,
                    session_token=entry['session_token'],
                    score=entry['best_score']
                )
                .order_by('time_spent_seconds')
                .first()
            )
            if session:
                result.append(session)
        
        return result


class TournamentLeaderboard(models.Model):
    """
    Tournament-specific leaderboard entry
    Tracks best score per player in each tournament
    """
    tournament = models.ForeignKey(
        QuizTournament,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        default=1
    )
    session_token = models.CharField(max_length=255)
    player_name = models.CharField(max_length=100)
    best_score = models.IntegerField()
    best_session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-best_score', 'updated_at']
        unique_together = ['tournament', 'session_token']
        indexes = [
            models.Index(fields=['tournament', '-best_score']),
        ]

    def __str__(self):
        return f"{self.player_name} - {self.best_score} pts ({self.tournament.name})"
