# room_services/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, BreakfastOrder
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_porters_order_count,
    notify_porters_of_breakfast_order,
    notify_porters_breakfast_count,
)


def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    if not created:
        print(f"[signals] ORDER saved (id={instance.id}), skipping")
        return

    print(f"[signals] NEW ROOM SERVICE ORDER id={instance.id}")

    # first: visible order notification
    def _do_order_notify():
        print(f"[signals] → notify_porters_of_room_service_order({instance.id})")
        try:
            notify_porters_of_room_service_order(instance)
            print(f"[signals]   ✓ order notification sent")
        except Exception as e:
            print(f"[signals]   ✗ order notify failed: {e!r}")

    # second: silent count update
    def _do_count_notify():
        print(f"[signals] → notify_porters_order_count(hotel={instance.hotel.slug})")
        try:
            notify_porters_order_count(instance.hotel)
            print(f"[signals]   ✓ order-count notification sent")
        except Exception as e:
            print(f"[signals]   ✗ order-count notify failed: {e!r}")

    transaction.on_commit(_do_order_notify)
    transaction.on_commit(_do_count_notify)


@receiver(post_save, sender=BreakfastOrder)
def send_porter_notification_on_breakfast_order(sender, instance, created, **kwargs):
    if not created:
        print(f"[signals] BREAKFAST saved (id={instance.id}), skipping")
        return

    print(f"[signals] NEW BREAKFAST ORDER id={instance.id}")

    def _do_breakfast_notify():
        print(f"[signals] → notify_porters_of_breakfast_order({instance.id})")
        try:
            notify_porters_of_breakfast_order(instance)
            print(f"[signals]   ✓ breakfast notification sent")
        except Exception as e:
            print(f"[signals]   ✗ breakfast notify failed: {e!r}")

    def _do_bcount_notify():
        print(f"[signals] → notify_porters_breakfast_count(hotel={instance.hotel.slug})")
        try:
            notify_porters_breakfast_count(instance.hotel)
            print(f"[signals]   ✓ breakfast-count notification sent")
        except Exception as e:
            print(f"[signals]   ✗ breakfast-count notify failed: {e!r}")

    transaction.on_commit(_do_breakfast_notify)
    transaction.on_commit(_do_bcount_notify)
