from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Game, GameHighScore, GameQRCode,
    MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament,
    TournamentParticipation, MemoryGameAchievement, UserAchievement,
    # Quiz models
    QuizCategory, Quiz, QuizQuestion, QuizAnswer,
    QuizSession, QuizSubmission, QuizLeaderboard, QuizPlayerProgress,
    QuizTournament, TournamentLeaderboard
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


# ============================================================================
# GUESSTICULATOR QUIZ GAME ADMIN
# ============================================================================

class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4
    min_num = 4
    max_num = 4
    fields = ('text', 'is_correct', 'order')
    ordering = ('order',)


@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug', 'order', 'question_count', 
        'is_math_category', 'is_active'
    )
    list_filter = ('is_active', 'is_math_category')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'order')
        }),
        ('Settings', {
            'fields': ('is_math_category', 'is_active')
        }),
    )
    
    def question_count(self, obj):
        return obj.question_count
    question_count.short_description = 'Questions'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'slug', 'questions_per_category',
        'time_per_question_seconds', 'turbo_mode_threshold',
        'turbo_multiplier', 'is_active', 'qr_preview'
    )
    list_filter = ('is_active',)
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('qr_preview', 'qr_generated_at', 'created_at')
    actions = ['generate_qr_codes']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'is_active')
        }),
        ('Game Settings', {
            'fields': (
                'questions_per_category',
                'time_per_question_seconds',
                'turbo_mode_threshold',
                'turbo_multiplier'
            )
        }),
        ('QR Code', {
            'fields': ('qr_code_url', 'qr_preview', 'qr_generated_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def qr_preview(self, obj):
        if obj.qr_code_url:
            return format_html(
                '<img src="{}" style="max-width:150px; max-height:150px;"/>',
                obj.qr_code_url
            )
        return "No QR code"
    qr_preview.short_description = 'QR Code'
    
    def generate_qr_codes(self, request, queryset):
        count = 0
        for quiz in queryset:
            quiz.generate_qr_code()
            count += 1
        self.message_user(request, f"Generated QR codes for {count} quiz(zes)")
    generate_qr_codes.short_description = "Generate QR codes"


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'text_preview', 'category', 'answer_count',
        'correct_answer_text', 'is_active'
    )
    list_filter = ('category', 'is_active')
    search_fields = ('text',)
    inlines = [QuizAnswerInline]
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Question', {
            'fields': ('category', 'text', 'image_url', 'is_active')
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def text_preview(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Question'
    
    def answer_count(self, obj):
        count = obj.answers.count()
        if count != 4:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {} answers</span>',
                count
            )
        return f'✓ {count}'
    answer_count.short_description = 'Answers'
    
    def correct_answer_text(self, obj):
        correct = obj.correct_answer
        if correct:
            return correct.text
        return format_html('<span style="color: red;">❌ None</span>')
    correct_answer_text.short_description = 'Correct Answer'


class QuizSubmissionInline(admin.TabularInline):
    model = QuizSubmission
    extra = 0
    can_delete = False
    readonly_fields = (
        'category', 'question_text', 'selected_answer',
        'correct_answer', 'is_correct', 'time_taken_seconds',
        'was_turbo_active', 'points_awarded', 'answered_at'
    )
    fields = readonly_fields
    ordering = ('answered_at',)
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = (
        'player_name', 'mode_icon', 'score', 'turbo_icon',
        'completion_status', 'duration_formatted', 'started_at'
    )
    list_filter = (
        'is_completed', 'is_tournament_mode',
        'is_turbo_active', 'started_at'
    )
    search_fields = (
        'player_name', 'session_token', 'id'
    )
    readonly_fields = (
        'id', 'quiz', 'session_token', 'tournament',
        'score', 'consecutive_correct', 'is_turbo_active',
        'current_category_index', 'current_question_index',
        'is_completed', 'finished_at', 'duration_formatted',
        'started_at'
    )
    inlines = [QuizSubmissionInline]
    
    fieldsets = (
        ('Player', {
            'fields': ('player_name', 'session_token')
        }),
        ('Game', {
            'fields': (
                'quiz', 'is_tournament_mode', 'tournament',
                'score', 'consecutive_correct', 'is_turbo_active'
            )
        }),
        ('Progress', {
            'fields': (
                'current_category_index', 'current_question_index',
                'is_completed', 'finished_at', 'duration_formatted'
            )
        }),
        ('Timestamps', {
            'fields': ('started_at',),
            'classes': ('collapse',)
        })
    )
    
    def mode_icon(self, obj):
        if obj.is_tournament_mode:
            return '🏆 Tournament'
        return '🎮 Casual'
    mode_icon.short_description = 'Mode'
    
    def turbo_icon(self, obj):
        if obj.is_turbo_active:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔥 TURBO</span>'
            )
        return f'⚡ {obj.consecutive_correct} streak'
    turbo_icon.short_description = 'Turbo Status'
    
    def completion_status(self, obj):
        if obj.is_completed:
            return format_html(
                '<span style="color: green;">✓ Complete</span>'
            )
        return format_html(
            '<span style="color: orange;">⏳ In Progress</span>'
        )
    completion_status.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False


@admin.register(QuizLeaderboard)
class QuizLeaderboardAdmin(admin.ModelAdmin):
    list_display = (
        'rank_display', 'player_name', 'best_score',
        'games_played', 'best_session_link', 'last_played'
    )
    list_filter = ('quiz', 'last_played')
    search_fields = ('player_name', 'session_token')
    readonly_fields = (
        'quiz', 'session_token', 'player_name',
        'best_score', 'best_session', 'games_played',
        'last_played'
    )
    ordering = ('-best_score', 'last_played')
    
    fieldsets = (
        ('Player', {
            'fields': ('player_name', 'session_token')
        }),
        ('Stats', {
            'fields': (
                'quiz', 'best_score', 'games_played',
                'best_session', 'last_played'
            )
        })
    )
    
    def rank_display(self, obj):
        entries = QuizLeaderboard.objects.filter(
            quiz=obj.quiz
        ).order_by('-best_score', 'last_played')
        
        rank = None
        for idx, entry in enumerate(entries, 1):
            if entry.id == obj.id:
                rank = idx
                break
        
        if rank == 1:
            return format_html(
                '<span style="font-size: 16px;">🥇</span> #1'
            )
        elif rank == 2:
            return format_html(
                '<span style="font-size: 16px;">🥈</span> #2'
            )
        elif rank == 3:
            return format_html(
                '<span style="font-size: 16px;">🥉</span> #3'
            )
        return f'#{rank}'
    rank_display.short_description = 'Rank'
    
    def best_session_link(self, obj):
        if obj.best_session:
            url = reverse(
                'admin:entertainment_quizsession_change',
                args=[obj.best_session.id]
            )
            return format_html(
                '<a href="{}">View Session</a>',
                url
            )
        return '-'
    best_session_link.short_description = 'Best Session'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(QuizPlayerProgress)
class QuizPlayerProgressAdmin(admin.ModelAdmin):
    list_display = ('session_token', 'quiz', 'total_seen', 'updated_at')
    list_filter = ('quiz', 'updated_at')
    search_fields = ('session_token',)
    
    def total_seen(self, obj):
        total = sum(len(ids) for ids in obj.seen_question_ids.values())
        total += len(obj.seen_math_questions)
        return total
    total_seen.short_description = 'Total Seen'
    
    def has_add_permission(self, request):
        return False
@admin.register(QuizTournament)
class QuizTournamentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'start_date', 'end_date',
        'participant_count', 'qr_preview'
    )
    list_filter = ('status', 'start_date')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'qr_preview', 'qr_generated_at', 'participant_count',
        'created_at'
    )
    actions = ['generate_qr_codes', 'activate_tournaments']
    
    fieldsets = (
        ('Tournament Information', {
            'fields': ('name', 'slug', 'description', 'quiz')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Stats', {
            'fields': ('participant_count',)
        }),
        ('QR Code', {
            'fields': ('qr_code_url', 'qr_preview', 'qr_generated_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def qr_preview(self, obj):
        if obj.qr_code_url:
            return format_html(
                '<img src="{}" style="max-width:150px; max-height:150px;"/>',
                obj.qr_code_url
            )
        return "No QR code"
    qr_preview.short_description = 'QR Code'
    
    def participant_count(self, obj):
        count = QuizSession.objects.filter(
            tournament=obj,
            is_tournament_mode=True
        ).values('session_token').distinct().count()
        return count
    participant_count.short_description = 'Participants'
    
    def generate_qr_codes(self, request, queryset):
        count = 0
        for tournament in queryset:
            tournament.generate_qr_code()
            count += 1
        self.message_user(
            request,
            f"Generated QR codes for {count} tournament(s)"
        )
    generate_qr_codes.short_description = "Generate QR codes"
    
    def activate_tournaments(self, request, queryset):
        count = queryset.update(
            status=QuizTournament.TournamentStatus.ACTIVE
        )
        self.message_user(
            request,
            f"Activated {count} tournament(s)"
        )
    activate_tournaments.short_description = "Activate tournaments"


@admin.register(TournamentLeaderboard)
class TournamentLeaderboardAdmin(admin.ModelAdmin):
    list_display = (
        'rank_display', 'tournament', 'player_name',
        'best_score', 'best_session_link', 'updated_at'
    )
    list_filter = ('tournament', 'updated_at')
    search_fields = ('player_name', 'session_token')
    readonly_fields = (
        'tournament', 'session_token', 'player_name',
        'best_score', 'best_session', 'updated_at'
    )
    ordering = ('tournament', '-best_score', 'updated_at')
    
    fieldsets = (
        ('Tournament', {
            'fields': ('tournament',)
        }),
        ('Player', {
            'fields': ('player_name', 'session_token')
        }),
        ('Stats', {
            'fields': ('best_score', 'best_session', 'updated_at')
        })
    )
    
    def rank_display(self, obj):
        entries = TournamentLeaderboard.objects.filter(
            tournament=obj.tournament
        ).order_by('-best_score', 'updated_at')
        
        rank = None
        for idx, entry in enumerate(entries, 1):
            if entry.id == obj.id:
                rank = idx
                break
        
        if rank == 1:
            return format_html(
                '<span style="font-size: 16px;">🥇</span> #1'
            )
        elif rank == 2:
            return format_html(
                '<span style="font-size: 16px;">🥈</span> #2'
            )
        elif rank == 3:
            return format_html(
                '<span style="font-size: 16px;">🥉</span> #3'
            )
        return f'#{rank}'
    rank_display.short_description = 'Rank'
    
    def best_session_link(self, obj):
        if obj.best_session:
            url = reverse(
                'admin:entertainment_quizsession_change',
                args=[obj.best_session.id]
            )
            return format_html(
                '<a href="{}">View Session</a>',
                url
            )
        return '-'
    best_session_link.short_description = 'Best Session'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

