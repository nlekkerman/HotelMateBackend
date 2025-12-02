"""
Pusher utility functions for staff-related real-time events.

This module centralizes all Pusher event broadcasting for staff operations
to ensure consistent real-time updates across the application.
"""

from django.utils import timezone
from chat.utils import pusher_client
import logging

logger = logging.getLogger(__name__)


def trigger_clock_status_update(hotel_slug, staff, action):
    """
    Broadcast clock in/out/break status change to all staff in the hotel.
    
    Args:
        hotel_slug: Hotel identifier
        staff: Staff instance
        action: 'clock_in', 'clock_out', 'start_break', 'end_break'
    """
    channel = f'hotel-{hotel_slug}'
    event = 'clock-status-updated'
    
    # Get current status details
    current_status = staff.get_current_status()
    
    # Ensure duty_status and current_status.status are consistent
    duty_status = staff.duty_status
    if action == 'clock_in':
        duty_status = 'on_duty'
    elif action == 'clock_out':
        duty_status = 'off_duty'
    elif action == 'start_break':
        duty_status = 'on_break'
    elif action == 'end_break':
        duty_status = 'on_duty'
    
    # Update current_status to match duty_status
    current_status['status'] = duty_status
    current_status['is_on_break'] = (duty_status == 'on_break')
    
    data = {
        'user_id': staff.user.id if staff.user else None,
        'staff_id': staff.id,
        'duty_status': duty_status,
        'is_on_duty': duty_status in ['on_duty', 'on_break'],
        'is_on_break': duty_status == 'on_break',
        'status_label': current_status['label'],
        'clock_time': timezone.now().isoformat(),
        'first_name': staff.first_name,
        'last_name': staff.last_name,
        'action': action,
        'department': staff.department.name if staff.department else None,
        'department_slug': (
            staff.department.slug if staff.department else None
        ),
        'current_status': current_status,
    }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher clock-status-updated → channel={channel} staff_id={staff.id} "
            f"duty_status={duty_status} action={action}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event} "
            f"for staff {staff.id}: {e}"
        )


def trigger_staff_profile_update(hotel_slug, staff, action='updated'):
    """
    Broadcast staff profile updates (create, update, delete).
    
    Args:
        hotel_slug: Hotel identifier
        staff: Staff instance or dict with staff data
        action: 'created', 'updated', or 'deleted'
    """
    channel = f'hotel-{hotel_slug}'
    event = 'staff-profile-updated'
    
    # Handle both Staff instance and dict
    if isinstance(staff, dict):
        data = {
            'staff_id': staff.get('id'),
            'action': action,
            'first_name': staff.get('first_name'),
            'last_name': staff.get('last_name'),
            'department': staff.get('department'),
            'role': staff.get('role'),
            'is_active': staff.get('is_active'),
            'timestamp': timezone.now().isoformat(),
        }
    else:
        data = {
            'staff_id': staff.id,
            'user_id': staff.user.id if staff.user else None,
            'action': action,
            'first_name': staff.first_name,
            'last_name': staff.last_name,
            'email': staff.email,
            'department': staff.department.name if staff.department else None,
            'department_slug': (
                staff.department.slug if staff.department else None
            ),
            'role': staff.role.name if staff.role else None,
            'role_slug': staff.role.slug if staff.role else None,
            'is_active': staff.is_active,
            'duty_status': staff.duty_status,
            'is_on_duty': staff.duty_status in ['on_duty', 'on_break'],
            'is_on_break': staff.duty_status == 'on_break',
            'access_level': staff.access_level,
            'current_status': staff.get_current_status(),
            'timestamp': timezone.now().isoformat(),
        }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: {event} ({action}) triggered "
            f"for staff {data.get('staff_id')} in hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event} "
            f"for staff {data.get('staff_id')}: {e}"
        )


def trigger_roster_update(hotel_slug, roster_data, action='updated'):
    """
    Broadcast roster/schedule updates.
    
    Args:
        hotel_slug: Hotel identifier
        roster_data: Dict with roster information
        action: 'created', 'updated', 'deleted', or 'bulk_updated'
    """
    channel = f'hotel-{hotel_slug}'
    event = 'roster-updated'
    
    data = {
        'action': action,
        'roster_id': roster_data.get('id'),
        'staff_id': roster_data.get('staff_id'),
        'staff_name': roster_data.get('staff_name'),
        'shift_date': roster_data.get('shift_date'),
        'shift_start': roster_data.get('shift_start'),
        'shift_end': roster_data.get('shift_end'),
        'department': roster_data.get('department'),
        'location': roster_data.get('location'),
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: {event} ({action}) triggered "
            f"for hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event}: {e}"
        )


def trigger_attendance_log(hotel_slug, log_data, action='clock_in'):
    """
    Broadcast attendance log events (clock in/out via face recognition).
    
    Args:
        hotel_slug: Hotel identifier
        log_data: Dict with clock log information
        action: 'clock_in' or 'clock_out'
    """
    channel = f'hotel-{hotel_slug}'
    event = 'attendance-logged'
    
    data = {
        'action': action,
        'log_id': log_data.get('id'),
        'staff_id': log_data.get('staff_id'),
        'staff_name': log_data.get('staff_name'),
        'department': log_data.get('department'),
        'time': log_data.get('time'),
        'verified_by_face': log_data.get('verified_by_face', True),
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: {event} ({action}) triggered "
            f"for staff {log_data.get('staff_id')} in hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event}: {e}"
        )


def trigger_registration_update(hotel_slug, registration_data, action):
    """
    Broadcast staff registration updates.
    
    Args:
        hotel_slug: Hotel identifier
        registration_data: Dict with registration information
        action: 'pending', 'approved', 'rejected'
    """
    channel = f'hotel-{hotel_slug}'
    event = 'staff-registration-updated'
    
    data = {
        'action': action,
        'user_id': registration_data.get('user_id'),
        'username': registration_data.get('username'),
        'registration_code': registration_data.get('registration_code'),
        'staff_id': registration_data.get('staff_id'),
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: {event} ({action}) triggered for hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event}: {e}"
        )


def trigger_navigation_permission_update(hotel_slug, staff_id, nav_items):
    """
    Broadcast navigation permission updates for staff.
    
    Args:
        hotel_slug: Hotel identifier
        staff_id: Staff member ID
        nav_items: List of navigation item slugs
    """
    channel = f'hotel-{hotel_slug}-staff-{staff_id}'
    event = 'navigation-permissions-updated'
    
    data = {
        'staff_id': staff_id,
        'navigation_items': nav_items,
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Pusher: {event} triggered for staff {staff_id} "
            f"in hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(
            f"Pusher error: Failed to trigger {event} "
            f"for staff {staff_id}: {e}"
        )


def trigger_department_role_update(hotel_slug, data_type, data, action):
    """
    Broadcast department or role updates.
    
    Args:
        hotel_slug: Hotel identifier
        data_type: 'department' or 'role'
        data: Dict with department/role information
        action: 'created', 'updated', 'deleted'
    """
    channel = f'hotel-{hotel_slug}'
    event = f'{data_type}-updated'
    
    payload = {
        'action': action,
        'id': data.get('id'),
        'name': data.get('name'),
        'slug': data.get('slug'),
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        pusher_client.trigger(channel, event, payload)
        logger.info(
            f"Pusher: {event} ({action}) triggered for hotel {hotel_slug}"
        )
    except Exception as e:
        logger.error(f"Pusher error: Failed to trigger {event}: {e}")
