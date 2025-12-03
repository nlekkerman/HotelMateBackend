"""
Attendance utilities for Staff model enhancements.
Provides helper functions for attendance status calculation, worked hours analysis,
issue detection, and status badge logic for the attendance dashboard.
"""
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.db.models import Q, Sum, Count, Avg
from typing import Dict, Any, Optional, List


def calculate_attendance_status(staff, from_date, to_date, clock_logs=None, roster_shifts=None) -> str:
    """
    Calculate attendance_status for a staff member in the given date range.
    
    Returns one of: 'active', 'completed', 'no_log', 'issue'
    
    Args:
        staff: Staff instance
        from_date: Start date (datetime.date)
        to_date: End date (datetime.date) 
        clock_logs: Optional pre-fetched ClockLog queryset for optimization
        roster_shifts: Optional pre-fetched StaffRoster queryset for optimization
    """
    from attendance.models import ClockLog, StaffRoster
    
    # Get clock logs for the period if not provided
    if clock_logs is None:
        clock_logs = ClockLog.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            time_in__date__range=[from_date, to_date]
        )
    
    # Get roster shifts for the period if not provided  
    if roster_shifts is None:
        roster_shifts = StaffRoster.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            shift_date__range=[from_date, to_date]
        )
    
    # Check for active status first (currently clocked in and on duty)
    current_log = clock_logs.filter(time_out__isnull=True).first()
    if current_log and staff.duty_status == 'on_duty':
        return 'active'
    
    # Check for issues
    if has_attendance_issues(staff, from_date, to_date, clock_logs, roster_shifts):
        return 'issue'
    
    # Check if staff has any completed logs in period
    completed_logs = clock_logs.filter(time_out__isnull=False, is_approved=True)
    if completed_logs.exists():
        return 'completed'
    
    # Check if staff has roster entries but no logs
    if roster_shifts.exists() and not clock_logs.exists():
        return 'no_log'
    
    # Default case - no roster, no logs, not currently active
    return 'no_log' if roster_shifts.exists() else 'completed'


def has_attendance_issues(staff, from_date, to_date, clock_logs=None, roster_shifts=None) -> bool:
    """
    Detect if staff has attendance issues in the given period.
    
    Issues include:
    - Missing time_out (open sessions older than 24 hours)
    - Excessive duration (>16 hours in single session) 
    - Roster planned but logs incomplete/missing
    - Rejected or unapproved unrostered logs
    """
    from attendance.models import ClockLog, StaffRoster
    
    if clock_logs is None:
        clock_logs = ClockLog.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            time_in__date__range=[from_date, to_date]
        )
    
    if roster_shifts is None:
        roster_shifts = StaffRoster.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            shift_date__range=[from_date, to_date]
        )
    
    # Check for missing time_out (older than 24 hours)
    cutoff_time = now() - timedelta(hours=24)
    open_old_logs = clock_logs.filter(
        time_out__isnull=True,
        time_in__lt=cutoff_time
    )
    if open_old_logs.exists():
        return True
    
    # Check for excessive duration (>16 hours)
    EXCESSIVE_HOURS_THRESHOLD = 16
    for log in clock_logs.filter(time_out__isnull=False):
        if log.hours_worked and float(log.hours_worked) > EXCESSIVE_HOURS_THRESHOLD:
            return True
    
    # Check for rejected logs
    if clock_logs.filter(is_rejected=True).exists():
        return True
    
    # Check for unapproved unrostered logs
    if clock_logs.filter(is_unrostered=True, is_approved=False).exists():
        return True
    
    # Check roster vs log completeness (simplified check)
    # If staff has many roster entries but very few logs, flag as issue
    roster_count = roster_shifts.count()
    completed_log_count = clock_logs.filter(time_out__isnull=False, is_approved=True).count()
    
    if roster_count > 0 and completed_log_count < (roster_count * 0.5):  # Less than 50% attendance
        return True
    
    return False


def calculate_worked_minutes(staff, from_date, to_date, clock_logs=None) -> int:
    """
    Calculate total worked minutes for staff in the given date range.
    Only counts approved logs with both time_in and time_out.
    """
    from attendance.models import ClockLog
    
    if clock_logs is None:
        clock_logs = ClockLog.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            time_in__date__range=[from_date, to_date]
        )
    
    # Sum hours_worked field and convert to minutes
    total_hours = clock_logs.filter(
        time_out__isnull=False,
        is_approved=True,
        hours_worked__isnull=False
    ).aggregate(
        total=Sum('hours_worked')
    )['total']
    
    if total_hours:
        return int(float(total_hours) * 60)  # Convert hours to minutes
    
    return 0


def count_planned_shifts(staff, from_date, to_date, roster_shifts=None) -> int:
    """
    Count planned shifts (roster entries) for staff in the given date range.
    """
    from attendance.models import StaffRoster
    
    if roster_shifts is None:
        roster_shifts = StaffRoster.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            shift_date__range=[from_date, to_date]
        )
    
    return roster_shifts.count()


def count_worked_shifts(staff, from_date, to_date, clock_logs=None) -> int:
    """
    Count completed shifts (approved clock logs) for staff in the given date range.
    """
    from attendance.models import ClockLog
    
    if clock_logs is None:
        clock_logs = ClockLog.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            time_in__date__range=[from_date, to_date]
        )
    
    return clock_logs.filter(
        time_out__isnull=False,
        is_approved=True
    ).count()


def count_attendance_issues(staff, from_date, to_date, clock_logs=None, roster_shifts=None) -> int:
    """
    Count specific attendance issues for staff in the given date range.
    Returns total count of issues found.
    """
    from attendance.models import ClockLog
    
    if clock_logs is None:
        clock_logs = ClockLog.objects.filter(
            staff=staff,
            hotel=staff.hotel,
            time_in__date__range=[from_date, to_date]
        )
    
    issue_count = 0
    
    # Count missing time_out (older than 24 hours)
    cutoff_time = now() - timedelta(hours=24)
    issue_count += clock_logs.filter(
        time_out__isnull=True,
        time_in__lt=cutoff_time
    ).count()
    
    # Count excessive duration logs (>16 hours)
    EXCESSIVE_HOURS_THRESHOLD = 16
    excessive_logs = clock_logs.filter(
        time_out__isnull=False,
        hours_worked__gt=EXCESSIVE_HOURS_THRESHOLD
    )
    issue_count += excessive_logs.count()
    
    # Count rejected logs
    issue_count += clock_logs.filter(is_rejected=True).count()
    
    # Count unapproved unrostered logs
    issue_count += clock_logs.filter(
        is_unrostered=True,
        is_approved=False
    ).count()
    
    return issue_count


def get_status_badge_info(duty_status: str) -> Dict[str, Any]:
    """
    Get consistent status badge information for UI rendering.
    Maps duty_status to colors, labels, and icons for frontend consistency.
    """
    badge_map = {
        'on_duty': {
            'label': 'On Duty',
            'color': 'success',
            'bg_color': '#28a745',
            'text_color': '#ffffff',
            'icon': 'clock',
            'status_type': 'active'
        },
        'off_duty': {
            'label': 'Off Duty',
            'color': 'secondary',
            'bg_color': '#6c757d',
            'text_color': '#ffffff',
            'icon': 'clock-slash',
            'status_type': 'inactive'
        },
        'on_break': {
            'label': 'On Break',
            'color': 'warning',
            'bg_color': '#ffc107',
            'text_color': '#000000',
            'icon': 'coffee',
            'status_type': 'break'
        }
    }
    
    return badge_map.get(duty_status, badge_map['off_duty'])


def get_attendance_status_badge_info(attendance_status: str) -> Dict[str, Any]:
    """
    Get badge information for attendance_status field.
    Used in attendance dashboard for visual indicators.
    """
    badge_map = {
        'active': {
            'label': 'Currently Active',
            'color': 'success',
            'bg_color': '#28a745',
            'text_color': '#ffffff',
            'icon': 'user-clock',
            'priority': 1
        },
        'completed': {
            'label': 'Completed Shifts',
            'color': 'primary',
            'bg_color': '#007bff',
            'text_color': '#ffffff',
            'icon': 'check-circle',
            'priority': 2
        },
        'no_log': {
            'label': 'No Attendance',
            'color': 'light',
            'bg_color': '#f8f9fa',
            'text_color': '#6c757d',
            'icon': 'clock-slash',
            'priority': 4
        },
        'issue': {
            'label': 'Has Issues',
            'color': 'danger',
            'bg_color': '#dc3545',
            'text_color': '#ffffff',
            'icon': 'exclamation-triangle',
            'priority': 3
        }
    }
    
    return badge_map.get(attendance_status, badge_map['no_log'])


def optimize_attendance_queryset(base_queryset, from_date=None, to_date=None):
    """
    Optimize staff queryset with attendance-related prefetching for dashboard performance.
    
    Args:
        base_queryset: Staff queryset to optimize
        from_date: Optional date range start
        to_date: Optional date range end
    
    Returns:
        Optimized queryset with prefetched relations
    """
    # Base optimizations for staff data
    qs = base_queryset.select_related(
        'user', 'hotel', 'department', 'role'
    ).prefetch_related(
        'allowed_navigation_items'
    )
    
    # If date range provided, prefetch filtered attendance data
    if from_date and to_date:
        # Prefetch clock logs for the period
        clock_logs_filter = Q(
            time_in__date__range=[from_date, to_date]
        )
        
        # Prefetch roster shifts for the period  
        roster_shifts_filter = Q(
            shift_date__range=[from_date, to_date]
        )
        
        qs = qs.prefetch_related(
            f'clocklog_set__filter({clock_logs_filter})',
            f'roster_entries__filter({roster_shifts_filter})'
        )
    else:
        # General prefetch for recent data
        qs = qs.prefetch_related(
            'clocklog_set',
            'roster_entries'
        )
    
    return qs


# Status constants for easy reference
ATTENDANCE_STATUS_CHOICES = [
    ('active', 'Currently Active'),
    ('completed', 'Completed Shifts'), 
    ('no_log', 'No Attendance'),
    ('issue', 'Has Issues'),
]

DUTY_STATUS_LABELS = {
    'on_duty': 'On Duty',
    'off_duty': 'Off Duty',
    'on_break': 'On Break',
}