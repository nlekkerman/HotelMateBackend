# Phase 2: Kiosk UX Safety Support Implementation
# This file contains helper functions for safety warnings and enhanced face clock-in response

from datetime import timedelta
from django.utils.timezone import now
from hotel.models import AttendanceSettings


def calculate_safety_warnings(staff, existing_log=None, hotel=None):
    """
    Calculate safety warning flags based on session duration and hotel settings.
    Returns dictionary with warning flags and metadata.
    """
    warnings = {
        'needs_break_warning': False,
        'needs_long_session_warning': False, 
        'needs_hard_stop_warning': False,
        'session_duration_hours': 0,
        'overtime_threshold_reached': False,
        'should_clock_out': False
    }
    
    if not existing_log:
        return warnings
    
    # Get hotel attendance settings (with defaults)
    settings = None
    if hotel:
        try:
            settings = hotel.attendance_settings
        except AttributeError:
            pass
    
    # Default thresholds if no settings configured
    break_warning_hours = settings.break_warning_hours if settings else 6.0
    overtime_warning_hours = settings.overtime_warning_hours if settings else 10.0
    hard_limit_hours = settings.hard_limit_hours if settings else 12.0
    
    # Calculate session duration
    current_time = now()
    session_duration = current_time - existing_log.time_in
    session_hours = session_duration.total_seconds() / 3600
    
    warnings['session_duration_hours'] = round(session_hours, 2)
    
    # Determine warning levels
    if session_hours >= break_warning_hours:
        warnings['needs_break_warning'] = True
    
    if session_hours >= overtime_warning_hours:
        warnings['needs_long_session_warning'] = True
        warnings['overtime_threshold_reached'] = True
    
    if session_hours >= hard_limit_hours:
        warnings['needs_hard_stop_warning'] = True
        warnings['should_clock_out'] = True
    
    return warnings


def get_shift_info(staff, hotel, current_dt):
    """
    Get shift information for the current staff member and time.
    Returns shift details or None if not rostered.
    """
    from attendance.views import find_matching_shift_for_datetime
    
    matching_shift = find_matching_shift_for_datetime(hotel, staff, current_dt)
    
    if matching_shift:
        return {
            'id': matching_shift.id,
            'date': matching_shift.shift_date,
            'start_time': matching_shift.shift_start,
            'end_time': matching_shift.shift_end,
            'location': matching_shift.location.name if matching_shift.location else None,
            'department': matching_shift.department.name if matching_shift.department else None,
            'is_rostered': True
        }
    
    return {'is_rostered': False}


def enhanced_face_clock_in_response(staff, log, action_type, hotel, existing_log=None):
    """
    Create enhanced response payload for face clock-in with safety information.
    """
    from attendance.serializers import ClockLogSerializer
    
    # Calculate safety warnings
    safety_warnings = calculate_safety_warnings(staff, existing_log, hotel)
    
    # Get shift information
    shift_info = get_shift_info(staff, hotel, now())
    
    # Base response
    response_data = {
        "message": f"{action_type.replace('_', '-').title()} successful for {staff.first_name}",
        "staff_id": staff.id,
        "staff_name": f"{staff.first_name} {staff.last_name}",
        "action": action_type.upper(),
        "is_rostered": shift_info['is_rostered'],
        "shift_info": shift_info if shift_info['is_rostered'] else None,
        "log": ClockLogSerializer(log).data
    }
    
    # Add safety warnings for active sessions
    if action_type == "clock_in" or existing_log:
        response_data.update({
            "session_duration_hours": safety_warnings['session_duration_hours'],
            "needs_break_warning": safety_warnings['needs_break_warning'],
            "needs_long_session_warning": safety_warnings['needs_long_session_warning'],
            "needs_hard_stop_warning": safety_warnings['needs_hard_stop_warning'],
            "overtime_threshold_reached": safety_warnings['overtime_threshold_reached'],
            "should_clock_out": safety_warnings['should_clock_out']
        })
    
    return response_data


def handle_force_log_unrostered(staff, hotel, request, reason=None):
    """
    Handle force logging for unrostered staff with audit trail.
    """
    from attendance.models import ClockLog, FaceAuditLog
    
    # Create unrostered clock log
    log = ClockLog.objects.create(
        hotel=hotel,
        staff=staff,
        verified_by_face=True,
        roster_shift=None,
        is_unrostered=True,
        is_approved=False,  # Requires manager approval
        is_rejected=False,
    )
    
    # Update staff status
    staff.is_on_duty = True
    staff.save(update_fields=["is_on_duty"])
    
    # Create audit log for forced clock-in
    FaceAuditLog.objects.create(
        hotel=hotel,
        staff=staff,
        action='FORCED_CLOCK_IN',
        performed_by=staff,
        reason=reason or 'Unrostered clock-in via kiosk',
        client_ip=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    )
    
    return log


def get_unrostered_response_with_force_option(staff, hotel_slug):
    """
    Generate response for unrostered staff with force log option.
    """
    return {
        "action": "unrostered_detected",
        "message": f"No scheduled shift found for {staff.first_name}. Please confirm if you want to clock in anyway.",
        "staff": {
            "id": staff.id,
            "name": f"{staff.first_name} {staff.last_name}",
            "department": staff.department.name if staff.department else "No Department"
        },
        "requires_confirmation": True,
        "force_log_available": True,
        "confirmation_endpoint": f"/api/staff/hotel/{hotel_slug}/attendance/clock-logs/unrostered-confirm/",
        "force_log_endpoint": f"/api/staff/hotel/{hotel_slug}/attendance/clock-logs/force-log/"
    }