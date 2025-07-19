from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'hotel', 'created_at', 'content_preview', 'has_image')
    list_filter = ('hotel', 'created_at')
    search_fields = ('content', 'author__first_name', 'author__last_name', 'hotel__name')
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        return (obj.content[:75] + '...') if obj.content else '-'
    content_preview.short_description = 'Content Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_at', 'content_preview', 'has_image')
    list_filter = ('created_at', 'post__hotel')
    search_fields = ('content', 'author__first_name', 'author__last_name', 'post__content')
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if obj.content else '-'
    content_preview.short_description = 'Comment Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'staff', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('staff__first_name', 'staff__last_name', 'post__content')
    readonly_fields = ('created_at',)
