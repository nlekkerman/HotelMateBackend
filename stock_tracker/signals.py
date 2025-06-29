# stock_tracker/signals.py

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StockMovement
from .stock_alerts import notify_super_admins_about_stock_movement


@receiver(post_save, sender=StockMovement)
def stock_movement_created(sender, instance, created, **kwargs):
    if not created:
        return

    summary = (
        f"{instance.quantity} unit(s) "
        f"{'added' if instance.direction == 'in' else 'removed'} "
        f"for {instance.item.name} by "
        f"{instance.staff.get_full_name() or instance.staff.username}"
    )
    print(f"[Signal] StockMovement created. Preparing to notify: {summary}")
    transaction.on_commit(lambda: notify_super_admins_about_stock_movement(summary, instance.hotel))
