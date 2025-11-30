"""
Attendance system utilities for Phase 4 implementation.
Includes attendance settings helpers and break/overtime alert system.
"""

from django.utils.timezone import now
from chat.utils import pusher_client


def get_attendance_settings(hotel):
    """
    Get or create AttendanceSettings for a hotel with sane defaults.
    
    Args:
        hotel: Hotel instance
        
    Returns:
        AttendanceSettings instance
    """
    from hotel.models import AttendanceSettings
    
    settings, created = AttendanceSettings.objects.get_or_create(
        hotel=hotel,
        defaults={
            'break_warning_hours': 6.0,
            'overtime_warning_hours': 10.0,
            'hard_limit_hours': 12.0,
            'enforce_limits': True,
        }
    )
    return settings


def check_open_log_alerts_for_hotel(hotel):
    """
    Check all open ClockLogs (no time_out) for this hotel and send alerts
    based on AttendanceSettings thresholds.
    
    This function should be called periodically (e.g., every 5-10 minutes)
    by a Celery task or management command.
    
    Args:
        hotel: Hotel instance
        
    Returns:
        dict: Summary of alerts sent
    """
    from .models import ClockLog
    
    settings = get_attendance_settings(hotel)
    current = now()
    
    # Only check logs that are approved and not rejected
    open_logs = ClockLog.objects.filter(
        hotel=hotel,
        time_out__isnull=True,
        is_approved=True,
        is_rejected=False,
    ).select_related('staff')
    
    alerts_sent = {
        'break_warnings': 0,
        'overtime_warnings': 0,
        'hard_limit_warnings': 0,
    }
    
    for log in open_logs:
        duration_hours = (current - log.time_in).total_seconds() / 3600
        
        # Break warning
        if (
            settings.enforce_limits
            and settings.break_warning_hours
            and not log.break_warning_sent
            and duration_hours >= float(settings.break_warning_hours)
        ):
            send_break_warning(hotel, log, duration_hours)
            log.break_warning_sent = True
            log.save(update_fields=['break_warning_sent'])
            alerts_sent['break_warnings'] += 1
        
        # Overtime warning
        if (
            settings.enforce_limits
            and settings.overtime_warning_hours
            and not log.overtime_warning_sent
            and duration_hours >= float(settings.overtime_warning_hours)
        ):
            send_overtime_warning(hotel, log, duration_hours)
            log.overtime_warning_sent = True
            log.save(update_fields=['overtime_warning_sent'])
            alerts_sent['overtime_warnings'] += 1
        
        # Hard limit warning
        if (
            settings.enforce_limits
            and settings.hard_limit_hours
            and not log.hard_limit_warning_sent
            and duration_hours >= float(settings.hard_limit_hours)
        ):
            send_hard_limit_warning(hotel, log, duration_hours)
            log.hard_limit_warning_sent = True
            log.save(update_fields=['hard_limit_warning_sent'])
            alerts_sent['hard_limit_warnings'] += 1
    
    return alerts_sent


def send_break_warning(hotel, clock_log, duration_hours):
    """
    Send a break reminder notification via Pusher.
    
    Args:
        hotel: Hotel instance
        clock_log: ClockLog instance
        duration_hours: Current shift duration in hours
    """
    event_data = {
        'type': 'break_warning',
        'clock_log_id': clock_log.id,
        'staff_id': clock_log.staff.id,
        'staff_name': f"{clock_log.staff.first_name} {clock_log.staff.last_name}",
        'duration_hours': round(duration_hours, 2),
        'message': f"Break reminder: You've been working for {duration_hours:.1f} hours. Consider taking a break.",
        'timestamp': now().isoformat(),
    }
    
    # Send to staff-specific channel
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        event='break-warning',
        data=event_data
    )
    
    # Also send to managers channel for oversight
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-managers",
        event='staff-break-warning',
        data=event_data
    )


def send_overtime_warning(hotel, clock_log, duration_hours):
    """
    Send an overtime warning notification via Pusher.
    
    Args:
        hotel: Hotel instance
        clock_log: ClockLog instance
        duration_hours: Current shift duration in hours
    """
    event_data = {
        'type': 'overtime_warning',
        'clock_log_id': clock_log.id,
        'staff_id': clock_log.staff.id,
        'staff_name': f"{clock_log.staff.first_name} {clock_log.staff.last_name}",
        'duration_hours': round(duration_hours, 2),
        'message': f"Long shift alert: You've been working for {duration_hours:.1f} hours. Monitor your wellbeing.",
        'timestamp': now().isoformat(),
    }
    
    # Send to staff-specific channel
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        event='overtime-warning',
        data=event_data
    )
    
    # Send to managers channel for oversight
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-managers",
        event='staff-overtime-warning',
        data=event_data
    )


def send_hard_limit_warning(hotel, clock_log, duration_hours):
    """
    Send a hard limit warning notification via Pusher.
    Staff must choose to stay clocked in or clock out.
    
    Args:
        hotel: Hotel instance
        clock_log: ClockLog instance
        duration_hours: Current shift duration in hours
    """
    event_data = {
        'type': 'hard_limit_warning',
        'clock_log_id': clock_log.id,
        'staff_id': clock_log.staff.id,
        'staff_name': f"{clock_log.staff.first_name} {clock_log.staff.last_name}",
        'duration_hours': round(duration_hours, 2),
        'message': f"Maximum shift duration reached: {duration_hours:.1f} hours. Please choose to continue or clock out.",
        'actions': [
            {
                'label': 'Continue Working',
                'action': 'stay_clocked_in',
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/stay-clocked-in/',
            },
            {
                'label': 'Clock Out Now',
                'action': 'force_clock_out',
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/force-clock-out/',
            }
        ],
        'timestamp': now().isoformat(),
    }
    
    # Send to staff-specific channel
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        event='hard-limit-warning',
        data=event_data
    )
    
    # Send to managers channel for urgent oversight
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-managers",
        event='staff-hard-limit-warning',
        data=event_data
    )


def send_unrostered_request_notification(hotel, clock_log):
    """
    Send notification to managers about an unrostered clock-in request.
    
    Args:
        hotel: Hotel instance
        clock_log: ClockLog instance (unrostered and pending approval)
    """
    event_data = {
        'type': 'unrostered_clockin_request',
        'clock_log_id': clock_log.id,
        'staff_id': clock_log.staff.id,
        'staff_name': f"{clock_log.staff.first_name} {clock_log.staff.last_name}",
        'department': clock_log.staff.department.name if clock_log.staff.department else 'No Department',
        'clock_in_time': clock_log.time_in.isoformat(),
        'message': f"{clock_log.staff.first_name} {clock_log.staff.last_name} clocked in without a scheduled shift and needs approval.",
        'actions': [
            {
                'label': 'Approve',
                'action': 'approve',
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/approve/',
                'style': 'success'
            },
            {
                'label': 'Reject',
                'action': 'reject', 
                'endpoint': f'/api/hotels/{hotel.slug}/clock-logs/{clock_log.id}/reject/',
                'style': 'danger'
            }
        ],
        'timestamp': now().isoformat(),
    }
    
    # Send to managers channel
    pusher_client.trigger(
        channel=f"attendance-{hotel.slug}-managers",
        event='unrostered-clockin-request',
        data=event_data
    )


def validate_period_finalization(period):
    """
    Validate that a roster period can be finalized.
    Checks for unresolved unrostered logs within the period date range.
    
    Args:
        period: RosterPeriod instance
        
    Returns:
        tuple: (is_valid, error_message)
    """
    from .models import ClockLog
    
    # Check for unresolved unrostered logs in the period date range
    unresolved_logs = ClockLog.objects.filter(
        hotel=period.hotel,
        time_in__date__gte=period.start_date,
        time_in__date__lte=period.end_date,
        is_unrostered=True,
        is_approved=False,
        is_rejected=False,
    ).select_related('staff')
    
    if unresolved_logs.exists():
        staff_names = [
            f"{log.staff.first_name} {log.staff.last_name}"
            for log in unresolved_logs[:5]  # Limit to first 5 for readability
        ]
        
        error_msg = f"Cannot finalize period. {unresolved_logs.count()} unresolved unrostered clock-in(s) from: {', '.join(staff_names)}"
        if unresolved_logs.count() > 5:
            error_msg += f" and {unresolved_logs.count() - 5} others"
        
        return False, error_msg
    
    return True, None


def is_period_or_log_locked(roster_period=None, clock_log=None):
    """
    Check if a roster period or clock log is locked due to finalization.
    
    Args:
        roster_period: RosterPeriod instance (optional)
        clock_log: ClockLog instance (optional)
        
    Returns:
        bool: True if locked, False otherwise
    """
    if roster_period:
        return roster_period.is_finalized
    
    if clock_log:
        # Check if the clock log falls within a finalized period
        from .models import RosterPeriod
        
        finalized_periods = RosterPeriod.objects.filter(
            hotel=clock_log.hotel,
            is_finalized=True,
            start_date__lte=clock_log.time_in.date(),
            end_date__gte=clock_log.time_in.date(),
        )
        
        return finalized_periods.exists()
    
    return False