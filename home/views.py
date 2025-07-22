# src/home/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from .models import Post, Comment, CommentReply, Like
from .serializers import (
    PostSerializer,
    CommentSerializer,
    CommentReplySerializer,
)
from hotel.models import Hotel


class PostViewSet(viewsets.ModelViewSet):
    """
    list/retrieve/create/update/destroy Posts for a given hotel_slug,
    including their top‐level Comments (each with nested replies).
    """
    serializer_class   = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get_queryset(self):
        hotel_slug = self.kwargs['hotel_slug']
        # Prefetch comments with their replies and authors
        comment_qs = (
            Comment.objects
                   .filter(post__hotel__slug=hotel_slug)
                   .select_related('author')
                   .prefetch_related('replies__author')
        )
        return (
            Post.objects
                .filter(hotel__slug=hotel_slug)
                .select_related('author', 'hotel')
                .prefetch_related(
                    'likes',
                    Prefetch('comments', queryset=comment_qs)
                )
        )

    def perform_create(self, serializer):
        hotel = get_object_or_404(Hotel, slug=self.kwargs['hotel_slug'])
        staff = getattr(self.request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError("Your user account is not linked to a staff profile.")
        serializer.save(author=staff, hotel=hotel)

    def get_object(self):
        post = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE'] and post.author != getattr(self.request.user, 'staff_profile', None):
            raise PermissionDenied("You can only modify your own posts.")
        return post

    @action(detail=True, methods=['post'])
    def like(self, request, hotel_slug=None, pk=None):
        post  = get_object_or_404(Post, id=pk, hotel__slug=hotel_slug)
        staff = getattr(request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError("Your user account is not linked to a staff profile.")
        like, created = Like.objects.get_or_create(post=post, staff=staff)
        if not created:
            like.delete()
            return Response({'liked': False, 'like_count': post.likes.count()})
        return Response({'liked': True,  'like_count': post.likes.count()})


class CommentViewSet(viewsets.ModelViewSet):
    """
    list/retrieve/create/update/destroy root-level Comments for a given post.
    """
    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get_queryset(self):
        hotel_slug = self.kwargs['hotel_slug']
        post_pk    = self.kwargs['post_pk']
        return (
            Comment.objects
                   .filter(post__id=post_pk, post__hotel__slug=hotel_slug)
                   .select_related('author')
                   .prefetch_related('replies__author')
        )

    def perform_create(self, serializer):
        hotel_slug = self.kwargs['hotel_slug']
        post_pk    = self.kwargs['post_pk']
        post = get_object_or_404(Post, id=post_pk, hotel__slug=hotel_slug)
        staff = getattr(self.request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError("Your user account is not linked to a staff profile.")
        serializer.save(author=staff, post=post)


class CommentReplyViewSet(viewsets.ModelViewSet):
    """
    list/retrieve/create/update/destroy replies to a specific comment.
    """
    serializer_class   = CommentReplySerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def get_queryset(self):
        hotel_slug = self.kwargs['hotel_slug']
        comment_pk = self.kwargs['comment_pk']
        return (
            CommentReply.objects
                        .filter(comment__id=comment_pk, comment__post__hotel__slug=hotel_slug)
                        .select_related('author', 'comment')
        )

    def perform_create(self, serializer):
        hotel_slug = self.kwargs['hotel_slug']
        post_pk    = self.kwargs['post_pk']
        comment_pk = self.kwargs['comment_pk']

        comment = get_object_or_404(
            Comment,
            id=comment_pk,
            post__id=post_pk,
            post__hotel__slug=hotel_slug
        )
        staff = getattr(self.request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError("Your user account is not linked to a staff profile.")
        serializer.save(author=staff, comment=comment)
