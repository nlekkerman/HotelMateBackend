from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    Hotel, HotelAccessConfig, HotelPublicPage,
    BookingOptions, AttendanceSettings,
    HotelPrecheckinConfig, HotelSurveyConfig,
)


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


@receiver(post_save, sender=Hotel)
def create_hotel_related_objects(sender, instance, created, **kwargs):
    """
    Auto-create all required OneToOne related objects when a hotel is created.
    Also backfills missing objects for existing hotels on save.
    """
    from common.models import ThemePreference

    # HotelPublicPage
    if not hasattr(instance, 'public_page'):
        HotelPublicPage.objects.create(hotel=instance)

    # BookingOptions
    if not hasattr(instance, 'booking_options'):
        BookingOptions.objects.create(hotel=instance)

    # AttendanceSettings
    if not hasattr(instance, 'attendance_settings'):
        AttendanceSettings.objects.create(hotel=instance)

    # ThemePreference
    if not hasattr(instance, 'theme'):
        ThemePreference.objects.create(hotel=instance)

    # PrecheckinConfig (uses its own defaults)
    HotelPrecheckinConfig.get_or_create_default(instance)

    # SurveyConfig (uses its own defaults)
    HotelSurveyConfig.get_or_create_default(instance)
