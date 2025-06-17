# hotel_info/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CategoryQRCode

@receiver(post_save, sender=CategoryQRCode)
def generate_qr_on_create(sender, instance, created, **kwargs):
    if created and not instance.qr_url:
        instance.generate_qr()
        instance.save()
