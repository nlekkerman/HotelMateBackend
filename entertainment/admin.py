from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Game, GameHighScore, GameQRCode,
    MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament,
    TournamentParticipation, MemoryGameAchievement, UserAchievement,
    QuizCategory, Quiz, QuizQuestion, QuizAnswer, QuizSession, QuizSubmission
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {"slug": ("title",)}  # auto-fill slug from title


@admin.register(GameHighScore)
class GameHighScoreAdmin(admin.ModelAdmin):
    list_display = ('display_player', 'game', 'score', 'hotel', 'achieved_at')
    list_filter = ('game', 'hotel', 'achieved_at')
    search_fields = ('player_name', 'user__username', 'game__title')
    ordering = ('-score',)

    def display_player(self, obj):
        return obj.player_name or (obj.user.username if obj.user else "Anonymous")
    display_player.short_description = 'Player'


@admin.register(GameQRCode)
class GameQRCodeAdmin(admin.ModelAdmin):
    list_display = ('game', 'hotel', 'qr_url', 'generated_at')
    list_filter = ('game', 'hotel', 'generated_at')
    search_fields = ('game__title', 'hotel__slug', 'qr_url')


@admin.register(MemoryGameCard)
class MemoryGameCardAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'image_preview', 'is_active', 
        'difficulty_levels', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Card Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Image', {
            'fields': ('image', 'image_preview')
        }),
        ('Game Settings', {
            'fields': ('is_active', 'difficulty_levels')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def image_preview(self, obj):
        """Show image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="height:80px; width:80px; object-fit:contain;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"


# MEMORY MATCH GAME ADMIN

@admin.register(MemoryGameSession)
class MemoryGameSessionAdmin(admin.ModelAdmin):
    list_display = (
        'display_player', 'room_number', 'difficulty', 'score', 'time_seconds', 
        'moves_count', 'hotel', 'tournament', 'completed', 'created_at'
    )
    list_filter = (
        'difficulty', 'completed', 'hotel', 'tournament', 'is_anonymous', 'created_at'
    )
    search_fields = ('player_name', 'room_number', 'hotel__name', 'tournament__name')
    readonly_fields = ('score', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def display_player(self, obj):
        """Display player name properly for anonymous players"""
        if obj.player_name:
            # Extract clean name from "name|token" format
            clean_name = (obj.player_name.split('|')[0]
                          if '|' in obj.player_name else obj.player_name)
            room_info = (f" (Room: {obj.room_number})"
                         if obj.room_number else "")
            return f"{clean_name}{room_info}"
        else:
            return "Unknown Player"
    display_player.short_description = 'Player'
    
    fieldsets = (
        ('Player Info', {
            'fields': ('player_name', 'room_number', 'is_anonymous')
        }),
        ('Game Info', {
            'fields': ('hotel', 'tournament', 'difficulty')
        }),
        ('Results', {
            'fields': ('time_seconds', 'moves_count', 'score', 'completed')
        }),
        ('Game Content', {
            'fields': ('cards_used',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'game_state'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MemoryGameStats)
class MemoryGameStatsAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'hotel', 'total_games', 'total_score',
        'best_score_easy', 'best_score_intermediate', 'best_score_hard'
    )
    list_filter = ('hotel', 'first_game_at', 'last_game_at')
    search_fields = ('user__username', 'hotel__name')
    readonly_fields = (
        'total_games', 'games_won', 'total_score', 'total_time_played',
        'average_moves_per_game', 'first_game_at', 'last_game_at', 'updated_at'
    )
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'hotel')
        }),
        ('Game Statistics', {
            'fields': (
                'total_games', 'games_won', 'total_score', 
                'total_time_played', 'average_moves_per_game'
            )
        }),
        ('Best Times', {
            'fields': (
                'best_time_easy', 'best_time_intermediate', 'best_time_hard'
            )
        }),
        ('Best Scores', {
            'fields': (
                'best_score_easy', 'best_score_intermediate', 'best_score_hard'
            )
        }),
        ('Timestamps', {
            'fields': ('first_game_at', 'last_game_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MemoryGameTournament)
class MemoryGameTournamentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'hotel', 'grid_size_display', 'status', 'participant_count',
        'start_date', 'end_date', 'created_by'
    )
    list_filter = (
        'status', 'hotel', 'start_date', 'created_at'
    )
    search_fields = ('name', 'slug', 'hotel__name', 'created_by__username')
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        'qr_code_url', 'qr_generated_at', 'created_at', 
        'updated_at', 'participant_count', 'grid_size_display'
    )
    
    def grid_size_display(self, obj):
        """Display fixed grid size"""
        return "3x4 (6 pairs)"
    grid_size_display.short_description = "Grid Size"
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'hotel', 'created_by')
        }),
        ('Tournament Settings', {
            'fields': (
                'grid_size_display', 'max_participants', 'min_age', 'max_age'
            )
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Status & QR Code', {
            'fields': ('status', 'qr_code_url', 'qr_generated_at')
        }),
        ('Prizes & Rules', {
            'fields': ('first_prize', 'second_prize', 'third_prize', 'rules'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_qr_codes', 'start_tournaments', 'end_tournaments']
    
    def generate_qr_codes(self, request, queryset):
        """Generate QR codes for selected tournaments"""
        count = 0
        for tournament in queryset:
            if tournament.generate_qr_code():
                count += 1
        self.message_user(
            request, 
            f'Successfully generated QR codes for {count} tournaments.'
        )
    generate_qr_codes.short_description = "Generate QR codes"
    
    def start_tournaments(self, request, queryset):
        """Start selected tournaments"""
        count = queryset.filter(status='upcoming').update(status='active')
        self.message_user(
            request, 
            f'Successfully started {count} tournaments.'
        )
    start_tournaments.short_description = "Start tournaments"
    
    def end_tournaments(self, request, queryset):
        """End selected tournaments"""
        count = queryset.filter(status='active').update(status='completed')
        self.message_user(
            request, 
            f'Successfully ended {count} tournaments.'
        )
    end_tournaments.short_description = "End tournaments"


class TournamentParticipationInline(admin.TabularInline):
    model = TournamentParticipation
    extra = 0
    readonly_fields = (
        'registered_at', 'best_score', 'best_time', 
        'games_played', 'total_score'
    )


@admin.register(TournamentParticipation)
class TournamentParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'participant_name', 'tournament', 'status', 'best_score',
        'best_time', 'final_rank', 'registered_at'
    )
    list_filter = (
        'status', 'tournament__hotel', 'registered_at'
    )
    search_fields = (
        'participant_name', 'user__username', 'tournament__name'
    )
    readonly_fields = (
        'registered_at', 'best_score', 'best_time', 
        'games_played', 'total_score'
    )
    
    fieldsets = (
        ('Participant Info', {
            'fields': ('tournament', 'user', 'participant_name', 'participant_age')
        }),
        ('Status', {
            'fields': ('status', 'registered_at')
        }),
        ('Performance', {
            'fields': (
                'best_score', 'best_time', 'final_rank', 
                'games_played', 'total_score'
            )
        }),
    )


@admin.register(MemoryGameAchievement)
class MemoryGameAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'achievement_type', 'required_value', 
        'difficulty', 'is_active'
    )
    list_filter = ('achievement_type', 'difficulty', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Requirements', {
            'fields': ('achievement_type', 'required_value', 'difficulty')
        }),
        ('Visual', {
            'fields': ('icon_url', 'badge_color')
        }),
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'achievement', 'unlocked_at', 'session'
    )
    list_filter = (
        'achievement__achievement_type', 'achievement__difficulty', 
        'unlocked_at'
    )
    search_fields = (
        'user__username', 'achievement__name'
    )
    readonly_fields = ('unlocked_at',)


# Add inlines to existing admins
MemoryGameTournamentAdmin.inlines = [TournamentParticipationInline]


# QUIZ GAME ADMIN

@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    """Admin for quiz categories"""
    list_display = ('name', 'is_active', 'quiz_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'quiz_count')

    fieldsets = (
        ('Category Info', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('quiz_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def quiz_count(self, obj):
        """Count of active quizzes in this category"""
        return obj.quizzes.filter(is_active=True).count()
    quiz_count.short_description = "Active Quizzes"


class QuizQuestionInline(admin.TabularInline):
    """Inline for quiz questions"""
    model = QuizQuestion
    extra = 0
    fields = ('text', 'order', 'base_points', 'is_active')
    ordering = ('order',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin for quizzes"""
    list_display = (
        'title', 'difficulty_level', 'difficulty_display', 'category',
        'is_daily', 'is_active', 'question_count', 'created_at'
    )
    list_filter = (
        'difficulty_level', 'is_active', 'is_daily',
        'category', 'created_at'
    )
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (
        'created_at', 'updated_at', 'question_count', 'is_math_quiz'
    )
    inlines = [QuizQuestionInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('category', 'title', 'slug', 'description')
        }),
        ('Difficulty', {
            'fields': (
                'difficulty_level', 'is_math_quiz', 'max_questions'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'is_daily')
        }),
        ('Timing Configuration', {
            'fields': (
                'time_per_question_seconds', 'total_time_limit_seconds'
            ),
            'description': (
                'Leave blank to use defaults based on difficulty level'
            )
        }),
        ('Audio Settings', {
            'fields': (
                'enable_background_music', 'enable_sound_effects',
                'sound_theme'
            )
        }),
        ('Metadata', {
            'fields': ('question_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def difficulty_display(self, obj):
        """Display difficulty name"""
        return obj.get_difficulty_level_display()
    difficulty_display.short_description = "Difficulty"

    actions = ['mark_as_daily', 'unmark_as_daily', 'activate', 'deactivate']

    def mark_as_daily(self, request, queryset):
        """Mark selected quizzes as daily"""
        count = queryset.update(is_daily=True)
        self.message_user(request, f'{count} quizzes marked as daily.')
    mark_as_daily.short_description = "Mark as daily quiz"

    def unmark_as_daily(self, request, queryset):
        """Unmark selected quizzes as daily"""
        count = queryset.update(is_daily=False)
        self.message_user(request, f'{count} quizzes unmarked as daily.')
    unmark_as_daily.short_description = "Remove daily quiz status"

    def activate(self, request, queryset):
        """Activate selected quizzes"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} quizzes activated.')
    activate.short_description = "Activate quizzes"

    def deactivate(self, request, queryset):
        """Deactivate selected quizzes"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} quizzes deactivated.')
    deactivate.short_description = "Deactivate quizzes"


class QuizAnswerInline(admin.TabularInline):
    """Inline for quiz answers"""
    model = QuizAnswer
    extra = 4
    max_num = 4
    fields = ('text', 'is_correct', 'order')
    ordering = ('order',)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """Admin for quiz questions"""
    list_display = (
        'quiz', 'text_preview', 'order', 'base_points',
        'answer_count', 'is_active'
    )
    list_filter = ('quiz__difficulty_level', 'is_active', 'quiz')
    search_fields = ('text', 'quiz__title')
    readonly_fields = ('created_at', 'updated_at', 'answer_count')
    inlines = [QuizAnswerInline]

    fieldsets = (
        ('Question Info', {
            'fields': ('quiz', 'text', 'image_url', 'order')
        }),
        ('Scoring', {
            'fields': ('base_points', 'is_active')
        }),
        ('Metadata', {
            'fields': ('answer_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def text_preview(self, obj):
        """Show preview of question text"""
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text
    text_preview.short_description = "Question"

    def answer_count(self, obj):
        """Count of answers"""
        return obj.answers.count()
    answer_count.short_description = "Answers"


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    """Admin for quiz answers"""
    list_display = (
        'question_preview', 'text_preview', 'is_correct', 'order'
    )
    list_filter = ('is_correct', 'question__quiz')
    search_fields = ('text', 'question__text')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Answer Info', {
            'fields': ('question', 'text', 'is_correct', 'order')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        """Show preview of question"""
        text = obj.question.text
        return text[:40] + "..." if len(text) > 40 else text
    question_preview.short_description = "Question"

    def text_preview(self, obj):
        """Show preview of answer text"""
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = "Answer"


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    """Admin for quiz sessions"""
    list_display = (
        'player_name', 'room_number', 'quiz', 'hotel_identifier', 'score',
        'is_practice_mode', 'is_completed', 'current_multiplier',
        'duration_formatted', 'started_at'
    )
    list_filter = (
        'is_completed', 'is_practice_mode', 'quiz__difficulty_level',
        'hotel_identifier', 'started_at'
    )
    search_fields = (
        'player_name', 'room_number', 'external_player_id',
        'quiz__title', 'hotel_identifier'
    )
    readonly_fields = (
        'id', 'score', 'started_at', 'finished_at',
        'time_spent_seconds', 'duration_formatted', 'submission_count',
        'consecutive_correct', 'current_multiplier'
    )
    ordering = ('-started_at',)

    fieldsets = (
        ('Session Info', {
            'fields': (
                'id', 'quiz', 'hotel_identifier'
            )
        }),
        ('Player Info', {
            'fields': (
                'player_name', 'room_number', 'external_player_id',
                'is_practice_mode'
            )
        }),
        ('Results', {
            'fields': (
                'score', 'is_completed', 'current_question_index',
                'submission_count'
            )
        }),
        ('Turbo Mode', {
            'fields': (
                'consecutive_correct', 'current_multiplier'
            )
        }),
        ('Timing', {
            'fields': (
                'started_at', 'finished_at', 'time_spent_seconds',
                'duration_formatted'
            )
        }),
    )

    def submission_count(self, obj):
        """Count of submissions"""
        return obj.submissions.count()
    submission_count.short_description = "Submissions"


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    """Admin for quiz submissions"""
    list_display = (
        'session_player', 'question_preview', 'is_correct',
        'points_awarded', 'time_taken_seconds', 'answered_at'
    )
    list_filter = (
        'is_correct', 'session__quiz__difficulty_level',
        'hotel_identifier', 'answered_at'
    )
    search_fields = (
        'session__player_name', 'question_text',
        'selected_answer', 'hotel_identifier'
    )
    readonly_fields = (
        'id', 'hotel_identifier', 'is_correct',
        'points_awarded', 'answered_at'
    )
    ordering = ('-answered_at',)

    fieldsets = (
        ('Submission Info', {
            'fields': (
                'id', 'session', 'hotel_identifier', 'question'
            )
        }),
        ('Question Data', {
            'fields': ('question_text', 'question_data')
        }),
        ('Answer', {
            'fields': (
                'selected_answer', 'selected_answer_id',
                'is_correct', 'time_taken_seconds'
            )
        }),
        ('Scoring', {
            'fields': ('base_points', 'points_awarded')
        }),
        ('Metadata', {
            'fields': ('answered_at',),
            'classes': ('collapse',)
        }),
    )

    def session_player(self, obj):
        """Show session player name"""
        return obj.session.player_name if obj.session else "N/A"
    session_player.short_description = "Player"

    def question_preview(self, obj):
        """Show preview of question"""
        text = obj.question_text or (
            obj.question.text if obj.question else "N/A"
        )
        return text[:40] + "..." if len(text) > 40 else text
    question_preview.short_description = "Question"
