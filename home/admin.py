# admin.py

from django.contrib import admin
from .models import Post, Comment, CommentReply, Like


class CommentReplyInline(admin.StackedInline):
    model = CommentReply
    fk_name = 'comment'
    fields = (
        'author',
        'content_preview',
        'has_image',
        'created_at',
    )
    readonly_fields = (
        'content_preview',
        'has_image',
        'created_at',
    )
    extra = 0
    show_change_link = True

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if obj.content else '-'
    content_preview.short_description = 'Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


class CommentInline(admin.StackedInline):
    model = Comment
    fk_name = 'post'
    fields = (
        'author',
        'content_preview',
        'has_image',
        'created_at',
    )
    readonly_fields = (
        'content_preview',
        'has_image',
        'created_at',
    )
    extra = 0
    show_change_link = True

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if obj.content else '-'
    content_preview.short_description = 'Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'hotel',
        'created_at',
        'content_preview',
        'has_image',
    )
    list_filter = (
        'hotel',
        'created_at',
    )
    search_fields = (
        'content',
        'author__first_name',
        'author__last_name',
        'hotel__name',
    )
    readonly_fields = (
        'created_at',
    )
    inlines = (CommentInline,)

    def content_preview(self, obj):
        return (obj.content[:75] + '...') if obj.content else '-'
    content_preview.short_description = 'Content Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'post',
        'created_at',
        'content_preview',
        'has_image',
    )
    list_filter = (
        'created_at',
        'post__hotel',
    )
    search_fields = (
        'content',
        'author__first_name',
        'author__last_name',
        'post__content',
    )
    readonly_fields = (
        'content_preview',
        'has_image',
        'created_at',
    )
    raw_id_fields = (
        'post',
        'author',
    )
    inlines = (CommentReplyInline,)

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if obj.content else '-'
    content_preview.short_description = 'Comment Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(CommentReply)
class CommentReplyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'comment',
        'created_at',
        'content_preview',
        'has_image',
    )
    list_filter = (
        'created_at',
        'comment__post__hotel',
    )
    search_fields = (
        'content',
        'author__first_name',
        'author__last_name',
        'comment__content',
    )
    readonly_fields = (
        'content_preview',
        'has_image',
        'created_at',
    )
    raw_id_fields = (
        'comment',
        'author',
    )

    def content_preview(self, obj):
        return (obj.content[:50] + '...') if obj.content else '-'
    content_preview.short_description = 'Reply Preview'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'staff',
        'post',
        'created_at',
    )
    list_filter = (
        'created_at',
    )
    search_fields = (
        'staff__first_name',
        'staff__last_name',
        'post__content',
    )
    readonly_fields = (
        'created_at',
    )
