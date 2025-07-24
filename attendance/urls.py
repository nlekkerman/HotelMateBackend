from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ClockLogViewSet, RosterPeriodViewSet, StaffRosterViewSet

# Standard router for face clocking
router = DefaultRouter()
router.register('clock-logs', ClockLogViewSet, basename='clock-log')

# Explicit view mappings for rostering via hotel_slug
roster_period_list = RosterPeriodViewSet.as_view({'get': 'list', 'post': 'create'})
roster_period_detail = RosterPeriodViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
roster_add_shift = RosterPeriodViewSet.as_view({'post': 'add_shift'})

staff_roster_list = StaffRosterViewSet.as_view({'get': 'list', 'post': 'create'})
staff_roster_detail = StaffRosterViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})

urlpatterns = [
    # Default routes (e.g., face register/clock-in/etc)
    *router.urls,

    # Scoped by hotel_slug
    path('<slug:hotel_slug>/periods/', roster_period_list, name='roster-period-list'),
    path('<slug:hotel_slug>/periods/<int:pk>/', roster_period_detail, name='roster-period-detail'),
    path('<slug:hotel_slug>/periods/<int:pk>/add-shift/', roster_add_shift, name='roster-add-shift'),

    path('<slug:hotel_slug>/shifts/', staff_roster_list, name='staff-roster-list'),
    path('<slug:hotel_slug>/shifts/<int:pk>/', staff_roster_detail, name='staff-roster-detail'),
]
