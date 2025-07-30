from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, RoomByHotelAndNumberView, AddGuestToRoomView, checkout_rooms,checkout_needed

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')

urlpatterns = [
    path('', include(router.urls)),
    path('<str:hotel_identifier>/rooms/<str:room_number>/add-guest/', AddGuestToRoomView.as_view(), name='add-guest-to-room'),
    path('<str:hotel_identifier>/rooms/<str:room_number>/', RoomByHotelAndNumberView.as_view(), name='room-by-hotel-and-number'),
    path(
        '<str:hotel_slug>/checkout/',
        checkout_rooms,
        name='room-checkout'
    ),
    path('<str:hotel_slug>/checkout-needed/', checkout_needed, name='checkout-needed'),
]
