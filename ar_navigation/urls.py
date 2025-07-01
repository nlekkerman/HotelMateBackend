from django.urls import path
from .views import ARNavigationView, ARAnchorDetailView

urlpatterns = [
    path('anchor/<int:id>/', ARAnchorDetailView.as_view(), name='ar-anchor-detail'),

    path('ar-navigation/<slug:hotel_slug>/room/<str:room_number>/', ARNavigationView.as_view(), name='ar-navigation'),
]
