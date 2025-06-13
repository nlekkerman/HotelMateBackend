from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GuestViewSet

guest_list = GuestViewSet.as_view({'get': 'list'})
guest_detail = GuestViewSet.as_view({'get': 'retrieve', 'put': 'update'})

urlpatterns = [
    path('<str:hotel_slug>/guests/', guest_list, name='guests-by-hotel'),
    path('<str:hotel_slug>/guests/<int:pk>/', guest_detail, name='guest-detail'),
   
    ]
