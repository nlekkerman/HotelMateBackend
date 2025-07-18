# home/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Post, Like
from .serializers import PostSerializer
from hotel.models import Hotel


class PostViewSet(viewsets.ModelViewSet):
    """
    /api/{hotel_slug}/posts/
    """
    serializer_class   = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends    = (filters.SearchFilter,)
    search_fields      = ('content', 'author__first_name', 'author__last_name')

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        qs = Post.objects.select_related('author', 'hotel') \
                         .prefetch_related('likes', 'comments')
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs

    def perform_create(self, serializer):
        staff = getattr(self.request.user, 'staff_profile', None)
        hotel = get_object_or_404(Hotel, slug=self.kwargs.get('hotel_slug'))
        serializer.save(author=staff, hotel=hotel)

    @action(detail=True, methods=('post',))
    def like(self, request, hotel_slug=None, pk=None):
        """
        POST /api/{hotel_slug}/posts/{pk}/like/
        Toggles a Like for the authenticated staff user.
        """
        post = self.get_object()
        staff = request.user.staff_profile
        like, created = Like.objects.get_or_create(staff=staff, post=post)
        if not created:
            like.delete()
            return Response({'liked': False}, status=status.HTTP_200_OK)
        return Response({'liked': True}, status=status.HTTP_201_CREATED)
