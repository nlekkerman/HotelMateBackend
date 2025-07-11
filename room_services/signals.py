# room_services/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, BreakfastOrder
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_porters_of_breakfast_order,
)

@receiver(post_save, sender=Order)
def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    """
    On creation of a new room service order, send a visible push
    to porters.
    """
    if not created:
        return

    # Visible notification for the new order
    transaction.on_commit(
        lambda: notify_porters_of_room_service_order(instance)
    )

@receiver(post_save, sender=BreakfastOrder)
def send_porter_notification_on_breakfast_order(sender, instance, created, **kwargs):
    """
    On creation of a new breakfast order, send a visible push
    to porters.
    """
    if not created:
        return

    # Visible notification for the new breakfast order
    transaction.on_commit(
        lambda: notify_porters_of_breakfast_order(instance)
    )
