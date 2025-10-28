from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Game, GameHighScore, GameQRCode,
    MemoryGameCard, MemoryGameSession, MemoryGameStats, MemoryGameTournament,
    TournamentParticipation, MemoryGameAchievement, UserAchievement
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
