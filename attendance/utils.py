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
        f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        'break-warning',
        event_data
    )
    
    # Also send to managers channel for oversight
    pusher_client.trigger(
        f"attendance-{hotel.slug}-managers",
        'staff-break-warning',
        event_data
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
        f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        'overtime-warning',
        event_data
    )
    
    # Send to managers channel for oversight
    pusher_client.trigger(
        f"attendance-{hotel.slug}-managers",
        'staff-overtime-warning',
        event_data
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
        f"attendance-{hotel.slug}-staff-{clock_log.staff.id}",
        'hard-limit-warning',
        event_data
    )
    
    # Send to managers channel for urgent oversight
    pusher_client.trigger(
        f"attendance-{hotel.slug}-managers",
        'staff-hard-limit-warning',
        event_data
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
        f"attendance-{hotel.slug}-managers",
        'unrostered-clockin-request',
        event_data
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


# ===== FACE RECOGNITION UTILITIES =====

def create_face_audit_log(hotel, staff, action, performed_by=None, reason=None, 
                         consent_given=True, request=None):
    """
    Create a face audit log entry for compliance tracking.
    
    Args:
        hotel: Hotel instance
        staff: Staff instance whose face is being acted upon
        action: One of 'REGISTERED', 'REVOKED', 'RE_REGISTERED'
        performed_by: Staff instance who performed the action (optional)
        reason: Reason for the action (optional, recommended for revocation)
        consent_given: Whether consent was given (default True)
        request: HTTP request object for IP/user agent tracking (optional)
    
    Returns:
        FaceAuditLog instance
    """
    from .models import FaceAuditLog
    
    audit_data = {
        'hotel': hotel,
        'staff': staff,
        'action': action,
        'performed_by': performed_by or staff,
        'reason': reason or '',
        'consent_given': consent_given,
    }
    
    # Extract request metadata if provided
    if request:
        # Get IP address (handles proxy headers)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            audit_data['client_ip'] = x_forwarded_for.split(',')[0].strip()
        else:
            audit_data['client_ip'] = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    return FaceAuditLog.objects.create(**audit_data)


def validate_face_encoding(encoding):
    """
    Validate face encoding format and values.
    
    Args:
        encoding: List of float values representing face descriptor
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not isinstance(encoding, list):
        return False, "Encoding must be a list"
    
    if len(encoding) != 128:
        return False, "Encoding must be exactly 128 dimensions"
    
    try:
        # Ensure all values are numeric
        float_encoding = [float(x) for x in encoding]
        
        # Basic sanity check - values should be reasonable
        for val in float_encoding:
            if abs(val) > 10.0:  # Face encodings typically range -2 to 2
                return False, "Encoding values appear invalid (out of expected range)"
        
        return True, ""
    except (ValueError, TypeError):
        return False, "Encoding values must be numeric"


def calculate_face_similarity_score(encoding1, encoding2):
    """
    Calculate similarity score between two face encodings using euclidean distance.
    
    Args:
        encoding1: First face encoding (128-dim list)
        encoding2: Second face encoding (128-dim list)
    
    Returns:
        float: Distance score (lower = more similar, typically < 0.6 = match)
    """
    import math
    
    if len(encoding1) != 128 or len(encoding2) != 128:
        raise ValueError("Both encodings must be 128 dimensions")
    
    # Calculate euclidean distance
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(encoding1, encoding2)))
    return distance


def find_best_face_match(probe_encoding, staff_faces_queryset, threshold=0.6):
    """
    Find the best matching staff face from a queryset.
    
    Args:
        probe_encoding: Face encoding to match against (128-dim list)
        staff_faces_queryset: QuerySet of StaffFace objects to search
        threshold: Maximum distance for a valid match (default 0.6)
    
    Returns:
        tuple: (staff_instance_or_none, confidence_score)
    """
    best_staff = None
    best_distance = float('inf')
    
    for face_entry in staff_faces_queryset.filter(is_active=True):
        if not face_entry.encoding:
            continue
            
        try:
            distance = calculate_face_similarity_score(probe_encoding, face_entry.encoding)
            
            if distance < best_distance:
                best_distance = distance
                best_staff = face_entry.staff
        except (ValueError, TypeError):
            # Skip invalid encodings
            continue
    
    # Return match only if within threshold
    if best_distance <= threshold:
        return best_staff, best_distance
    
    return None, best_distance


def generate_face_registration_response(staff_face):
    """
    Generate standardized response data for face registration.
    
    Args:
        staff_face: StaffFace instance
    
    Returns:
        dict: Serialized face registration data
    """
    return {
        'id': staff_face.id,
        'staff': staff_face.staff.id,
        'staff_name': staff_face.staff.user.get_full_name(),
        'hotel': staff_face.hotel.id,
        'hotel_slug': staff_face.hotel.slug,
        'image_url': staff_face.get_image_url(),
        'public_id': staff_face.get_public_id(),
        'encoding_length': len(staff_face.encoding) if staff_face.encoding else 0,
        'is_active': staff_face.is_active,
        'consent_given': staff_face.consent_given,
        'registered_by': (
            staff_face.registered_by.user.get_full_name() 
            if staff_face.registered_by else None
        ),
        'created_at': staff_face.created_at.isoformat(),
        'updated_at': staff_face.updated_at.isoformat(),
    }


def check_face_attendance_permissions(staff, hotel):
    """
    Check if staff member has permission to use face attendance features.
    
    Args:
        staff: Staff instance
        hotel: Hotel instance
    
    Returns:
        tuple: (has_permission: bool, error_message: str)
    """
    # Basic hotel access check
    if staff.hotel_id != hotel.id:
        return False, "Staff member does not belong to this hotel"
    
    # Check if staff is active
    if not staff.is_active:
        return False, "Staff member account is inactive"
    
    # Check hotel settings (if implemented)
    attendance_settings = getattr(hotel, 'attendance_settings', None)
    if attendance_settings:
        # Check if face attendance is enabled
        if hasattr(attendance_settings, 'face_attendance_enabled'):
            if not attendance_settings.face_attendance_enabled:
                return False, "Face attendance is disabled for this hotel"
        
        # Check department restrictions (if implemented)
        if hasattr(attendance_settings, 'allowed_departments'):
            allowed_departments = getattr(attendance_settings, 'allowed_departments', None)
            if allowed_departments and staff.department:
                if staff.department not in allowed_departments.all():
                    return False, "Face attendance not allowed for your department"
    
    return True, ""


def sanitize_face_data_for_export(staff_face):
    """
    Create a sanitized version of face data for audit exports.
    Excludes sensitive biometric encoding data.
    
    Args:
        staff_face: StaffFace instance
    
    Returns:
        dict: Sanitized face data for export
    """
    return {
        'staff_id': staff_face.staff.id,
        'staff_name': staff_face.staff.user.get_full_name(),
        'hotel_slug': staff_face.hotel.slug,
        'has_image': bool(staff_face.image),
        'image_url': staff_face.get_image_url(),  # URL only, no raw data
        'has_encoding': bool(staff_face.encoding),
        'encoding_dimensions': len(staff_face.encoding) if staff_face.encoding else 0,
        'is_active': staff_face.is_active,
        'consent_given': staff_face.consent_given,
        'registered_by': (
            staff_face.registered_by.user.get_full_name() 
            if staff_face.registered_by else None
        ),
        'created_at': staff_face.created_at.isoformat(),
        'updated_at': staff_face.updated_at.isoformat(),
    }