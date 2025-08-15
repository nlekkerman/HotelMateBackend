from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StaffRegisterAPIView,
    CustomAuthToken,
    StaffViewSet,
    UserListAPIView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    StaffMetadataView,
    UsersByHotelRegistrationCodeAPIView,
    
)
router = DefaultRouter()
router.register(r'', StaffViewSet, basename='staff')

urlpatterns = [
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('register/', StaffRegisterAPIView.as_view(), name='staff-register'),
    path('users/by-hotel-codes/', UsersByHotelRegistrationCodeAPIView.as_view(), name='users-by-hotel-codes'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('<slug:hotel_slug>/metadata/', StaffMetadataView.as_view(), name='staff-metadata'),
    path('<slug:hotel_slug>/', include(router.urls)),
    

]
