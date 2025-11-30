# Phase 3: Config & Permissions System Implementation
# This contains configuration validation and enforcement for face attendance

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


def check_face_attendance_permissions(hotel, staff, request_type='clock_in'):
    """
    Check if face attendance is enabled for hotel and staff's department.
    Returns (allowed, error_response) tuple.
    """
    # Get hotel attendance settings
    try:
        settings = hotel.attendance_settings
    except AttributeError:
        # No settings configured - use defaults (face disabled)
        return False, Response(
            {"error": "FACE_DISABLED_FOR_HOTEL", "message": "Face attendance is not enabled for this hotel."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if face attendance is globally enabled for hotel
    face_enabled = getattr(settings, 'face_attendance_enabled', False)
    if not face_enabled:
        return False, Response(
            {"error": "FACE_DISABLED_FOR_HOTEL", "message": "Face attendance is not enabled for this hotel."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check department restrictions
    dept_restrictions = getattr(settings, 'face_attendance_departments', [])
    if dept_restrictions and staff.department:
        if staff.department.id not in dept_restrictions:
            return False, Response(
                {"error": "FACE_DISABLED_FOR_DEPARTMENT", 
                 "message": f"Face attendance is not enabled for the {staff.department.name} department."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Check if self-registration is allowed (for registration requests)
    if request_type == 'register':
        self_registration_allowed = getattr(settings, 'allow_face_self_registration', True)
        if not self_registration_allowed:
            return False, Response(
                {"error": "SELF_REGISTRATION_DISABLED", 
                 "message": "Self-registration of face data is disabled. Contact your manager."},
                status=status.HTTP_403_FORBIDDEN
            )
    
    return True, None


def get_face_confidence_threshold(hotel):
    """Get the face recognition confidence threshold for the hotel"""
    try:
        settings = hotel.attendance_settings
        min_confidence = getattr(settings, 'face_attendance_min_confidence', 0.80)
        # Convert confidence (higher = better) to distance threshold (lower = better)
        # Assuming euclidean distance where 0.6 corresponds to ~80% confidence
        return (1.0 - min_confidence) * 1.5
    except AttributeError:
        return 0.6  # Default threshold


def validate_consent_requirement(hotel, consent_given):
    """Check if explicit consent is required and validate it"""
    try:
        settings = hotel.attendance_settings
        require_consent = getattr(settings, 'require_face_consent', True)
        
        if require_consent and not consent_given:
            return False, Response(
                {"error": "CONSENT_REQUIRED", 
                 "message": "Explicit consent is required for face data processing."},
                status=status.HTTP_400_BAD_REQUEST
            )
    except AttributeError:
        # Default to requiring consent
        if not consent_given:
            return False, Response(
                {"error": "CONSENT_REQUIRED", 
                 "message": "Explicit consent is required for face data processing."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return True, None


def enforce_face_config_in_register_face(hotel, staff, consent_given, request_type='register'):
    """
    Comprehensive validation for face registration with all Phase 3 checks.
    Returns (allowed, error_response) tuple.
    """
    # Check basic permissions
    allowed, error_response = check_face_attendance_permissions(hotel, staff, request_type)
    if not allowed:
        return False, error_response
    
    # Check consent requirements
    consent_valid, consent_error = validate_consent_requirement(hotel, consent_given)
    if not consent_valid:
        return False, consent_error
    
    return True, None


def enforce_face_config_in_clock_in(hotel, staff, face_distance):
    """
    Validate face clock-in against hotel configuration.
    Returns (allowed, error_response) tuple.
    """
    # Check basic permissions
    allowed, error_response = check_face_attendance_permissions(hotel, staff, 'clock_in')
    if not allowed:
        return False, error_response
    
    # Check confidence threshold
    threshold = get_face_confidence_threshold(hotel)
    if face_distance > threshold:
        return False, Response(
            {"error": "FACE_CONFIDENCE_TOO_LOW", 
             "message": "Face recognition confidence below required threshold."},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    return True, None


# Default configuration when AttendanceSettings doesn't exist
DEFAULT_FACE_CONFIG = {
    'face_attendance_enabled': False,
    'face_attendance_min_confidence': 0.80,
    'require_face_consent': True,
    'allow_face_self_registration': True,
    'face_data_retention_days': 365,
    'face_attendance_departments': []
}


def get_hotel_face_config(hotel):
    """Get face attendance configuration for a hotel with fallbacks"""
    try:
        settings = hotel.attendance_settings
        return {
            'face_attendance_enabled': getattr(settings, 'face_attendance_enabled', False),
            'face_attendance_min_confidence': getattr(settings, 'face_attendance_min_confidence', 0.80),
            'require_face_consent': getattr(settings, 'require_face_consent', True),
            'allow_face_self_registration': getattr(settings, 'allow_face_self_registration', True),
            'face_data_retention_days': getattr(settings, 'face_data_retention_days', 365),
            'face_attendance_departments': getattr(settings, 'face_attendance_departments', [])
        }
    except AttributeError:
        return DEFAULT_FACE_CONFIG.copy()


def create_attendance_settings_with_face_config(hotel):
    """Create AttendanceSettings for hotel with default face config if it doesn't exist"""
    from hotel.models import AttendanceSettings
    
    settings, created = AttendanceSettings.objects.get_or_create(
        hotel=hotel,
        defaults={
            'break_warning_hours': 6.0,
            'overtime_warning_hours': 10.0,
            'hard_limit_hours': 12.0,
            'enforce_limits': True,
            # Face settings will be added via migration
        }
    )
    return settings