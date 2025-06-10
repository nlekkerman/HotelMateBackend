# src/apps/hotel_info/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  (
    HotelInfoViewSet,
    HotelInfoCategoryViewSet,
    HotelInfoCreateView,
    CategoryQRView,
)

router = DefaultRouter()
router.register(r"hotelinfo",        HotelInfoViewSet,         basename="hotelinfo")
router.register(r"categories",       HotelInfoCategoryViewSet, basename="hotelinfo-category")

urlpatterns = [
    path("", include(router.urls)),
    path("hotelinfo/create/", HotelInfoCreateView.as_view(), name="hotelinfo-create"),
    path("category_qr/", CategoryQRView.as_view(), name="category-qr"),
]
