from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Hotel, HotelAccessConfig


@receiver(post_save, sender=Hotel)
def create_hotel_access_config(sender, instance, created, **kwargs):
    """
    Automatically create HotelAccessConfig when a new Hotel is created.
    """
    if created:
        HotelAccessConfig.objects.create(hotel=instance)


@receiver(post_save, sender=Hotel)
def save_hotel_access_config(sender, instance, **kwargs):
    """
    Ensure access_config exists when hotel is saved.
    Creates it if missing (for existing hotels).
    """
    if not hasattr(instance, 'access_config'):
        HotelAccessConfig.objects.create(hotel=instance)
