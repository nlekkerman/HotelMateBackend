from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StaffRegisterAPIView,
    CustomAuthToken,
    StaffViewSet,
    UserListAPIView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    StaffMetadataView,  # ← add this line
)
router = DefaultRouter()
router.register(r'', StaffViewSet, basename='staff')

urlpatterns = [
    path('<slug:hotel_slug>/', include(router.urls)),
    path('register/', StaffRegisterAPIView.as_view(), name='staff-register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('metadata/', StaffMetadataView.as_view(), name='staff-metadata'),
]
