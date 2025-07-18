# home/serializers.py
from rest_framework import serializers
from .models import Post, Like, Comment
from hotel.models import Hotel


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'author',
            'author_name',
            'content',
            'created_at',
        )

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"


class PostSerializer(serializers.ModelSerializer):
    author_name   = serializers.SerializerMethodField()
    like_count    = serializers.IntegerField(
        source='likes.count',
        read_only=True,
    )
    comment_count = serializers.IntegerField(
        source='comments.count',
        read_only=True,
    )
    comments      = CommentSerializer(many=True, read_only=True)
    hotel_slug    = serializers.SlugRelatedField(
        source='hotel',
        slug_field='slug',
        queryset=Hotel.objects.all(),
    )

    class Meta:
        model = Post
        fields = (
            'id',
            'author',
            'author_name',
            'hotel',
            'hotel_slug',
            'content',
            'image',
            'created_at',
            'like_count',
            'comment_count',
            'comments',
        )
        read_only_fields = ('author', 'created_at')

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"
