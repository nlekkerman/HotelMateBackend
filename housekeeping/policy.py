"""
Housekeeping Permission System

Defines role-based access control for room status changes and task management.
Integrates with existing Staff access_level, department, and role models.
"""


def is_manager(staff):
    """
    Check if staff member has manager-level access.
    
    Args:
        staff: Staff instance
    
    Returns:
        bool: True if staff has manager privileges
    """
    if not staff or not staff.access_level:
        return False
    
    return staff.access_level in ['staff_admin', 'super_staff_admin']


def is_housekeeping(staff):
    """
    Check if staff member belongs to housekeeping department or role.
    Defensive against null department/role values.
    
    Args:
        staff: Staff instance
    
    Returns:
        bool: True if staff is in housekeeping
    """
    if not staff:
        return False
    
    # Check department slug first
    if staff.department and hasattr(staff.department, 'slug'):
        if staff.department.slug == 'housekeeping':
            return True
    
    # Check role slug second
    if staff.role and hasattr(staff.role, 'slug'):
        if staff.role.slug == 'housekeeping':
            return True
    
    return False


def can_change_room_status(staff, room, to_status, source="HOUSEKEEPING", note=""):
    """
    Determine if staff member can change room status based on role and business rules.
    
    Args:
        staff: Staff instance attempting the change
        room: Room instance to be changed
        to_status: Target room status
        source: Source of the change (HOUSEKEEPING, FRONT_DESK, etc.)
        note: Optional note (required for MANAGER_OVERRIDE)
    
    Returns:
        tuple: (can_change: bool, error_message: str)
    """
    if not staff or not room:
        return False, "Staff and room are required"
    
    # Validate hotel scoping
    if staff.hotel_id != room.hotel_id:
        return False, "Staff member must belong to the same hotel as the room"
    
    # Validate the room can transition to the target status
    if not room.can_transition_to(to_status):
        return False, f"Room cannot transition from {room.room_status} to {to_status}"
    
    # Manager privileges - can do any valid transition
    if is_manager(staff):
        # Require note for manager overrides
        if source == "MANAGER_OVERRIDE" and not note.strip():
            return False, "Manager override requires a note explaining the reason"
        return True, ""
    
    # Housekeeping staff privileges
    if is_housekeeping(staff):
        return _can_housekeeping_change_status(room.room_status, to_status, source)
    
    # Front desk and other staff - limited access
    return _can_front_desk_change_status(room.room_status, to_status, source)


def _can_housekeeping_change_status(from_status, to_status, source):
    """
    Check if housekeeping staff can make specific status transitions.
    
    Housekeeping can handle normal cleaning workflow:
    - CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED → READY_FOR_GUEST
    - Rollback: CLEANING_IN_PROGRESS → CHECKOUT_DIRTY
    - Flag maintenance: Any → MAINTENANCE_REQUIRED
    
    Returns:
        tuple: (can_change: bool, error_message: str)
    """
    # Normal cleaning workflow transitions
    allowed_transitions = {
        'CHECKOUT_DIRTY': ['CLEANING_IN_PROGRESS', 'MAINTENANCE_REQUIRED'],
        'CLEANING_IN_PROGRESS': ['CLEANED_UNINSPECTED', 'CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
        'CLEANED_UNINSPECTED': ['READY_FOR_GUEST', 'MAINTENANCE_REQUIRED'],
        'READY_FOR_GUEST': ['MAINTENANCE_REQUIRED'],
        'OCCUPIED': ['MAINTENANCE_REQUIRED'],
    }
    
    if from_status in allowed_transitions:
        if to_status in allowed_transitions[from_status]:
            return True, ""
    
    # Additional maintenance flagging from any status
    if to_status == 'MAINTENANCE_REQUIRED':
        return True, ""
    
    return False, f"Housekeeping staff cannot change room status from {from_status} to {to_status}"


def _can_front_desk_change_status(from_status, to_status, source):
    """
    Check if front desk staff can make specific status transitions.
    
    Front desk has limited access:
    - Cannot set cleaning-related statuses (READY_FOR_GUEST, CLEANED_UNINSPECTED, CLEANING_IN_PROGRESS)
    - Can create tasks and request cleaning
    - May set CHECKOUT_DIRTY in rare cases
    - Can flag maintenance
    
    Returns:
        tuple: (can_change: bool, error_message: str)
    """
    # Statuses front desk cannot set
    forbidden_statuses = {
        'READY_FOR_GUEST',
        'CLEANED_UNINSPECTED', 
        'CLEANING_IN_PROGRESS'
    }
    
    if to_status in forbidden_statuses:
        return False, f"Front desk staff cannot set room status to {to_status}"
    
    # Limited allowed transitions
    allowed_transitions = {
        'OCCUPIED': ['CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
        'READY_FOR_GUEST': ['MAINTENANCE_REQUIRED'],
    }
    
    if from_status in allowed_transitions:
        if to_status in allowed_transitions[from_status]:
            return True, ""
    
    return False, f"Front desk staff cannot change room status from {from_status} to {to_status}"


def can_assign_task(staff, task):
    """
    Check if staff member can assign housekeeping tasks.
    
    Args:
        staff: Staff instance attempting assignment
        task: HousekeepingTask instance to be assigned
    
    Returns:
        tuple: (can_assign: bool, error_message: str)
    """
    if not staff or not task:
        return False, "Staff and task are required"
    
    # Must belong to same hotel
    if staff.hotel_id != task.hotel_id:
        return False, "Staff member must belong to the same hotel as the task"
    
    # Only managers can assign tasks (keep it simple for now)
    if not is_manager(staff):
        return False, "Only managers can assign housekeeping tasks"
    
    return True, ""


def can_view_dashboard(staff):
    """
    Check if staff member can view housekeeping dashboard.
    
    Args:
        staff: Staff instance
    
    Returns:
        bool: True if staff can view dashboard
    """
    if not staff:
        return False
    
    # Managers and housekeeping staff can view dashboard
    return is_manager(staff) or is_housekeeping(staff)
