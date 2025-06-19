from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from notifications.utils import notify_porters_of_room_service_order

@receiver(post_save, sender=Order)
def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    if not created:
        return

    # Defer until all related writes (items, etc.) are committed
    transaction.on_commit(lambda: notify_porters_of_room_service_order(instance))
# This signal handler listens for new Order instances being created