"""
NEW GUESSTICULATOR QUIZ ADMIN
Admin interface for managing quiz system
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models_new_quiz import (
    QuizCategory,
    Quiz,
    QuizQuestion,
    QuizAnswer,
    QuizSession,
    QuizSubmission,
    QuizLeaderboard,
    QuizTournament,
    TournamentLeaderboard
)


# ============================================================================
# INLINE ADMINS
# ============================================================================

class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4
    max_num = 4
    fields = ['text', 'is_correct', 'order']
    ordering = ['order']


class QuizSubmissionInline(admin.TabularInline):
    model = QuizSubmission
    extra = 0
    readonly_fields = [
        'category', 'question_text', 'selected_answer',
        'correct_answer', 'is_correct', 'time_taken_seconds',
        'was_turbo_active', 'points_awarded', 'answered_at'
    ]
    fields = readonly_fields
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================================================
# CATEGORY ADMIN
# ============================================================================

@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'slug',
        'order',
        'is_math_category',
        'question_count_display',
        'is_active'
    ]
    list_filter = ['is_active', 'is_math_category']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'order')
        }),
        ('Settings', {
            'fields': ('is_math_category', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def question_count_display(self, obj):
        """Display question count"""
        count = obj.question_count
        if count == "Dynamic":
            return format_html(
                '<span style="color: blue; font-weight: bold;">Dynamic</span>'
            )
        return count
    question_count_display.short_description = 'Questions'


# ============================================================================
# QUIZ ADMIN
# ============================================================================

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'questions_per_category',
        'time_per_question_seconds',
        'turbo_mode_threshold',
        'is_active',
        'qr_code_display'
    ]
    list_filter = ['is_active']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Info', {
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
            'fields': ('qr_code_url', 'qr_generated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['qr_code_url', 'qr_generated_at', 'created_at', 'updated_at']
    
    actions = ['generate_qr_codes']
    
    def qr_code_display(self, obj):
        """Display QR code status"""
        if obj.qr_code_url:
            return format_html(
                '<a href="{}" target="_blank">View QR</a>',
                obj.qr_code_url
            )
        return format_html(
            '<span style="color: red;">Not generated</span>'
        )
    qr_code_display.short_description = 'QR Code'
    
    def generate_qr_codes(self, request, queryset):
        """Generate QR codes for selected quizzes"""
        count = 0
        for quiz in queryset:
            quiz.generate_qr_code()
            count += 1
        self.message_user(
            request,
            f'Successfully generated QR codes for {count} quiz(zes).'
        )
    generate_qr_codes.short_description = 'Generate QR codes'


# ============================================================================
# QUESTION ADMIN
# ============================================================================

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'short_text',
        'category',
        'has_image',
        'answer_count',
        'correct_answer_display',
        'is_active'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['text']
    inlines = [QuizAnswerInline]
    
    fieldsets = (
        ('Question', {
            'fields': ('category', 'text', 'image_url')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def short_text(self, obj):
        """Display shortened text"""
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    short_text.short_description = 'Question'
    
    def has_image(self, obj):
        """Check if question has image"""
        if obj.image_url:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html(
            '<span style="color: gray;">-</span>'
        )
    has_image.short_description = 'Image'
    
    def answer_count(self, obj):
        """Count answers"""
        count = obj.answers.count()
        if count == 4:
            color = 'green'
        elif count > 0:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}/4</span>',
            color, count
        )
    answer_count.short_description = 'Answers'
    
    def correct_answer_display(self, obj):
        """Display correct answer"""
        correct = obj.correct_answer
        if correct:
            return format_html(
                '<span style="color: green;">{}</span>',
                correct.text[:30]
            )
        return format_html(
            '<span style="color: red;">None</span>'
        )
    correct_answer_display.short_description = 'Correct Answer'


# ============================================================================
# SESSION ADMIN
# ============================================================================

@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = [
        'player_name',
        'quiz',
        'mode_display',
        'score',
        'status_display',
        'turbo_display',
        'started_at',
        'duration_formatted'
    ]
    list_filter = [
        'is_tournament_mode',
        'is_completed',
        'is_turbo_active',
        'tournament',
        'started_at'
    ]
    search_fields = [
        'player_name',
        'session_token',
        'quiz__title'
    ]
    readonly_fields = [
        'id',
        'session_token',
        'quiz',
        'player_name',
        'is_tournament_mode',
        'tournament',
        'score',
        'started_at',
        'finished_at',
        'is_completed',
        'time_spent_seconds',
        'duration_formatted',
        'consecutive_correct',
        'is_turbo_active',
        'current_category_index',
        'current_question_index'
    ]
    inlines = [QuizSubmissionInline]
    
    fieldsets = (
        ('Session Info', {
            'fields': (
                'id',
                'session_token',
                'player_name',
                'quiz'
            )
        }),
        ('Game Mode', {
            'fields': (
                'is_tournament_mode',
                'tournament'
            )
        }),
        ('Game State', {
            'fields': (
                'score',
                'consecutive_correct',
                'is_turbo_active',
                'current_category_index',
                'current_question_index'
            )
        }),
        ('Timing', {
            'fields': (
                'started_at',
                'finished_at',
                'is_completed',
                'time_spent_seconds',
                'duration_formatted'
            )
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def mode_display(self, obj):
        """Display mode icon"""
        if obj.is_tournament_mode:
            return format_html('🏆 Tournament')
        return format_html('🎮 Casual')
    mode_display.short_description = 'Mode'
    
    def status_display(self, obj):
        """Display completion status"""
        if obj.is_completed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Complete</span>'
            )
        return format_html(
            '<span style="color: orange;">▶ Playing</span>'
        )
    status_display.short_description = 'Status'
    
    def turbo_display(self, obj):
        """Display turbo status"""
        if obj.is_turbo_active:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔥 {}x</span>',
                obj.consecutive_correct
            )
        return format_html(
            '<span style="color: gray;">{}/5</span>',
            obj.consecutive_correct
        )
    turbo_display.short_description = 'Turbo'


# ============================================================================
# LEADERBOARD ADMIN
# ============================================================================

@admin.register(QuizLeaderboard)
class QuizLeaderboardAdmin(admin.ModelAdmin):
    list_display = [
        'rank_display',
        'player_name',
        'best_score',
        'games_played',
        'last_played',
        'view_session_link'
    ]
    list_filter = ['quiz', 'last_played']
    search_fields = ['player_name', 'session_token']
    readonly_fields = [
        'quiz',
        'session_token',
        'player_name',
        'best_score',
        'best_session',
        'games_played',
        'last_played',
        'created_at',
        'updated_at'
    ]
    ordering = ['-best_score', 'last_played']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def rank_display(self, obj):
        """Calculate and display rank"""
        rank = QuizLeaderboard.objects.filter(
            quiz=obj.quiz,
            best_score__gt=obj.best_score
        ).count() + 1
        
        if rank == 1:
            return format_html('🥇 #1')
        elif rank == 2:
            return format_html('🥈 #2')
        elif rank == 3:
            return format_html('🥉 #3')
        return f'#{rank}'
    rank_display.short_description = 'Rank'
    
    def view_session_link(self, obj):
        """Link to best session"""
        if obj.best_session:
            url = reverse('admin:entertainment_quizsession_change', args=[obj.best_session.id])
            return format_html(
                '<a href="{}">View Session</a>',
                url
            )
        return '-'
    view_session_link.short_description = 'Best Session'


# ============================================================================
# TOURNAMENT ADMIN
# ============================================================================

@admin.register(QuizTournament)
class QuizTournamentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'quiz',
        'status',
        'start_date',
        'end_date',
        'participant_count_display',
        'qr_code_display'
    ]
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'slug', 'quiz__title']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'quiz')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Prizes', {
            'fields': ('first_prize', 'second_prize', 'third_prize')
        }),
        ('QR Code', {
            'fields': ('qr_code_url', 'qr_generated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['qr_code_url', 'qr_generated_at', 'created_at', 'updated_at']
    
    actions = ['generate_qr_codes', 'activate_tournaments']
    
    def participant_count_display(self, obj):
        """Display participant count"""
        count = QuizSession.objects.filter(
            tournament=obj,
            is_completed=True
        ).values('session_token').distinct().count()
        return format_html(
            '<span style="font-weight: bold;">{}</span> players',
            count
        )
    participant_count_display.short_description = 'Participants'
    
    def qr_code_display(self, obj):
        """Display QR code"""
        if obj.qr_code_url:
            return format_html(
                '<a href="{}" target="_blank">View QR</a>',
                obj.qr_code_url
            )
        return format_html(
            '<span style="color: red;">Not generated</span>'
        )
    qr_code_display.short_description = 'QR Code'
    
    def generate_qr_codes(self, request, queryset):
        """Generate QR codes"""
        count = 0
        for tournament in queryset:
            tournament.generate_qr_code()
            count += 1
        self.message_user(
            request,
            f'Generated QR codes for {count} tournament(s).'
        )
    generate_qr_codes.short_description = 'Generate QR codes'
    
    def activate_tournaments(self, request, queryset):
        """Activate tournaments"""
        count = queryset.update(status=QuizTournament.TournamentStatus.ACTIVE)
        self.message_user(
            request,
            f'Activated {count} tournament(s).'
        )
    activate_tournaments.short_description = 'Activate selected tournaments'


# ============================================================================
# TOURNAMENT LEADERBOARD ADMIN
# ============================================================================

@admin.register(TournamentLeaderboard)
class TournamentLeaderboardAdmin(admin.ModelAdmin):
    list_display = [
        'rank_display',
        'player_name',
        'tournament',
        'best_score',
        'updated_at',
        'view_session_link'
    ]
    list_filter = ['tournament', 'updated_at']
    search_fields = ['player_name', 'session_token', 'tournament__name']
    readonly_fields = [
        'tournament',
        'session_token',
        'player_name',
        'best_score',
        'best_session',
        'created_at',
        'updated_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def rank_display(self, obj):
        """Calculate rank"""
        rank = TournamentLeaderboard.objects.filter(
            tournament=obj.tournament,
            best_score__gt=obj.best_score
        ).count() + 1
        
        if rank == 1:
            return format_html('🥇 #1')
        elif rank == 2:
            return format_html('🥈 #2')
        elif rank == 3:
            return format_html('🥉 #3')
        return f'#{rank}'
    rank_display.short_description = 'Rank'
    
    def view_session_link(self, obj):
        """Link to session"""
        if obj.best_session:
            url = reverse('admin:entertainment_quizsession_change', args=[obj.best_session.id])
            return format_html(
                '<a href="{}">View Session</a>',
                url
            )
        return '-'
    view_session_link.short_description = 'Best Session'
