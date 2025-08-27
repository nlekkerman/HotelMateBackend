from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BookingViewSet,
    BookingCategoryViewSet,
    GuestDinnerBookingView,
    RestaurantViewSet,
    RestaurantBlueprintViewSet,
    DiningTableViewSet,
    BlueprintObjectTypeViewSet,
    BlueprintObjectViewSet,
    AvailableTablesView,
    mark_bookings_seen
)

# Register viewsets to the router
router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'categories', BookingCategoryViewSet)
router.register(r'blueprint-object-types', BlueprintObjectTypeViewSet, basename='blueprint-object-type')  # ← add here

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
    # Include router-generated URLs (e.g. /bookings/, /categories/)
    path('', include(router.urls)),
    path(
        '<str:hotel_slug>/<str:restaurant_slug>/blueprint/<int:blueprint_id>/objects/',
        blueprint_objects,
        name='blueprint-objects-list'
    ),
    path(
        '<str:hotel_slug>/<str:restaurant_slug>/blueprint/<int:blueprint_id>/objects/<int:pk>/',
        blueprint_object_detail,
        name='blueprint-object-detail'
    ),
    # Public guest dinner booking route (QR form submission)
    path(
        'guest-booking/<str:hotel_slug>/restaurant/<str:restaurant_slug>/room/<str:room_number>/',
        GuestDinnerBookingView.as_view(),
        name='guest-dinner-booking'
    ),
    path(
        'guest-booking/<str:hotel_slug>/restaurant/<str:restaurant_slug>/',
        GuestDinnerBookingView.as_view(),
        name='guest-dinner-booking-list'
    ),

    # Blueprint routes
    path('<slug:hotel_slug>/<slug:restaurant_slug>/blueprint/', blueprint_list, name='blueprint-list'),
    path('<slug:hotel_slug>/<slug:restaurant_slug>/blueprint/<int:pk>/', blueprint_detail, name='blueprint-detail'),

    # Dining table routes
    path('<slug:hotel_slug>/<slug:restaurant_slug>/tables/', dining_table_list, name='dining-table-list'),
    path('<slug:hotel_slug>/<slug:restaurant_slug>/tables/<int:id>/', dining_table_detail, name='dining-table-detail'),

    path(
        'available-tables/<str:hotel_slug>/<str:restaurant_slug>/',
        AvailableTablesView.as_view(),
        name='available-tables'
    ),
    path(
        'bookings/mark-seen/<str:hotel_slug>/',
        mark_bookings_seen,
        name='mark-bookings-seen'
    ),
]
