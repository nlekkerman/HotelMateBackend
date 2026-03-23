"""
Management command to backfill missing OneToOne related objects for all hotels.
Run once after deploying the signal changes to fix existing hotels.

Usage:
    python manage.py backfill_hotel_related_objects
"""
from django.core.management.base import BaseCommand
from hotel.models import (
    Hotel, HotelAccessConfig, HotelPublicPage,
    BookingOptions, AttendanceSettings,
    HotelPrecheckinConfig, HotelSurveyConfig,
)
from common.models import ThemePreference


class Command(BaseCommand):
    help = "Backfill missing related objects (public_page, booking_options, etc.) for all hotels"

    def handle(self, *args, **options):
        hotels = Hotel.objects.all()
        self.stdout.write(f"Checking {hotels.count()} hotel(s)...")

        models_to_check = [
            ("access_config", HotelAccessConfig),
            ("public_page", HotelPublicPage),
            ("booking_options", BookingOptions),
            ("attendance_settings", AttendanceSettings),
            ("theme", ThemePreference),
        ]

        created_counts = {name: 0 for name, _ in models_to_check}
        created_counts["precheckin_config"] = 0
        created_counts["survey_config"] = 0

        for hotel in hotels:
            for attr_name, model_cls in models_to_check:
                if not hasattr(hotel, attr_name):
                    model_cls.objects.create(hotel=hotel)
                    created_counts[attr_name] += 1
                else:
                    try:
                        getattr(hotel, attr_name)
                    except model_cls.DoesNotExist:
                        model_cls.objects.create(hotel=hotel)
                        created_counts[attr_name] += 1

            # Precheckin & Survey use get_or_create_default
            _, pc_created = HotelPrecheckinConfig.objects.get_or_create(hotel=hotel)
            if pc_created:
                created_counts["precheckin_config"] += 1

            _, sc_created = HotelSurveyConfig.objects.get_or_create(hotel=hotel)
            if sc_created:
                created_counts["survey_config"] += 1

        for name, count in created_counts.items():
            if count:
                self.stdout.write(self.style.SUCCESS(f"  Created {count} {name}(s)"))
            else:
                self.stdout.write(f"  {name}: all present")

        self.stdout.write(self.style.SUCCESS("Done."))
