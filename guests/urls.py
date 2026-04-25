from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GuestViewSet

guest_list = GuestViewSet.as_view({'get': 'list'})
guest_detail = GuestViewSet.as_view({'get': 'retrieve', 'put': 'update'})

# Mounted under /api/staff/hotel/<hotel_slug>/guests/ via staff_urls.py.
# The outer wrapper provides the hotel_slug URL kwarg — do NOT add another
# one here (keeps a single canonical /api/staff/hotel/<slug>/guests/ shape).
urlpatterns = [
    path('', guest_list, name='guests-by-hotel'),
    path('<int:pk>/', guest_detail, name='guest-detail'),
]
