from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StaffRegisterAPIView,
    CustomAuthToken,
    StaffViewSet,
    DepartmentViewSet,
    RoleViewSet,
    UserListAPIView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    StaffMetadataView,
    UsersByHotelRegistrationCodeAPIView,
    PendingRegistrationsAPIView,
    CreateStaffFromUserAPIView,
)

# Staff router (hotel-specific)
router = DefaultRouter()
router.register(r'', StaffViewSet, basename='staff')

# Department and Role routers (global)
departments_router = DefaultRouter()
departments_router.register(
    r'departments',
    DepartmentViewSet,
    basename='department'
)

roles_router = DefaultRouter()
roles_router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    # Authentication
    path('login/', CustomAuthToken.as_view(), name='login'),
    path(
        'register/',
        StaffRegisterAPIView.as_view(),
        name='staff-register'
    ),
    
    # Password management
    path(
        'password-reset/',
        PasswordResetRequestView.as_view(),
        name='password-reset'
    ),
    path(
        'password-reset-confirm/',
        PasswordResetConfirmView.as_view(),
        name='password-reset-confirm'
    ),
    
    # User management
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path(
        'users/by-hotel-codes/',
        UsersByHotelRegistrationCodeAPIView.as_view(),
        name='users-by-hotel-codes'
    ),
    
    # Department and Role endpoints
    path('', include(departments_router.urls)),
    path('', include(roles_router.urls)),
    
    # Hotel-specific staff endpoints
    path(
        '<slug:hotel_slug>/metadata/',
        StaffMetadataView.as_view(),
        name='staff-metadata'
    ),
    path(
        '<slug:hotel_slug>/pending-registrations/',
        PendingRegistrationsAPIView.as_view(),
        name='pending-registrations'
    ),
    path(
        '<slug:hotel_slug>/create-staff/',
        CreateStaffFromUserAPIView.as_view(),
        name='create-staff'
    ),
    path('<slug:hotel_slug>/', include(router.urls)),
]
