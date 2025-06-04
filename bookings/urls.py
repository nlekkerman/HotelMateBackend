from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet, 
    BookingCategoryViewSet, 
    GuestDinnerBookingView  # 👈 this is your custom view
)

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'categories', BookingCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'bookings/<str:hotel_slug>/restaurant/<str:restaurant_slug>/room/<str:room_number>/',
        GuestDinnerBookingView.as_view(),
        name='guest-dinner-booking'
    ),
]
