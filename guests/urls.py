from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuestViewSet

router = DefaultRouter()
router.register(r'', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
