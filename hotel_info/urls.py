# src/apps/hotel_info/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HotelInfoViewSet,
    HotelInfoCategoryViewSet,
    HotelInfoCreateView,
    CategoryQRView,
    GoodToKnowEntryViewSet,
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

    # GoodToKnowEntry CRUD routes with hotel_slug and slug params
    path(
        "good_to_know/<slug:hotel_slug>/",
        GoodToKnowEntryViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="goodtoknow-list-create",
    ),
    path(
        "good_to_know/<slug:hotel_slug>/<slug:slug>/",
        GoodToKnowEntryViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="goodtoknow-detail",
    ),
]
