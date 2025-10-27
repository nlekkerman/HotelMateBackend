from staff.models import Staff

import logging
logger = logging.getLogger(__name__)


def notify_porters_of_room_service_order(order):
    """
    Notify all active, on-duty porters of a new room service order.
    Note: Firebase/FCM functionality has been removed.
    This function now serves as a placeholder for future notification systems.
    """
    porters = (
        Staff.objects
        .filter(
            hotel=order.hotel,
            role__slug="porter",
            is_active=True,
            is_on_duty=True,
        )
        .distinct()
    )

    for porter in porters:
        logger.info(
            f"Room service order notification for {porter.first_name} {porter.last_name}: "
            f"Room {order.room_number}: Total €{order.total_price:.2f}"
        )


def notify_porters_order_count(hotel):
    """
    Send order count update to all active, on-duty porters.
    Note: Firebase/FCM functionality has been removed.
    This function now serves as a placeholder for future notification systems.
    """
    pending = hotel.order_set.filter(status="pending").count()

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
        )
        .distinct()
    )
    
    logger.info(f"Order count update for {hotel.name}: {pending} pending orders")


def notify_porters_of_breakfast_order(order):
    """
    Notify all active, on-duty porters of a new breakfast order.
    Note: Firebase/FCM functionality has been removed.
    This function now serves as a placeholder for future notification systems.
    """
    porters = (
        Staff.objects
        .filter(
            hotel=order.hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
        )
        .distinct()
    )
    
    for porter in porters:
        logger.info(
            f"Breakfast order notification for {porter.first_name} {porter.last_name}: "
            f"Room {order.room_number}"
        )


def notify_porters_breakfast_count(hotel):
    """
    Send breakfast count update to all active, on-duty porters.
    Note: Firebase/FCM functionality has been removed.
    This function now serves as a placeholder for future notification systems.
    """
    from room_services.models import BreakfastOrder
    pending = BreakfastOrder.objects.filter(hotel=hotel, status="pending").count()

    porters = (
        Staff.objects
        .filter(
            hotel=hotel,
            role="porter",
            is_active=True,
            is_on_duty=True,
        )
        .distinct()
    )
    
    logger.info(f"Breakfast count update for {hotel.name}: {pending} pending orders")
