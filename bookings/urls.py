from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, BookingCategoryViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'categories', BookingCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
