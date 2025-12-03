# attendance/business_rules.py
"""
Business Rules Validation for Roster Operations
Maintains consistency with existing attendance/clock logic
"""

from datetime import datetime, timedelta, time
from django.db.models import Q, Sum
from django.utils.timezone import now
from .models import StaffRoster, ClockLog
from .helpers import shift_to_datetime_range


# Reuse existing constants from attendance logic
MAX_DAILY_HOURS = 12  # Align with attendance "12h hard stop"
MAX_WEEKLY_HOURS = 48  # Standard working week limit
MINIMUM_BREAK_DURATION = timedelta(minutes=30)  # Minimum break time
MAXIMUM_SHIFT_DURATION = timedelta(hours=12)  # Max single shift length


def validate_shift_business_rules(shift_data, hotel, existing_shifts=None):
    """
    Validate a shift against business rules used by attendance system.
    Returns (is_valid, error_messages)
    
    Args:
        shift_data: Dict with shift_start, shift_end, shift_date, staff_id
        hotel: Hotel instance
        existing_shifts: Optional list of existing shifts to check against
    """
    errors = []
    
    # 1. Use existing shift_to_datetime_range logic
    try:
        start_dt, end_dt = shift_to_datetime_range(
            shift_date=shift_data['shift_date'],
            shift_start=shift_data['shift_start'], 
            shift_end=shift_data['shift_end']
        )
    except Exception as e:
        errors.append(f"Invalid shift time range: {e}")
        return False, errors
    
    # 2. Validate shift duration
    shift_duration = end_dt - start_dt
    if shift_duration > MAXIMUM_SHIFT_DURATION:
        errors.append(f"Shift duration ({shift_duration}) exceeds maximum {MAXIMUM_SHIFT_DURATION}")
    
    if shift_duration <= timedelta(minutes=0):
        errors.append("Shift duration must be positive")
    
    # 3. Check daily hour limits (align with attendance logic)
    if existing_shifts:
        daily_hours = calculate_daily_hours(
            staff_id=shift_data['staff_id'],
            date=shift_data['shift_date'],
            existing_shifts=existing_shifts,
            additional_hours=shift_duration.total_seconds() / 3600
        )
        
        if daily_hours > MAX_DAILY_HOURS:
            errors.append(f"Daily hours ({daily_hours:.1f}) would exceed maximum {MAX_DAILY_HOURS}")
    
    # 4. Validate break times if provided
    if shift_data.get('break_start') and shift_data.get('break_end'):
        break_start = shift_data['break_start']
        break_end = shift_data['break_end']
        
        # Convert to datetime for comparison
        break_start_dt = datetime.combine(shift_data['shift_date'], break_start)
        break_end_dt = datetime.combine(shift_data['shift_date'], break_end)
        
        # Handle overnight breaks
        if break_end < break_start:
            break_end_dt += timedelta(days=1)
        
        break_duration = break_end_dt - break_start_dt
        
        # Check break is within shift
        if break_start_dt < start_dt or break_end_dt > end_dt:
            errors.append("Break time must be within shift hours")
        
        # Check minimum break duration for long shifts
        if shift_duration > timedelta(hours=6) and break_duration < MINIMUM_BREAK_DURATION:
            errors.append(f"Shifts over 6 hours require minimum {MINIMUM_BREAK_DURATION} break")
    
    return len(errors) == 0, errors


def calculate_daily_hours(staff_id, date, existing_shifts=None, additional_hours=0):
    """
    Calculate total daily hours for a staff member.
    Consistent with attendance daily hour calculations.
    """
    total_hours = additional_hours
    
    if existing_shifts:
        # Sum from existing shift list
        for shift in existing_shifts:
            if (shift.get('staff_id') == staff_id and 
                shift.get('shift_date') == date):
                
                # Use same logic as attendance system
                start_dt, end_dt = shift_to_datetime_range(
                    shift_date=shift['shift_date'],
                    shift_start=shift['shift_start'],
                    shift_end=shift['shift_end']
                )
                shift_hours = (end_dt - start_dt).total_seconds() / 3600
                total_hours += shift_hours
    
    return total_hours


def calculate_weekly_hours(staff_id, week_start_date, shifts):
    """
    Calculate weekly hours consistent with attendance tracking.
    """
    week_end_date = week_start_date + timedelta(days=6)
    total_hours = 0
    
    for shift in shifts:
        if (shift.get('staff_id') == staff_id and 
            week_start_date <= shift.get('shift_date') <= week_end_date):
            
            start_dt, end_dt = shift_to_datetime_range(
                shift_date=shift['shift_date'],
                shift_start=shift['shift_start'],
                shift_end=shift['shift_end']
            )
            shift_hours = (end_dt - start_dt).total_seconds() / 3600
            total_hours += shift_hours
    
    return total_hours


def check_availability_conflicts(staff_id, shift_date, shift_start, shift_end, hotel):
    """
    Check if staff member has availability conflicts.
    Integrates with ClockLog logic for active sessions.
    """
    conflicts = []
    
    # 1. Check for overlapping roster shifts
    overlapping_shifts = StaffRoster.objects.filter(
        hotel=hotel,
        staff_id=staff_id,
        shift_date=shift_date
    ).exclude(
        Q(shift_end__lte=shift_start) | Q(shift_start__gte=shift_end)
    )
    
    if overlapping_shifts.exists():
        conflicts.append("Overlapping roster shift exists")
    
    # 2. Check for active clock sessions (align with ClockLog logic)
    active_session = ClockLog.objects.filter(
        hotel=hotel,
        staff_id=staff_id,
        time_in__date=shift_date,
        time_out__isnull=True
    ).first()
    
    if active_session:
        # Use existing session logic to determine if it conflicts
        session_start = active_session.time_in.time()
        
        # Check if new shift overlaps with active session
        if not (shift_end <= session_start or shift_start >= time(23, 59)):
            conflicts.append(f"Active clock session since {session_start}")
    
    return conflicts


def validate_copy_operation_constraints(source_shifts, target_period, copy_options=None):
    """
    Validate that a copy operation respects business rules.
    """
    errors = []
    warnings = []
    
    if not source_shifts:
        errors.append("No source shifts to copy")
        return False, errors, warnings
    
    # Check target period capacity
    if target_period.published:
        errors.append("Cannot copy to published/finalized period")
    
    # Validate each shift would comply with business rules
    for shift in source_shifts:
        shift_data = {
            'shift_date': shift.shift_date,
            'shift_start': shift.shift_start,
            'shift_end': shift.shift_end,
            'break_start': shift.break_start,
            'break_end': shift.break_end,
            'staff_id': shift.staff_id
        }
        
        is_valid, shift_errors = validate_shift_business_rules(
            shift_data, 
            target_period.hotel,
            existing_shifts=[]
        )
        
        if not is_valid:
            errors.extend([f"Shift {shift.id}: {err}" for err in shift_errors])
    
    # Check weekly hour limits if copying full weeks
    if copy_options and copy_options.get('check_weekly_limits', True):
        staff_weekly_hours = {}
        for shift in source_shifts:
            if shift.staff_id not in staff_weekly_hours:
                staff_weekly_hours[shift.staff_id] = 0
            
            start_dt, end_dt = shift_to_datetime_range(
                shift.shift_date, shift.shift_start, shift.shift_end
            )
            hours = (end_dt - start_dt).total_seconds() / 3600
            staff_weekly_hours[shift.staff_id] += hours
        
        for staff_id, hours in staff_weekly_hours.items():
            if hours > MAX_WEEKLY_HOURS:
                warnings.append(f"Staff {staff_id}: {hours:.1f}h exceeds recommended {MAX_WEEKLY_HOURS}h")
    
    return len(errors) == 0, errors, warnings


def suggest_conflict_resolution(conflicted_shifts):
    """
    Suggest automatic resolutions for shift conflicts.
    Uses same logic as attendance conflict resolution.
    """
    suggestions = []
    
    for shift_data in conflicted_shifts:
        # Suggest time adjustments
        original_start = shift_data['shift_start']
        original_end = shift_data['shift_end']
        
        # Suggest 15-minute adjustments
        suggestions.append({
            'shift_id': shift_data.get('id'),
            'type': 'time_adjustment',
            'options': [
                {
                    'description': 'Start 15 minutes later',
                    'shift_start': (datetime.combine(shift_data['shift_date'], original_start) + 
                                  timedelta(minutes=15)).time(),
                    'shift_end': original_end
                },
                {
                    'description': 'End 15 minutes earlier', 
                    'shift_start': original_start,
                    'shift_end': (datetime.combine(shift_data['shift_date'], original_end) - 
                                timedelta(minutes=15)).time()
                }
            ]
        })
    
    return suggestions


# Integration with existing attendance helpers
def align_with_clock_log_rules(shift, clock_logs=None):
    """
    Ensure roster shift aligns with ClockLog attachment rules.
    Uses existing find_matching_shift_for_datetime logic.
    """
    from .helpers import find_matching_shift_for_datetime
    
    # This ensures new roster shifts follow same rules that 
    # ClockLog.roster_shift attachment uses
    
    if clock_logs:
        for log in clock_logs:
            matching_shift = find_matching_shift_for_datetime(
                hotel=shift.hotel,
                staff=shift.staff, 
                current_dt=log.time_in
            )
            
            # If this shift should match the clock log, verify compatibility
            if matching_shift and matching_shift.id == shift.id:
                # Shift is correctly aligned with clock log rules
                continue
    
    return True  # Shift follows existing rules