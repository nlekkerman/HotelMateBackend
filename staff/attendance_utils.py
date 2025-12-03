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
    
    # Get clock logs for the period - use prefetched data if available
    if clock_logs is None:
        if hasattr(staff, 'filtered_clock_logs'):
            # Use prefetched filtered data
            clock_logs = [log for log in staff.filtered_clock_logs 
                         if from_date <= log.time_in.date() <= to_date]
        else:
            # Fall back to database query
            clock_logs = ClockLog.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                time_in__date__range=[from_date, to_date]
            )
    
    # Get roster shifts for the period - use prefetched data if available
    if roster_shifts is None:
        if hasattr(staff, 'filtered_roster_entries'):
            # Use prefetched filtered data
            roster_shifts = [shift for shift in staff.filtered_roster_entries
                           if from_date <= shift.shift_date <= to_date]
        else:
            # Fall back to database query
            roster_shifts = StaffRoster.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                shift_date__range=[from_date, to_date]
            )
    
    # Check for active status first (currently clocked in and on duty)
    if hasattr(clock_logs, 'filter'):  # QuerySet
        current_log = clock_logs.filter(time_out__isnull=True).first()
    else:  # List
        current_log = next((log for log in clock_logs if log.time_out is None), None)
    
    if current_log and staff.duty_status == 'on_duty':
        return 'active'
    
    # Check for issues
    if has_attendance_issues(staff, from_date, to_date, clock_logs, roster_shifts):
        return 'issue'
    
    # Check if staff has any completed logs in period
    if hasattr(clock_logs, 'filter'):  # QuerySet
        completed_logs = clock_logs.filter(time_out__isnull=False, is_approved=True)
        has_completed = completed_logs.exists()
        has_logs = clock_logs.exists()
    else:  # List
        completed_logs = [log for log in clock_logs 
                         if log.time_out is not None and log.is_approved]
        has_completed = len(completed_logs) > 0
        has_logs = len(clock_logs) > 0
    
    if has_completed:
        return 'completed'
    
    # Check if staff has roster entries but no logs
    if hasattr(roster_shifts, 'exists'):  # QuerySet
        has_roster = roster_shifts.exists()
    else:  # List
        has_roster = len(roster_shifts) > 0
    
    if has_roster and not has_logs:
        return 'no_log'
    
    # Default case - no roster, no logs, not currently active
    return 'no_log' if has_roster else 'completed'


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
    
    # Get clock logs - handle both querysets and prefetched lists
    if clock_logs is None:
        if hasattr(staff, 'filtered_clock_logs'):
            clock_logs = [log for log in staff.filtered_clock_logs 
                         if from_date <= log.time_in.date() <= to_date]
        else:
            clock_logs = ClockLog.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                time_in__date__range=[from_date, to_date]
            )
    
    # Get roster shifts - handle both querysets and prefetched lists  
    if roster_shifts is None:
        if hasattr(staff, 'filtered_roster_entries'):
            roster_shifts = [shift for shift in staff.filtered_roster_entries
                           if from_date <= shift.shift_date <= to_date]
        else:
            roster_shifts = StaffRoster.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                shift_date__range=[from_date, to_date]
            )
    
    # Helper function to handle both querysets and lists
    def _filter_logs(logs, condition_func):
        if hasattr(logs, 'filter'):  # QuerySet
            return [log for log in logs if condition_func(log)]
        else:  # List
            return [log for log in logs if condition_func(log)]
    
    def _count_items(items):
        if hasattr(items, 'count'):  # QuerySet
            return items.count()
        else:  # List
            return len(items)
    
    # Check for missing time_out (older than 24 hours)
    cutoff_time = now() - timedelta(hours=24)
    open_old_logs = _filter_logs(clock_logs, lambda log: 
        log.time_out is None and log.time_in < cutoff_time)
    if len(open_old_logs) > 0:
        return True
    
    # Check for excessive duration (>16 hours)
    EXCESSIVE_HOURS_THRESHOLD = 16
    excessive_logs = _filter_logs(clock_logs, lambda log:
        log.time_out is not None and log.hours_worked and 
        float(log.hours_worked) > EXCESSIVE_HOURS_THRESHOLD)
    if len(excessive_logs) > 0:
        return True
    
    # Check for rejected logs
    rejected_logs = _filter_logs(clock_logs, lambda log: log.is_rejected)
    if len(rejected_logs) > 0:
        return True
    
    # Check for unapproved unrostered logs
    unapproved_logs = _filter_logs(clock_logs, lambda log: 
        log.is_unrostered and not log.is_approved)
    if len(unapproved_logs) > 0:
        return True
    
    # Check roster vs log completeness (simplified check)
    # If staff has many roster entries but very few logs, flag as issue
    roster_count = _count_items(roster_shifts)
    completed_logs = _filter_logs(clock_logs, lambda log:
        log.time_out is not None and log.is_approved)
    completed_log_count = len(completed_logs)
    
    if roster_count > 0 and completed_log_count < (roster_count * 0.5):  # Less than 50% attendance
        return True
    
    return False


def calculate_worked_minutes(staff, from_date, to_date, clock_logs=None) -> int:
    """
    Calculate total worked minutes for staff in the given date range.
    Only counts approved logs with both time_in and time_out.
    """
    from attendance.models import ClockLog
    from django.db.models import Sum
    
    # Get clock logs - handle both querysets and prefetched lists
    if clock_logs is None:
        if hasattr(staff, 'filtered_clock_logs'):
            clock_logs = [log for log in staff.filtered_clock_logs 
                         if from_date <= log.time_in.date() <= to_date]
        else:
            clock_logs = ClockLog.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                time_in__date__range=[from_date, to_date]
            )
    
    # Calculate total hours
    if hasattr(clock_logs, 'filter'):  # QuerySet
        total_hours = clock_logs.filter(
            time_out__isnull=False,
            is_approved=True,
            hours_worked__isnull=False
        ).aggregate(
            total=Sum('hours_worked')
        )['total']
    else:  # List from prefetched data
        total_hours = sum(
            float(log.hours_worked) for log in clock_logs
            if (log.time_out is not None and 
                log.is_approved and 
                log.hours_worked is not None)
        )
    
    if total_hours:
        return int(float(total_hours) * 60)  # Convert hours to minutes
    
    return 0


def count_planned_shifts(staff, from_date, to_date, roster_shifts=None) -> int:
    """
    Count planned shifts (roster entries) for staff in the given date range.
    """
    from attendance.models import StaffRoster
    
    # Get roster shifts - handle both querysets and prefetched lists
    if roster_shifts is None:
        if hasattr(staff, 'filtered_roster_entries'):
            roster_shifts = [shift for shift in staff.filtered_roster_entries
                           if from_date <= shift.shift_date <= to_date]
        else:
            roster_shifts = StaffRoster.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                shift_date__range=[from_date, to_date]
            )
    
    # Count items - handle both querysets and lists
    if hasattr(roster_shifts, 'count'):
        return roster_shifts.count()
    else:
        return len(roster_shifts)


def count_worked_shifts(staff, from_date, to_date, clock_logs=None) -> int:
    """
    Count completed shifts (approved clock logs) for staff in the given date range.
    """
    from attendance.models import ClockLog
    
    # Get clock logs - handle both querysets and prefetched lists
    if clock_logs is None:
        if hasattr(staff, 'filtered_clock_logs'):
            clock_logs = [log for log in staff.filtered_clock_logs 
                         if from_date <= log.time_in.date() <= to_date]
        else:
            clock_logs = ClockLog.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                time_in__date__range=[from_date, to_date]
            )
    
    # Count completed shifts - handle both querysets and lists
    if hasattr(clock_logs, 'filter'):
        return clock_logs.filter(
            time_out__isnull=False,
            is_approved=True
        ).count()
    else:
        return len([
            log for log in clock_logs 
            if log.time_out is not None and log.is_approved
        ])


def count_attendance_issues(staff, from_date, to_date, clock_logs=None, roster_shifts=None) -> int:
    """
    Count specific attendance issues for staff in the given date range.
    Returns total count of issues found.
    """
    from attendance.models import ClockLog
    
    # Get clock logs - handle both querysets and prefetched lists
    if clock_logs is None:
        if hasattr(staff, 'filtered_clock_logs'):
            clock_logs = [log for log in staff.filtered_clock_logs 
                         if from_date <= log.time_in.date() <= to_date]
        else:
            clock_logs = ClockLog.objects.filter(
                staff=staff,
                hotel=staff.hotel,
                time_in__date__range=[from_date, to_date]
            )
    
    issue_count = 0
    cutoff_time = now() - timedelta(hours=24)
    EXCESSIVE_HOURS_THRESHOLD = 16
    
    # Handle both querysets and lists
    if hasattr(clock_logs, 'filter'):  # QuerySet
        issue_count += clock_logs.filter(
            time_out__isnull=True,
            time_in__lt=cutoff_time
        ).count()
        
        issue_count += clock_logs.filter(
            time_out__isnull=False,
            hours_worked__gt=EXCESSIVE_HOURS_THRESHOLD
        ).count()
        
        issue_count += clock_logs.filter(is_rejected=True).count()
        
        issue_count += clock_logs.filter(
            is_unrostered=True,
            is_approved=False
        ).count()
    else:  # List from prefetched data
        for log in clock_logs:
            # Missing time_out (older than 24 hours)
            if log.time_out is None and log.time_in < cutoff_time:
                issue_count += 1
            
            # Excessive duration (>16 hours)
            if (log.time_out is not None and log.hours_worked and 
                float(log.hours_worked) > EXCESSIVE_HOURS_THRESHOLD):
                issue_count += 1
            
            # Rejected logs
            if log.is_rejected:
                issue_count += 1
            
            # Unapproved unrostered logs
            if log.is_unrostered and not log.is_approved:
                issue_count += 1
    
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
    from django.db.models import Prefetch
    from attendance.models import ClockLog, StaffRoster
    
    # Base optimizations for staff data
    qs = base_queryset.select_related(
        'user', 'hotel', 'department', 'role'
    ).prefetch_related(
        'allowed_navigation_items'
    )
    
    # If date range provided, prefetch filtered attendance data
    if from_date and to_date:
        # Prefetch clock logs for the period using proper Prefetch objects
        clock_logs_prefetch = Prefetch(
            'clocklog_set',
            queryset=ClockLog.objects.filter(
                time_in__date__range=[from_date, to_date]
            ).select_related('roster_shift'),
            to_attr='filtered_clock_logs'
        )
        
        # Prefetch roster shifts for the period
        roster_shifts_prefetch = Prefetch(
            'roster_entries',
            queryset=StaffRoster.objects.filter(
                shift_date__range=[from_date, to_date]
            ).select_related('department', 'period', 'location'),
            to_attr='filtered_roster_entries'
        )
        
        qs = qs.prefetch_related(
            clock_logs_prefetch,
            roster_shifts_prefetch
        )
    else:
        # General prefetch for recent data
        qs = qs.prefetch_related(
            Prefetch(
                'clocklog_set',
                queryset=ClockLog.objects.select_related('roster_shift')
            ),
            Prefetch(
                'roster_entries', 
                queryset=StaffRoster.objects.select_related('department', 'period', 'location')
            )
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