from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GuestViewSet

guest_list = GuestViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('<str:hotel_slug>/guests/', guest_list, name='guests-by-hotel'),
]
