# room_services/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, BreakfastOrder
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_porters_order_count,
    notify_porters_breakfast_count,
    notify_porters_of_breakfast_order

)

def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    """
    On creation of a new room service order, send a visible push
    to porters and then send a silent data-only update of pending count.
    """
    if not created:
        return

    # Visible notification for the new order
    transaction.on_commit(
        lambda: notify_porters_of_room_service_order(instance)
    )

    # Silent count update for all porters
    def send_count():
        notify_porters_order_count(instance.hotel)

    transaction.on_commit(send_count)
    
@receiver(post_save, sender=BreakfastOrder)
def send_porter_notification_on_breakfast_order(sender, instance, created, **kwargs):
    if not created:
        return

    transaction.on_commit(lambda: notify_porters_of_breakfast_order(instance))
    transaction.on_commit(lambda: notify_porters_breakfast_count(instance.hotel))