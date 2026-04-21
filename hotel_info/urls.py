from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HotelInfoViewSet,
    HotelInfoCategoryViewSet,
    HotelInfoCreateView,
    CategoryQRView,
    download_all_qrs,
)

router = DefaultRouter()
router.register(r"hotelinfo", HotelInfoViewSet, basename="hotelinfo")
router.register(r"categories", HotelInfoCategoryViewSet, basename="hotelinfo-category")

urlpatterns = [
    path("", include(router.urls)),
    path("hotelinfo/create/", HotelInfoCreateView.as_view(), name="hotelinfo-create"),
    path("category_qr/", CategoryQRView.as_view(), name="category-qr"),
    path("category_qr/download_all/", download_all_qrs, name="download-all-qrs"),
]
