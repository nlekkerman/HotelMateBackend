from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order  # Adjust import as needed
from notifications.utils import notify_porters_of_room_service_order

@receiver(post_save, sender=Order)
def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    if created:  # Only on create
        notify_porters_of_room_service_order(instance)
