from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'(?P<hotel_slug>[\w-]+)/posts', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),

    # Comments by hotel and post context
    path(
        '<str:hotel_slug>/posts/<int:post_pk>/comments/',
        CommentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='comment-list-create'
    ),
    path(
        '<str:hotel_slug>/posts/<int:post_pk>/comments/<int:pk>/',
        CommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='comment-detail'
    ),
]
