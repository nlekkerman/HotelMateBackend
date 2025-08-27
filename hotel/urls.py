from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HotelViewSet, HotelBySlugView  # Import the new view

# Default router for the main HotelViewSet
router = DefaultRouter()
router.register(r'hotels', HotelViewSet)

urlpatterns = [
    path("", include(router.urls)),  # Include the router URLs
    path("<slug:slug>/", HotelBySlugView.as_view(), name="hotel-by-slug"),  # New slug-based endpoint
]
