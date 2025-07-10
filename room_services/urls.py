from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomServiceItemViewSet,
    BreakfastItemViewSet,
    OrderViewSet,
    BreakfastOrderViewSet,
    validate_pin,
    validate_dinner_pin
)
order_pending_count = OrderViewSet.as_view({
    'get': 'pending_count'
})

breakfast_order_pending_count = BreakfastOrderViewSet.as_view({
    'get': 'pending_count'
})
# Hotel-scoped room-service orders:
order_list = OrderViewSet.as_view({
    'get': 'list','post': 'create'
})
order_detail = OrderViewSet.as_view({
    'get': 'retrieve','put': 'update','patch': 'partial_update','delete': 'destroy'
})
breakfast_order_list = BreakfastOrderViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

breakfast_order_detail = BreakfastOrderViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

# Manual paths for custom @action routes
room_service_items = RoomServiceItemViewSet.as_view({'get': 'menu'})
breakfast_items = BreakfastItemViewSet.as_view({'get': 'menu'})

urlpatterns = [
    path('', include(router.urls)),
    path('<str:hotel_slug>/orders/', order_list, name='hotel-order-list'),
    path('<str:hotel_slug>/orders/<int:pk>/', order_detail,name='hotel-order-detail'),
    path('<str:hotel_slug>/room/<int:room_number>/menu/', room_service_items, name='room-service-menu'),
    path('<str:hotel_slug>/room/<int:room_number>/breakfast/', breakfast_items, name='breakfast-menu'),
    path('<str:hotel_slug>/room/<int:room_number>/validate-pin/', validate_pin, name='validate-pin'),
    path('<str:hotel_slug>/breakfast-orders/', breakfast_order_list, name='breakfastorder-list'),
    path('<str:hotel_slug>/breakfast-orders/<int:pk>/', breakfast_order_detail, name='breakfastorder-detail'),
    path('<str:hotel_slug>/breakfast-orders/breakfast-pending-count/', breakfast_order_pending_count, name='breakfastorder-pending-count'),
    path(
        '<str:hotel_slug>/restaurant/<str:restaurant_slug>/room/<int:room_number>/validate-dinner-pin/',
        validate_dinner_pin,
        name='validate-dinner-pin'
    ),
]
