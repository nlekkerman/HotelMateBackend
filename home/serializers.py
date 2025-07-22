# src/home/serializers.py

from rest_framework import serializers
from .models import Post, Comment, CommentReply
from staff.serializers import StaffMinimalSerializer

class CommentReplySerializer(serializers.ModelSerializer):
    author_details = StaffMinimalSerializer(source='author', read_only=True)

    class Meta:
        model = CommentReply
        fields = [
            'id',
            'author', 'author_details',
            'comment',
            'content',
            'image',
            'created_at',
        ]
        read_only_fields = [
            'author',
            'created_at',
            'comment',
        ]


class CommentSerializer(serializers.ModelSerializer):
    author_details = StaffMinimalSerializer(source='author', read_only=True)
    replies        = CommentReplySerializer(many=True, read_only=True)
    image          = serializers.ImageField(required=False)

    class Meta:
        model = Comment
        fields = [
            'id',
            'author', 'author_details',
            'post',
            'content',
            'image',
            'created_at',
            'replies',
        ]
        read_only_fields = [
            'author',
            'created_at',
            'post',
            'replies',
        ]


class PostSerializer(serializers.ModelSerializer):
    author_details = StaffMinimalSerializer(source='author', read_only=True)
    hotel_slug     = serializers.SerializerMethodField()
    like_count     = serializers.IntegerField(source='likes.count',    read_only=True)
    comment_count  = serializers.IntegerField(source='comments.count', read_only=True)
    comments       = CommentSerializer(many=True, read_only=True)
    is_author      = serializers.SerializerMethodField()
    image          = serializers.ImageField(required=False)

    class Meta:
        model = Post
        fields = [
            'id',
            'author', 'author_details',
            'hotel', 'hotel_slug',
            'content', 'image', 'created_at',
            'like_count', 'comment_count',
            'comments',
            'is_author',   # ← new flag
        ]
        read_only_fields = [
            'author',
            'created_at',
            'hotel',
            'comments',
            'is_author',
        ]

    def get_hotel_slug(self, obj):
        return obj.hotel.slug if obj.hotel else None

    def get_is_author(self, obj):
        request = self.context.get('request', None)
        if not request or not hasattr(request.user, 'staff_profile'):
            return False
        return obj.author_id == request.user.staff_profile.id
