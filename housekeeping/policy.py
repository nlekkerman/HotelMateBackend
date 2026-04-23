"""
Housekeeping Permission System

Defines capability-backed access control for room status changes and task
management. All enforcement reads from the canonical capability catalog
(staff/capability_catalog.py) via staff.permissions.has_capability.

Capabilities consulted:
    housekeeping.room_status.override    — manager-level override (any valid transition)
    housekeeping.room_status.transition  — normal housekeeping cleaning workflow
    housekeeping.room_status.front_desk  — limited front-desk transitions
    housekeeping.task.assign             — assign housekeeping tasks
"""
from staff.permissions import has_capability


# ---------------------------------------------------------------------------
# Transition matrices — business rules only, no identity/role logic.
# ---------------------------------------------------------------------------

def _can_housekeeping_change_status(from_status, to_status, source):
    """
    Check if a holder of housekeeping.room_status.transition can make
    this transition.

    Normal cleaning workflow:
        CHECKOUT_DIRTY → CLEANING_IN_PROGRESS → CLEANED_UNINSPECTED
        → READY_FOR_GUEST
        Rollback: CLEANING_IN_PROGRESS → CHECKOUT_DIRTY
        Flag maintenance: Any → MAINTENANCE_REQUIRED
    """
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
    Check if a holder of housekeeping.room_status.front_desk can make
    this transition.

    Front desk is limited: cannot set cleaning-related statuses, can flag
    maintenance, may mark OCCUPIED → CHECKOUT_DIRTY.
    """
    forbidden_statuses = {
        'READY_FOR_GUEST',
        'CLEANED_UNINSPECTED',
        'CLEANING_IN_PROGRESS',
    }

    if to_status in forbidden_statuses:
        return False, f"Front desk staff cannot set room status to {to_status}"

    allowed_transitions = {
        'OCCUPIED': ['CHECKOUT_DIRTY', 'MAINTENANCE_REQUIRED'],
        'READY_FOR_GUEST': ['MAINTENANCE_REQUIRED'],
    }

    if from_status in allowed_transitions:
        if to_status in allowed_transitions[from_status]:
            return True, ""

    return False, f"Front desk staff cannot change room status from {from_status} to {to_status}"


# ---------------------------------------------------------------------------
# Public policy API — capability + hotel scope + business rules.
# ---------------------------------------------------------------------------

def can_change_room_status(staff, room, to_status, source="HOUSEKEEPING", note=""):
    """
    Determine if staff can change room status.

    Precedence:
        1. housekeeping.room_status.override → any valid transition
           (note required when source == MANAGER_OVERRIDE).
        2. housekeeping.room_status.transition → housekeeping workflow matrix.
        3. housekeeping.room_status.front_desk → front-desk matrix.
        4. Otherwise → denied.

    Returns:
        tuple: (can_change: bool, error_message: str)
    """
    if not staff or not room:
        return False, "Staff and room are required"

    # Hotel scope
    if staff.hotel_id != room.hotel_id:
        return False, "Staff member must belong to the same hotel as the room"

    # Business rule: transition must be valid on the room's state machine.
    if not room.can_transition_to(to_status):
        return False, f"Room cannot transition from {room.room_status} to {to_status}"

    user = staff.user

    # 1. Override capability — full reach, requires note on MANAGER_OVERRIDE.
    if has_capability(user, 'housekeeping.room_status.override'):
        if source == "MANAGER_OVERRIDE" and not note.strip():
            return False, "Manager override requires a note explaining the reason"
        return True, ""

    # 2. Housekeeping workflow capability.
    if has_capability(user, 'housekeeping.room_status.transition'):
        return _can_housekeeping_change_status(room.room_status, to_status, source)

    # 3. Front desk capability.
    if has_capability(user, 'housekeeping.room_status.front_desk'):
        return _can_front_desk_change_status(room.room_status, to_status, source)

    return False, "You do not have permission to change room status"


def can_assign_task(staff, task):
    """
    Check if staff can assign housekeeping tasks.

    Requires capability: housekeeping.task.assign, same-hotel scope.
    """
    if not staff or not task:
        return False, "Staff and task are required"

    if staff.hotel_id != task.hotel_id:
        return False, "Staff member must belong to the same hotel as the task"

    if not has_capability(staff.user, 'housekeeping.task.assign'):
        return False, "You do not have permission to assign housekeeping tasks"

    return True, ""


def can_view_dashboard(staff):
    """
    Dashboard visibility: any staff carrying any housekeeping capability.
    """
    if not staff:
        return False

    user = staff.user
    return (
        has_capability(user, 'housekeeping.room_status.override')
        or has_capability(user, 'housekeeping.room_status.transition')
        or has_capability(user, 'housekeeping.room_status.front_desk')
        or has_capability(user, 'housekeeping.task.assign')
    )
