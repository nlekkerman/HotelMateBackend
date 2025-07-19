from rest_framework import serializers
from .models import Post, Comment
from staff.serializers import StaffMinimalSerializer

class CommentSerializer(serializers.ModelSerializer):
    author_details = StaffMinimalSerializer(source='author', read_only=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_details', 'post', 'content', 'image', 'created_at']
        read_only_fields = ['author', 'created_at', 'post']

class PostSerializer(serializers.ModelSerializer):
    author_details = StaffMinimalSerializer(source='author', read_only=True)
    hotel_slug = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False)
    class Meta:
        model = Post
        fields = ['id', 'author', 'author_details', 'hotel', 'hotel_slug', 'content', 'image', 'created_at', 'like_count', 'comment_count', 'comments']
        read_only_fields = ['author', 'created_at', 'hotel']

    def get_hotel_slug(self, obj):
        return obj.hotel.slug if obj.hotel else None
