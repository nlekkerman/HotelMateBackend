# home/admin.py
from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'hotel', 'created_at')
    list_filter = ('hotel__slug', 'created_at')
    search_fields = (
        'content',
        'author__first_name',
        'author__last_name',
    )


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'staff', 'post', 'created_at')
    list_filter = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at')
    search_fields = (
        'content',
        'author__first_name',
        'author__last_name',
    )
