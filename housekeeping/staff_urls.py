"""
Housekeeping Staff URLs

Staff-authenticated URL patterns for housekeeping endpoints.
These URLs are included in the main staff routing under /api/staff/hotel/{hotel_slug}/housekeeping/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    HousekeepingDashboardViewSet,
    HousekeepingTaskViewSet,
    RoomStatusViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'tasks', HousekeepingTaskViewSet, basename='housekeeping-tasks')

# Define URL patterns
urlpatterns = [
    # Dashboard endpoint
    path('dashboard/', 
         HousekeepingDashboardViewSet.as_view({'get': 'list'}), 
         name='housekeeping-dashboard'),
    
    # Include router URLs for tasks
    path('', include(router.urls)),
    
    # Room status management endpoints
    path('rooms/<int:room_id>/status/', 
         RoomStatusViewSet.as_view({'post': 'update_status'}), 
         name='room-status-update'),
    
    path('rooms/<int:room_id>/status-history/', 
         RoomStatusViewSet.as_view({'get': 'status_history'}), 
         name='room-status-history'),
]

# URL patterns will resolve to:
# /api/staff/hotel/{hotel_slug}/housekeeping/dashboard/
# /api/staff/hotel/{hotel_slug}/housekeeping/tasks/
# /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{id}/
# /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{id}/assign/
# /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{id}/start/
# /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{id}/complete/
# /api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/status/
# /api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/status-history/
