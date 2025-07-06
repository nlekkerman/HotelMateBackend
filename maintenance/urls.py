from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaintenanceRequestViewSet, MaintenanceCommentViewSet, MaintenancePhotoViewSet

router = DefaultRouter()
router.register(r'requests', MaintenanceRequestViewSet)
router.register(r'comments', MaintenanceCommentViewSet)
router.register(r'photos', MaintenancePhotoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
