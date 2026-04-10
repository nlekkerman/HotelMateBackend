from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    Hotel, HotelAccessConfig, HotelPublicPage,
    BookingOptions, AttendanceSettings,
    HotelPrecheckinConfig, HotelSurveyConfig,
)


@receiver(post_save, sender=Hotel)
def create_hotel_related_objects(sender, instance, created, **kwargs):
    """
    Canonical idempotent signal: auto-create all required OneToOne related
    objects when a hotel is created OR backfill missing objects on save.

    This is the ONLY hotel post_save handler. All related-object creation
    is consolidated here to avoid redundant/duplicate signal paths.
    """
    from common.models import ThemePreference

    # HotelAccessConfig
    if not hasattr(instance, 'access_config'):
        HotelAccessConfig.objects.create(hotel=instance)

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

    # Canonical NavigationItems — only on hotel creation
    if created:
        from staff.nav_catalog import CANONICAL_NAV_ITEMS
        from staff.models import NavigationItem

        for item in CANONICAL_NAV_ITEMS:
            NavigationItem.objects.get_or_create(
                hotel=instance,
                slug=item['slug'],
                defaults={
                    'name': item['name'],
                    'path': item['path'],
                    'description': item['description'],
                    'display_order': item['display_order'],
                    'is_active': True,
                },
            )
