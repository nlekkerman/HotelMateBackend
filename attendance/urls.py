# attendance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClockLogViewSet,
    RosterPeriodViewSet,
    StaffRosterViewSet,
    ShiftLocationViewSet,
)
from .views_analytics import RosterAnalyticsViewSet

app_name = "attendance"

# -------------------------
# Routers (ONLY for simple, non-slugged endpoints)
# -------------------------
router = DefaultRouter()
router.register(r'clock-logs', ClockLogViewSet, basename='clock-log')
router.register(r'shift-locations', ShiftLocationViewSet, basename='shift-location')
# Do NOT register RosterAnalyticsViewSet here (it needs hotel_slug in the URL)

# -------------------------
# RosterPeriod explicit bindings
# -------------------------
roster_period_list = RosterPeriodViewSet.as_view({'get': 'list', 'post': 'create'})
roster_period_detail = RosterPeriodViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
roster_add_shift = RosterPeriodViewSet.as_view({'post': 'add_shift'})
roster_create_department = RosterPeriodViewSet.as_view({'post': 'create_department_roster'})
roster_create_for_week = RosterPeriodViewSet.as_view({'post': 'create_for_week'})
roster_period_export_pdf = RosterPeriodViewSet.as_view({'get': 'export_pdf'})

# --------- Staff Roster PDF exports ---------
staff_roster_daily_pdf = StaffRosterViewSet.as_view({'get': 'daily_pdf'})
staff_roster_staff_pdf = StaffRosterViewSet.as_view({'get': 'staff_pdf'})
# -------------------------
# StaffRoster explicit bindings
# -------------------------
staff_roster_list = StaffRosterViewSet.as_view({'get': 'list', 'post': 'create'})
staff_roster_detail = StaffRosterViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
staff_roster_bulk_save = StaffRosterViewSet.as_view({'post': 'bulk_save'})

# -------------------------
# Analytics explicit bindings (need hotel_slug)
# -------------------------
staff_summary = RosterAnalyticsViewSet.as_view({'get': 'staff_summary'})
department_summary = RosterAnalyticsViewSet.as_view({'get': 'department_summary'})
kpis = RosterAnalyticsViewSet.as_view({'get': 'kpis'})

daily_totals = RosterAnalyticsViewSet.as_view({'get': 'daily_totals'})
daily_by_department = RosterAnalyticsViewSet.as_view({'get': 'daily_by_department'})
daily_by_staff = RosterAnalyticsViewSet.as_view({'get': 'daily_by_staff'})

weekly_totals = RosterAnalyticsViewSet.as_view({'get': 'weekly_totals'})
weekly_by_department = RosterAnalyticsViewSet.as_view({'get': 'weekly_by_department'})
weekly_by_staff = RosterAnalyticsViewSet.as_view({'get': 'weekly_by_staff'})

shift_location_list = ShiftLocationViewSet.as_view({'get': 'list', 'post': 'create'})
shift_location_detail = ShiftLocationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
# -------------------------
# URL patterns
# -------------------------
urlpatterns = [
    # Router-mounted (no hotel_slug)
    path('', include(router.urls)),

    # --------- Roster Periods ---------
    path('<slug:hotel_slug>/periods/', roster_period_list, name='roster-period-list'),
    path('<slug:hotel_slug>/periods/<int:pk>/', roster_period_detail, name='roster-period-detail'),
    path('<slug:hotel_slug>/periods/<int:pk>/add-shift/', roster_add_shift, name='roster-add-shift'),
    path('<slug:hotel_slug>/periods/<int:pk>/create-department-roster/', roster_create_department, name='roster-create-department'),
    path('<slug:hotel_slug>/periods/create-for-week/', roster_create_for_week, name='roster-create-for-week'),
    
    # --------- Staff Shifts ---------
    path('<slug:hotel_slug>/shifts/', staff_roster_list, name='staff-roster-list'),
    path('<slug:hotel_slug>/shifts/<int:pk>/', staff_roster_detail, name='staff-roster-detail'),
    path('<slug:hotel_slug>/shifts/bulk-save/', staff_roster_bulk_save, name='staff-roster-bulk-save'),

    # --------- Roster Analytics (slugged) ---------
    path('<slug:hotel_slug>/roster-analytics/staff-summary/', staff_summary, name='ra-staff-summary'),
    path('<slug:hotel_slug>/roster-analytics/department-summary/', department_summary, name='ra-department-summary'),
    path('<slug:hotel_slug>/roster-analytics/kpis/', kpis, name='ra-kpis'),

    path('<slug:hotel_slug>/roster-analytics/daily-totals/', daily_totals, name='ra-daily-totals'),
    path('<slug:hotel_slug>/roster-analytics/daily-by-department/', daily_by_department, name='ra-daily-by-department'),
    path('<slug:hotel_slug>/roster-analytics/daily-by-staff/', daily_by_staff, name='ra-daily-by-staff'),

    path('<slug:hotel_slug>/roster-analytics/weekly-totals/', weekly_totals, name='ra-weekly-totals'),
    path('<slug:hotel_slug>/roster-analytics/weekly-by-department/', weekly_by_department, name='ra-weekly-by-department'),
    path('<slug:hotel_slug>/roster-analytics/weekly-by-staff/', weekly_by_staff, name='ra-weekly-by-staff'),

    path('<slug:hotel_slug>/shift-locations/', shift_location_list, name='shift-location-list'),
    path('<slug:hotel_slug>/shift-locations/<int:pk>/', shift_location_detail, name='shift-location-detail'),

    # --------- Roster Period PDF ---------
path('<slug:hotel_slug>/periods/<int:pk>/export-pdf/', roster_period_export_pdf, name='roster-period-export-pdf'),

# --------- Staff Roster PDFs ---------
path('<slug:hotel_slug>/shifts/daily-pdf/', staff_roster_daily_pdf, name='staff-roster-daily-pdf'),
path('<slug:hotel_slug>/shifts/staff-pdf/', staff_roster_staff_pdf, name='staff-roster-staff-pdf'),


]
