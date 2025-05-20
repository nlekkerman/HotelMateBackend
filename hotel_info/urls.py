from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotelInfoViewSet

router = DefaultRouter()
router.register(r'hotelinfo', HotelInfoViewSet, basename='hotelinfo')

urlpatterns = [
    path('', include(router.urls)),
]
