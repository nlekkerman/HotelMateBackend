from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ClockLogViewSet, RosterPeriodViewSet, StaffRosterViewSet

# DRF Router for clock logs
router = DefaultRouter()
router.register('clock-logs', ClockLogViewSet, basename='clock-log')

# Explicit method bindings for RosterPeriod
roster_period_list = RosterPeriodViewSet.as_view({'get': 'list', 'post': 'create'})
roster_period_detail = RosterPeriodViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
roster_add_shift = RosterPeriodViewSet.as_view({'post': 'add_shift'})
roster_create_department = RosterPeriodViewSet.as_view({'post': 'create_department_roster'})
roster_create_for_week = RosterPeriodViewSet.as_view({'post': 'create_for_week'})  # 🔥 NEW

# Explicit method bindings for StaffRoster
staff_roster_list = StaffRosterViewSet.as_view({'get': 'list', 'post': 'create'})
staff_roster_detail = StaffRosterViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
staff_roster_bulk_save = StaffRosterViewSet.as_view({'post': 'bulk_save'})  # ✅ NEW for batch-saving shifts

urlpatterns = [
    # Clock logs router endpoints
    *router.urls,

    # Roster Periods
    path('<slug:hotel_slug>/periods/', roster_period_list, name='roster-period-list'),
    path('<slug:hotel_slug>/periods/<int:pk>/', roster_period_detail, name='roster-period-detail'),
    path('<slug:hotel_slug>/periods/<int:pk>/add-shift/', roster_add_shift, name='roster-add-shift'),
    path('<slug:hotel_slug>/periods/<int:pk>/create-department-roster/', roster_create_department, name='roster-create-department'),
    path('<slug:hotel_slug>/periods/create-for-week/', roster_create_for_week, name='roster-create-for-week'),

    # Staff Shifts
    path('<slug:hotel_slug>/shifts/', staff_roster_list, name='staff-roster-list'),
    path('<slug:hotel_slug>/shifts/<int:pk>/', staff_roster_detail, name='staff-roster-detail'),
    path('<slug:hotel_slug>/shifts/bulk-save/', staff_roster_bulk_save, name='staff-roster-bulk-save'),  # ✅ FINAL ADDITION
]
