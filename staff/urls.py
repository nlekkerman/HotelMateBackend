from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateStaffAPIView, RegisterNormalUserAPIView, CustomAuthToken, StaffViewSet,UserListAPIView

router = DefaultRouter()
router.register(r'', StaffViewSet, basename='staff')

urlpatterns = [
    path('register/', CreateStaffAPIView.as_view(), name='staff-register'),  # for staff registration
    path('signup/', RegisterNormalUserAPIView.as_view(), name='user-signup'),   # for normal user registration
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('', include(router.urls)),
]
