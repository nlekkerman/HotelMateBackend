from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet,
    BookingCategoryViewSet,
    GuestDinnerBookingView,
    RestaurantViewSet,
)

# Register viewsets to the router
router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'categories', BookingCategoryViewSet)

urlpatterns = [
    # Include router-generated URLs (e.g. /bookings/, /categories/)
    path('', include(router.urls)),

    # Public guest dinner booking route (QR form submission)
    path(
        'guest-booking/<str:hotel_slug>/restaurant/<str:restaurant_slug>/room/<str:room_number>/',
        GuestDinnerBookingView.as_view(),
        name='guest-dinner-booking'
    ),
    
    path(
        'guest-booking/<str:hotel_slug>/restaurant/<str:restaurant_slug>/',
        GuestDinnerBookingView.as_view(),
        name='guest-dinner-booking-list'
    ),
]
