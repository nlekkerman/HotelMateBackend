# room_services/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Order, BreakfastOrder
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_porters_of_breakfast_order,
)

# -----------------------------------------------------------------------------
# Helper: Channels broadcast for counts
# -----------------------------------------------------------------------------

def broadcast_counts(hotel_slug):
    """
    Recompute pending counts and send them into the 'orders_<hotel_slug>' group.
    """
    # Import here to avoid circular dependency
    from .models import Order, BreakfastOrder

    pending_rs = Order.objects.filter(
        hotel__slug=hotel_slug, status="pending"
    ).count()
    pending_bf = BreakfastOrder.objects.filter(
        hotel__slug=hotel_slug, status="pending"
    ).count()

    channel_layer = get_channel_layer()
    group_name = f"orders_{hotel_slug}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "count_update",
            "data": {
                "type": "counts",
                "pending_orders": pending_rs,
                "pending_breakfast": pending_bf,
            },
        },
    )

# -----------------------------------------------------------------------------
# Firebase notifications for *new* orders (visible pushes only)
# -----------------------------------------------------------------------------

@receiver(post_save, sender=Order)
def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    if not created:
        return

    # Visible push for the new order
    transaction.on_commit(
        lambda: notify_porters_of_room_service_order(instance)
    )
    # Channels broadcast of updated counts
    transaction.on_commit(
        lambda: broadcast_counts(instance.hotel.slug)
    )

@receiver(post_save, sender=BreakfastOrder)
def send_porter_notification_on_breakfast_order(sender, instance, created, **kwargs):
    if not created:
        return

    # Visible push for the new breakfast order
    transaction.on_commit(
        lambda: notify_porters_of_breakfast_order(instance)
    )
    # Channels broadcast of updated counts
    transaction.on_commit(
        lambda: broadcast_counts(instance.hotel.slug)
    )

# -----------------------------------------------------------------------------
# Channels broadcasts for *all* count changes (save & delete)
# -----------------------------------------------------------------------------

@receiver([post_save, post_delete], sender=Order)
def room_service_count_changed(sender, instance, **kwargs):
    broadcast_counts(instance.hotel.slug)

@receiver([post_save, post_delete], sender=BreakfastOrder)
def breakfast_count_changed(sender, instance, **kwargs):
    broadcast_counts(instance.hotel.slug)
