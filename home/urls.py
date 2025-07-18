# home/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

router = DefaultRouter()
# Register 'posts' on the router, but wrap it in a slug-based path
router.register(r'posts', PostViewSet, basename='hotel-posts')

urlpatterns = [
    # /api/<hotel_slug>/posts/ ...
    path('<str:hotel_slug>/', include(router.urls)),
]
