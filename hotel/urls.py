from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HotelViewSet,
    HotelBySlugView,
    HotelPublicListView,
    HotelPublicDetailView,
    HotelPublicPageView,
    HotelAvailabilityView,
)

# Default router for the main HotelViewSet
router = DefaultRouter()
router.register(r'hotels', HotelViewSet)

urlpatterns = [
    # Public API endpoints for hotel discovery
    path(
        "public/",
        HotelPublicListView.as_view(),
        name="hotel-public-list"
    ),
    path(
        "public/<slug:slug>/",
        HotelPublicDetailView.as_view(),
        name="hotel-public-detail"
    ),
    path(
        "public/page/<slug:slug>/",
        HotelPublicPageView.as_view(),
        name="hotel-public-page"
    ),
    
    # Availability check endpoint
    path(
        "<slug:slug>/availability/",
        HotelAvailabilityView.as_view(),
        name="hotel-availability"
    ),
    
    # Internal/admin endpoints
    path("", include(router.urls)),
    path(
        "<slug:slug>/",
        HotelBySlugView.as_view(),
        name="hotel-by-slug"
    ),
]
