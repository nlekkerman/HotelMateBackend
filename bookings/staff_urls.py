"""
Staff-specific routing for service bookings.
Phase 4A: URL routing only - no permission changes.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssignGuestToTableAPIView,
    BookingViewSet,
    BookingCategoryViewSet,
    DeleteBookingAPIView,
    RestaurantViewSet,
    RestaurantBlueprintViewSet,
    DiningTableViewSet,
    BlueprintObjectTypeViewSet,
    BlueprintObjectViewSet,
    AvailableTablesView,
    UnseatBookingAPIView,
    mark_bookings_seen
)

# Register viewsets for staff operations
router = DefaultRouter()
router.register(r'bookings', BookingViewSet)
router.register(r'categories', BookingCategoryViewSet)
router.register(
    r'blueprint-object-types',
    BlueprintObjectTypeViewSet,
    basename='blueprint-object-type'
)
# Register restaurant viewset properly
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')

# Staff management views with hotel_slug parameter
restaurant_list_create = RestaurantViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

restaurant_detail = RestaurantViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

blueprint_list = RestaurantBlueprintViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

blueprint_detail = RestaurantBlueprintViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

dining_table_list = DiningTableViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

dining_table_detail = DiningTableViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

# Blueprint objects nested under blueprint
blueprint_objects = BlueprintObjectViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

blueprint_object_detail = BlueprintObjectViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'put': 'update',
    'delete': 'destroy'
})

urlpatterns = [
    # Include router-generated URLs for staff operations
    path('', include(router.urls)),
    
    # Restaurant management
    path(
        'restaurants/',
        restaurant_list_create,
        name='staff-restaurant-list-create'
    ),
    path(
        'restaurants/<str:slug>/',
        restaurant_detail,
        name='staff-restaurant-detail'
    ),
    
    # Blueprint management
    path(
        'blueprint/<str:slug>/',
        blueprint_list,
        name='staff-blueprint-list'
    ),
    path(
        'blueprint/<str:slug>/<int:pk>/',
        blueprint_detail,
        name='staff-blueprint-detail'
    ),

    # Dining table management
    path(
        'tables/<str:slug>/',
        dining_table_list,
        name='staff-dining-table-list'
    ),
    path(
        'tables/<str:slug>/<int:id>/',
        dining_table_detail,
        name='staff-dining-table-detail'
    ),
    
    # Blueprint objects management
    path(
        'blueprint/<str:slug>/<int:blueprint_id>/objects/',
        blueprint_objects,
        name='staff-blueprint-objects-list'
    ),
    path(
        'blueprint/<str:slug>/<int:blueprint_id>/objects/<int:pk>/',
        blueprint_object_detail,
        name='staff-blueprint-object-detail'
    ),
    
    # Staff action endpoints
    path(
        'available-tables/<str:slug>/',
        AvailableTablesView.as_view(),
        name='staff-available-tables'
    ),
    path(
        'mark-seen/',
        mark_bookings_seen,
        name='staff-mark-bookings-seen'
    ),
    path(
        'assign/<str:slug>/',
        AssignGuestToTableAPIView.as_view(),
        name='staff-assign-guest-to-table'
    ),
    path(
        'unseat/<str:slug>/',
        UnseatBookingAPIView.as_view(),
        name='staff-unseat-guest-from-table'
    ),
    path(
        'delete/<str:slug>/<int:booking_id>/',
        DeleteBookingAPIView.as_view(),
        name='staff-delete-booking'
    ),
]