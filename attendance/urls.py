# attendance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ClockLogViewSet,
    RosterPeriodViewSet,
    StaffRosterViewSet,
    ShiftLocationViewSet,
    DailyPlanViewSet,
    DailyPlanEntryViewSet,
    CopyRosterViewSet, 
)
from .views_analytics import RosterAnalyticsViewSet
from .face_views import (
    FaceManagementViewSet, 
    force_clock_in_unrostered,
    confirm_clock_out_view,
    toggle_break_view
)

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
roster_period_finalize = RosterPeriodViewSet.as_view({'post': 'finalize_period'})
roster_period_unfinalize = RosterPeriodViewSet.as_view({'post': 'unfinalize_period'})
roster_period_finalization_status = RosterPeriodViewSet.as_view({'get': 'finalization_status'})
roster_period_finalized_rosters = RosterPeriodViewSet.as_view({'get': 'finalized_rosters_by_department'})

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

daily_plan_list = DailyPlanViewSet.as_view({'get': 'list', 'post': 'create'})
daily_plan_detail = DailyPlanViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
daily_plan_entry_list = DailyPlanEntryViewSet.as_view({'get': 'list', 'post': 'create'})
daily_plan_entry_detail = DailyPlanEntryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
prepare_daily_plan = DailyPlanViewSet.as_view({'get': 'prepare_daily_plan'})
download_daily_plan_pdf = DailyPlanViewSet.as_view({'get': 'download_pdf'})


# --------- Copy Operations ---------
copy_roster_bulk = CopyRosterViewSet.as_view({'post': 'copy_roster_bulk'})
copy_roster_day_all = CopyRosterViewSet.as_view({'post': 'copy_roster_day_all'})
copy_week_staff = CopyRosterViewSet.as_view({'post': 'copy_week_staff'})
copy_entire_period = CopyRosterViewSet.as_view({'post': 'copy_entire_period'})

# --------- Period Management ---------
roster_create_custom = RosterPeriodViewSet.as_view({'post': 'create_custom_period'})
roster_duplicate_period = RosterPeriodViewSet.as_view({'post': 'duplicate_period'})

# --------- Face Management ---------
face_register = FaceManagementViewSet.as_view({'post': 'register_face'})
face_revoke = FaceManagementViewSet.as_view({'post': 'revoke_face'})
face_list = FaceManagementViewSet.as_view({'get': 'list_faces'})
face_clock_in = FaceManagementViewSet.as_view({'post': 'face_clock_in'})
face_audit_logs = FaceManagementViewSet.as_view({'get': 'audit_logs'})
face_status = FaceManagementViewSet.as_view({'get': 'face_status'})

# -------------------------
# URL patterns
# -------------------------
urlpatterns = [
    # Router-mounted (no hotel_slug)
    path('', include(router.urls)),

    # --------- Roster Periods ---------
    path('roster-periods/', roster_period_list, name='roster-period-list'),
    path('roster-periods/<int:pk>/', roster_period_detail, name='roster-period-detail'),
    path('roster-periods/<int:pk>/add-shift/', roster_add_shift, name='roster-add-shift'),
    path('roster-periods/<int:pk>/create-department-roster/', roster_create_department, name='roster-create-department'),
    path('roster-periods/<int:pk>/finalize/', roster_period_finalize, name='roster-period-finalize'),
    path('roster-periods/<int:pk>/unfinalize/', roster_period_unfinalize, name='roster-period-unfinalize'),
    path('roster-periods/<int:pk>/finalization-status/', roster_period_finalization_status, name='roster-period-finalization-status'),
    path('roster-periods/<int:pk>/finalized-rosters/', roster_period_finalized_rosters, name='roster-period-finalized-rosters'),
    path('roster-periods/create-for-week/', roster_create_for_week, name='roster-create-for-week'),
    
    # --------- Staff Shifts ---------
    path('shifts/', staff_roster_list, name='staff-roster-list'),
    path('shifts/<int:pk>/', staff_roster_detail, name='staff-roster-detail'),
    path('shifts/bulk-save/', staff_roster_bulk_save, name='staff-roster-bulk-save'),

    # --------- Roster Analytics ---------
    path('roster-analytics/staff-summary/', staff_summary, name='ra-staff-summary'),
    path('roster-analytics/department-summary/', department_summary, name='ra-department-summary'),
    path('roster-analytics/kpis/', kpis, name='ra-kpis'),

    path('roster-analytics/daily-totals/', daily_totals, name='ra-daily-totals'),
    path('roster-analytics/daily-by-department/', daily_by_department, name='ra-daily-by-department'),
    path('roster-analytics/daily-by-staff/', daily_by_staff, name='ra-daily-by-staff'),

    path('roster-analytics/weekly-totals/', weekly_totals, name='ra-weekly-totals'),
    path('roster-analytics/weekly-by-department/', weekly_by_department, name='ra-weekly-by-department'),
    path('roster-analytics/weekly-by-staff/', weekly_by_staff, name='ra-weekly-by-staff'),

    path('shift-locations/', shift_location_list, name='shift-location-list'),
    path('shift-locations/<int:pk>/', shift_location_detail, name='shift-location-detail'),

        # --------- Roster Period PDF ---------
    path('periods/<int:pk>/export-pdf/', roster_period_export_pdf, name='roster-period-export-pdf'),

    # --------- Staff Roster PDFs ---------
    path('shifts/daily-pdf/', staff_roster_daily_pdf, name='staff-roster-daily-pdf'),
    path('shifts/staff-pdf/', staff_roster_staff_pdf, name='staff-roster-staff-pdf'),

    # Daily Plans for a hotel
    path('daily-plans/', daily_plan_list, name='daily-plan-list'),
    path('daily-plans/<int:pk>/', daily_plan_detail, name='daily-plan-detail'),

    # Nested Daily Plan Entries under a Daily Plan
    path('departments/<slug:department_slug>/daily-plans/', daily_plan_list, name='daily-plan-by-department-list'),
    path('daily-plans/<int:daily_plan_pk>/entries/<int:pk>/', daily_plan_entry_detail, name='daily-plan-entry-detail'),
    path(
        'departments/<slug:department_slug>/daily-plans/prepare-daily-plan/',
        prepare_daily_plan,
        name='prepare-daily-plan'
    ),
    path(
        'departments/<slug:department_slug>/daily-plans/download-pdf/',
        download_daily_plan_pdf,
        name='daily-plan-download-pdf',
    ),
    
    # --------- Shift Copy Endpoints ---------
    path('shift-copy/copy-roster-day-all/', copy_roster_day_all, name='copy-roster-day-all'),
    path('shift-copy/copy-roster-bulk/', copy_roster_bulk, name='copy-roster-bulk'),
    path('shift-copy/copy-week-staff/', copy_week_staff, name='copy-week-staff'),
    path('shift-copy/copy-entire-period/', copy_entire_period, name='copy-entire-period'),
    
    # --------- Enhanced Period Management ---------
    path('periods/create-custom-period/', roster_create_custom, name='roster-create-custom'),
    path('periods/<int:pk>/duplicate-period/', roster_duplicate_period, name='roster-duplicate-period'),
    
    # --------- Face Management Endpoints ---------
    path('face-management/register-face/', face_register, name='face-register'),
    path('face-management/revoke-face/', face_revoke, name='face-revoke'),
    path('face-management/list-faces/', face_list, name='face-list'),
    path('face-management/face-clock-in/', face_clock_in, name='face-clock-in'),
    path('face-management/force-clock-in/', force_clock_in_unrostered, name='force-clock-in'),
    path('face-management/confirm-clock-out/', confirm_clock_out_view, name='confirm-clock-out'),
    path('face-management/toggle-break/', toggle_break_view, name='toggle-break'),
    path('face-management/audit-logs/', face_audit_logs, name='face-audit-logs'),
    path('face-management/face-status/', face_status, name='face-status'),
]
