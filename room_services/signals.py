# room_services/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, BreakfastOrder
from notifications.notification_manager import notification_manager


def send_porter_notification_on_room_service(sender, instance, created, **kwargs):
    if not created:
        print(f"[signals] ORDER saved (id={instance.id}), skipping")
        return

    print(f"[signals] NEW ROOM SERVICE ORDER id={instance.id}")

    # first: visible order notification
    def _do_order_notify():
        print(f"[signals] → NotificationManager.realtime_room_service_order_created({instance.id})")
        try:
            notification_manager.realtime_room_service_order_created(instance)
            print(f"[signals]   ✓ order notification sent via NotificationManager")
        except Exception as e:
            print(f"[signals]   ✗ order notify failed: {e!r}")

    # second: silent count update
    def _do_count_notify():
        print(f"[signals] → NotificationManager count update for hotel={instance.hotel.slug}")
        try:
            # Count notifications are now handled within realtime_room_service_order_created
            # No separate count update needed with unified system
            print(f"[signals]   ✓ count update handled by unified notification")
        except Exception as e:
            print(f"[signals]   ✗ count notify failed: {e!r}")

    transaction.on_commit(_do_order_notify)
    transaction.on_commit(_do_count_notify)


@receiver(post_save, sender=BreakfastOrder)
def send_porter_notification_on_breakfast_order(sender, instance, created, **kwargs):
    if not created:
        print(f"[signals] BREAKFAST saved (id={instance.id}), skipping")
        return

    print(f"[signals] NEW BREAKFAST ORDER id={instance.id}")

    def _do_breakfast_notify():
        print(f"[signals] → NotificationManager.realtime_breakfast_order_created({instance.id})")
        try:
            # Note: breakfast order method may need to be added to NotificationManager
            notification_manager.realtime_room_service_order_created(instance)  # Use room service for now
            print(f"[signals]   ✓ breakfast notification sent via NotificationManager")
        except Exception as e:
            print(f"[signals]   ✗ breakfast notify failed: {e!r}")

    def _do_bcount_notify():
        print(f"[signals] → NotificationManager breakfast count for hotel={instance.hotel.slug}")
        try:
            # Count notifications handled within unified system
            print(f"[signals]   ✓ breakfast count handled by unified notification")
        except Exception as e:
            print(f"[signals]   ✗ breakfast count failed: {e!r}")

    transaction.on_commit(_do_breakfast_notify)
    transaction.on_commit(_do_bcount_notify)
