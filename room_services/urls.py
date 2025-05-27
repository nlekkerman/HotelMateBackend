from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomServiceItemViewSet,
    BreakfastItemViewSet,
    OrderViewSet,
    BreakfastOrderViewSet,
    validate_pin,
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'breakfast-orders', BreakfastOrderViewSet, basename='breakfast-order')

# Manual paths for custom @action routes
room_service_items = RoomServiceItemViewSet.as_view({'get': 'menu'})
breakfast_items = BreakfastItemViewSet.as_view({'get': 'menu'})

urlpatterns = [
    path('', include(router.urls)),
    path('room/<int:room_number>/menu/', room_service_items, name='room-service-menu'),
    path('room/<int:room_number>/breakfast/', breakfast_items, name='breakfast-menu'),
    path('<int:room_number>/validate-pin/', validate_pin, name='validate-pin'),
]
