# ar_navigation/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ARAnchorViewSet

router = DefaultRouter()
router.register(r'ar-anchors', ARAnchorViewSet, basename='ar-anchor')

urlpatterns = [
    path('', include(router.urls)),
]
