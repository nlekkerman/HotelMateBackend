from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import action
from .models import Like 

from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from hotel.models import Hotel


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        hotel_slug = self.kwargs['hotel_slug']
        return Post.objects.filter(hotel__slug=hotel_slug).select_related('author', 'hotel').prefetch_related('likes', 'comments')

    def perform_create(self, serializer):
        hotel_slug = self.kwargs['hotel_slug']
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
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
        post = get_object_or_404(Post, id=pk, hotel__slug=hotel_slug)
        staff = getattr(request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError("Your user account is not linked to a staff profile.")
        
        like, created = Like.objects.get_or_create(post=post, staff=staff)
        if not created:
            like.delete()  # Toggle like
            return Response({'liked': False, 'like_count': post.likes.count()})
        
        return Response({'liked': True, 'like_count': post.likes.count()})

class CommentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ✅ for image upload

    def list(self, request, hotel_slug=None, post_pk=None):
        comments = Comment.objects.filter(post_id=post_pk).select_related('author')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def create(self, request, hotel_slug=None, post_pk=None):
        post = get_object_or_404(Post, id=post_pk, hotel__slug=hotel_slug)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            staff = getattr(request.user, 'staff_profile', None)
            if not staff:
                raise ValidationError("Your user account is not linked to a staff profile.")
            serializer.save(author=staff, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, hotel_slug=None, post_pk=None, pk=None):
        comment = get_object_or_404(Comment, id=pk, post_id=post_pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    def update(self, request, hotel_slug=None, post_pk=None, pk=None):
        comment = get_object_or_404(Comment, id=pk, post_id=post_pk)
        if comment.author != getattr(request.user, 'staff_profile', None):
            raise PermissionDenied("You can only update your own comments.")
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, hotel_slug=None, post_pk=None, pk=None):
        comment = get_object_or_404(Comment, id=pk, post_id=post_pk)
        if comment.author != getattr(request.user, 'staff_profile', None):
            raise PermissionDenied("You can only partially update your own comments.")
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, hotel_slug=None, post_pk=None, pk=None):
        comment = get_object_or_404(Comment, id=pk, post_id=post_pk)
        if comment.author != getattr(request.user, 'staff_profile', None):
            raise PermissionDenied("You can only delete your own comments.")
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
