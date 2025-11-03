from notifications.pusher_utils import notify_porters
from notifications.fcm_service import (
    send_porter_order_notification,
    send_porter_breakfast_notification,
    send_porter_count_update,
    send_kitchen_staff_order_notification
)

import logging
logger = logging.getLogger(__name__)


def notify_porters_of_room_service_order(order):
    """
    Notify all active, on-duty porters of a new room service order.
    Sends via both Pusher (real-time, app open) and FCM (push, app closed).
    """
    from staff.models import Staff
    
    order_data = {
        "order_id": order.id,
        "room_number": order.room_number,
        "total_price": float(order.total_price),
        "created_at": order.created_at.isoformat(),
        "status": order.status
    }
    
    # Send via Pusher (real-time when app is open)
    pusher_count = notify_porters(order.hotel, 'new-room-service-order', order_data)
    
    # Send FCM push notifications (when app is closed)
    fcm_count = 0
    porters = Staff.objects.filter(
        hotel=order.hotel,
        role__slug='porter',
        is_active=True,
        is_on_duty=True
    )
    for porter in porters:
        if send_porter_order_notification(porter, order):
            fcm_count += 1
    
    logger.info(
        f"Room service order {order.id}: "
        f"Notified {pusher_count} porters via Pusher, "
        f"{fcm_count} via FCM push"
    )


def notify_kitchen_staff_of_room_service_order(order):
    """
    Notify all active, on-duty kitchen staff of a new room service order.
    Sends via FCM push notifications (when app is closed).
    """
    from staff.models import Staff
    
    # Send FCM push notifications to kitchen staff
    fcm_count = 0
    kitchen_staff = Staff.objects.filter(
        hotel=order.hotel,
        department__slug='kitchen',
        is_active=True,
        is_on_duty=True
    )
    for staff_member in kitchen_staff:
        if send_kitchen_staff_order_notification(staff_member, order):
            fcm_count += 1
    
    logger.info(
        f"Room service order {order.id}: "
        f"Notified {fcm_count} kitchen staff via FCM push"
    )


def notify_porters_order_count(hotel):
    """
    Send order count update to all active, on-duty porters.
    Sends via both Pusher (real-time) and FCM (push notifications).
    """
    from staff.models import Staff
    from room_services.models import Order
    
    pending = Order.objects.filter(hotel=hotel, status="pending").count()
    
    count_data = {
        "pending_count": pending,
        "type": "room_service_orders"
    }
    
    # Send via Pusher
    pusher_count = notify_porters(hotel, 'order-count-update', count_data)
    
    # Send FCM push notifications
    fcm_count = 0
    porters = Staff.objects.filter(
        hotel=hotel,
        role__slug='porter',
        is_active=True,
        is_on_duty=True
    )
    for porter in porters:
        if send_porter_count_update(porter, pending, "room_service_orders"):
            fcm_count += 1
    
    logger.info(
        f"Order count update for {hotel.name}: "
        f"{pending} pending orders, notified {pusher_count} porters via Pusher, "
        f"{fcm_count} via FCM push"
    )


def notify_porters_of_breakfast_order(order):
    """
    Notify all active, on-duty porters of a new breakfast order.
    Sends via both Pusher (real-time) and FCM (push notifications).
    """
    from staff.models import Staff
    
    order_data = {
        "order_id": order.id,
        "room_number": order.room_number,
        "delivery_time": (
            order.delivery_time.isoformat()
            if order.delivery_time else None
        ),
        "created_at": order.created_at.isoformat(),
        "status": order.status
    }
    
    # Send via Pusher
    pusher_count = notify_porters(order.hotel, 'new-breakfast-order', order_data)
    
    # Send FCM push notifications
    fcm_count = 0
    porters = Staff.objects.filter(
        hotel=order.hotel,
        role__slug='porter',
        is_active=True,
        is_on_duty=True
    )
    for porter in porters:
        if send_porter_breakfast_notification(porter, order):
            fcm_count += 1
    
    logger.info(
        f"Breakfast order {order.id}: "
        f"Notified {pusher_count} porters via Pusher, "
        f"{fcm_count} via FCM push"
    )


def notify_porters_breakfast_count(hotel):
    """
    Send breakfast count update to all active, on-duty porters.
    Sends via both Pusher (real-time) and FCM (push notifications).
    """
    from staff.models import Staff
    from room_services.models import BreakfastOrder
    
    pending = BreakfastOrder.objects.filter(
        hotel=hotel, status="pending"
    ).count()
    
    count_data = {
        "pending_count": pending,
        "type": "breakfast_orders"
    }
    
    # Send via Pusher
    pusher_count = notify_porters(hotel, 'breakfast-count-update', count_data)
    
    # Send FCM push notifications
    fcm_count = 0
    porters = Staff.objects.filter(
        hotel=hotel,
        role__slug='porter',
        is_active=True,
        is_on_duty=True
    )
    for porter in porters:
        if send_porter_count_update(porter, pending, "breakfast_orders"):
            fcm_count += 1
    
    logger.info(
        f"Breakfast count update for {hotel.name}: "
        f"{pending} pending orders, notified {pusher_count} porters via Pusher, "
        f"{fcm_count} via FCM push"
    )
