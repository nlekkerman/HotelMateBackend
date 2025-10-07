from django.contrib import admin
from .models import Game, GameHighScore, GameQRCode


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
