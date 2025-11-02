"""
Centralized Pusher notification utilities for HotelMate
Sends real-time notifications to staff based on department and on-duty status
"""
import logging
from typing import List, Dict, Any
from chat.utils import pusher_client
from staff.models import Staff

logger = logging.getLogger(__name__)


def notify_staff_by_department(
    hotel,
    department_slug: str,
    event: str,
    data: Dict[str, Any],
    only_on_duty: bool = True
) -> int:
    """
    Notify all staff in a specific department.
    
    Args:
        hotel: Hotel instance
        department_slug: Department slug (e.g., 'kitchen', 'front-office')
        event: Pusher event name (e.g., 'new-order')
        data: Event payload data
        only_on_duty: If True, only notify staff who are on duty
    
    Returns:
        Number of staff members notified
    """
    staff_qs = Staff.objects.filter(
        hotel=hotel,
        department__slug=department_slug,
        is_active=True
    )
    
    if only_on_duty:
        staff_qs = staff_qs.filter(is_on_duty=True)
    
    notified_count = 0
    for staff in staff_qs:
        channel = f"{hotel.slug}-staff-{staff.id}-{department_slug}"
        try:
            pusher_client.trigger(channel, event, data)
            logger.info(
                f"Pusher: staff={staff.id} "
                f"({staff.first_name} {staff.last_name}), "
                f"channel={channel}, event={event}"
            )
            notified_count += 1
        except Exception as e:
            logger.error(
                f"Failed Pusher to staff={staff.id}, "
                f"channel={channel}: {e}"
            )
    
    return notified_count


def notify_staff_by_role(
    hotel,
    role_slug: str,
    event: str,
    data: Dict[str, Any],
    only_on_duty: bool = True
) -> int:
    """
    Notify all staff with a specific role.
    
    Args:
        hotel: Hotel instance
        role_slug: Role slug (e.g., 'porter', 'receptionist')
        event: Pusher event name
        data: Event payload data
        only_on_duty: If True, only notify staff who are on duty
    
    Returns:
        Number of staff members notified
    """
    staff_qs = Staff.objects.filter(
        hotel=hotel,
        role__slug=role_slug,
        is_active=True
    )
    
    if only_on_duty:
        staff_qs = staff_qs.filter(is_on_duty=True)
    
    notified_count = 0
    for staff in staff_qs:
        channel = f"{hotel.slug}-staff-{staff.id}-{role_slug}"
        try:
            pusher_client.trigger(channel, event, data)
            logger.info(
                f"Pusher: staff={staff.id} "
                f"({staff.first_name} {staff.last_name}), "
                f"role={role_slug}, channel={channel}, event={event}"
            )
            notified_count += 1
        except Exception as e:
            logger.error(
                f"Failed Pusher to staff={staff.id}, "
                f"channel={channel}: {e}"
            )
    
    return notified_count


def notify_multiple_roles(
    hotel,
    role_slugs: List[str],
    event: str,
    data: Dict[str, Any],
    only_on_duty: bool = True
) -> int:
    """
    Notify staff across multiple roles.
    """
    total_notified = 0
    for role_slug in role_slugs:
        count = notify_staff_by_role(
            hotel, role_slug, event, data, only_on_duty
        )
        total_notified += count
    
    return total_notified


def notify_kitchen_staff(hotel, event: str, data: Dict[str, Any]) -> int:
    """Notify all on-duty kitchen staff."""
    return notify_staff_by_department(
        hotel, 'kitchen', event, data, only_on_duty=True
    )


def notify_porters(hotel, event: str, data: Dict[str, Any]) -> int:
    """Notify all on-duty porters."""
    return notify_staff_by_role(
        hotel, 'porter', event, data, only_on_duty=True
    )


def notify_room_service_waiters(
    hotel, event: str, data: Dict[str, Any]
) -> int:
    """Notify all on-duty room service waiters."""
    return notify_staff_by_role(
        hotel,
        'room_service_waiter',
        event,
        data,
        only_on_duty=True
    )


def notify_receptionists(hotel, event: str, data: Dict[str, Any]) -> int:
    """Notify all on-duty receptionists."""
    return notify_staff_by_role(
        hotel, 'receptionist', event, data, only_on_duty=True
    )


def notify_maintenance_staff(
    hotel, event: str, data: Dict[str, Any]
) -> int:
    """Notify all on-duty maintenance staff."""
    return notify_staff_by_department(
        hotel,
        'maintenance',
        event,
        data,
        only_on_duty=True
    )


def notify_fnb_staff(hotel, event: str, data: Dict[str, Any]) -> int:
    """Notify all on-duty Food & Beverage staff."""
    return notify_staff_by_department(
        hotel,
        'food-and-beverage',
        event,
        data,
        only_on_duty=True
    )


def notify_guest_in_room(
    hotel,
    room_number: str,
    event: str,
    data: Dict[str, Any]
) -> bool:
    """Notify guest in a specific room."""
    channel = f"{hotel.slug}-room-{room_number}"
    try:
        pusher_client.trigger(channel, event, data)
        logger.info(
            f"Guest notification sent: room={room_number}, "
            f"channel={channel}, event={event}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed guest notification: room={room_number}, "
            f"channel={channel}: {e}"
        )
        return False
