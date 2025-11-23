# src/home/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet, CommentReplyViewSet

router = DefaultRouter()
# Posts endpoint: /api/staff/hotels/{hotel_slug}/home/posts/
# hotel_slug is already captured by staff_urls.py
router.register(r'posts', PostViewSet, basename='post')

urlpatterns = [
    # Include the Post routes
    path('', include(router.urls)),

    # Comments (root-level) under a specific post
    path(
        'posts/<int:post_pk>/comments/',
        CommentViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='comment-list-create'
    ),
    path(
        'posts/<int:post_pk>/comments/<int:pk>/',
        CommentViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='comment-detail'
    ),

    # Replies under a specific comment
    path(
        'posts/<int:post_pk>/comments/<int:comment_pk>/replies/',
        CommentReplyViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='reply-list-create'
    ),
    path(
        'posts/<int:post_pk>/comments/<int:comment_pk>/replies/<int:pk>/',
        CommentReplyViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='reply-detail'
    ),
]
