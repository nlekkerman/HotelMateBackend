"""
Management command to seed database with sample hotels for development/testing.
Usage: python manage.py seed_hotels
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from hotel.models import Hotel, HotelAccessConfig


class Command(BaseCommand):
    help = 'Seed database with sample hotels for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing hotels before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing hotels...'))
            Hotel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared all hotels'))

        hotels_data = [
            {
                'name': 'Grand Hotel Dublin',
                'slug': 'grand-hotel-dublin',
                'subdomain': 'grand-dublin',
                'city': 'Dublin',
                'country': 'Ireland',
                'short_description': 'Luxury 5-star hotel in the heart of Dublin city centre. Perfect for business and leisure travelers.',
                'sort_order': 0,
                'is_active': True,
            },
            {
                'name': 'London Palace Hotel',
                'slug': 'london-palace-hotel',
                'subdomain': 'london-palace',
                'city': 'London',
                'country': 'United Kingdom',
                'short_description': 'Elegant boutique hotel near Hyde Park. Experience British hospitality at its finest.',
                'sort_order': 10,
                'is_active': True,
            },
            {
                'name': 'Paris Elegance Suites',
                'slug': 'paris-elegance-suites',
                'subdomain': 'paris-elegance',
                'city': 'Paris',
                'country': 'France',
                'short_description': 'Charming hotel with views of the Eiffel Tower. Romance and luxury combined.',
                'sort_order': 20,
                'is_active': True,
            },
            {
                'name': 'Berlin Modern Hotel',
                'slug': 'berlin-modern-hotel',
                'subdomain': 'berlin-modern',
                'city': 'Berlin',
                'country': 'Germany',
                'short_description': 'Contemporary design hotel in the vibrant heart of Berlin. Art and culture at your doorstep.',
                'sort_order': 30,
                'is_active': True,
            },
            {
                'name': 'Madrid Royal Inn',
                'slug': 'madrid-royal-inn',
                'subdomain': 'madrid-royal',
                'city': 'Madrid',
                'country': 'Spain',
                'short_description': 'Traditional Spanish hospitality meets modern comfort. Steps from the Royal Palace.',
                'sort_order': 40,
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for data in hotels_data:
                hotel, created = Hotel.objects.update_or_create(
                    slug=data['slug'],
                    defaults=data
                )

                # Ensure HotelAccessConfig exists (signal should create it, but double-check)
                if not hasattr(hotel, 'access_config'):
                    HotelAccessConfig.objects.create(
                        hotel=hotel,
                        guest_portal_enabled=True,
                        staff_portal_enabled=True,
                        requires_room_pin=True,
                        room_pin_length=4,
                        rotate_pin_on_checkout=True,
                        allow_multiple_guest_sessions=True,
                        max_active_guest_devices_per_room=5,
                    )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created: {hotel.name} ({hotel.city}, {hotel.country})')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'→ Updated: {hotel.name} ({hotel.city}, {hotel.country})')
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'✓ Seeding complete!'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count} hotels'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count} hotels'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {Hotel.objects.count()} hotels in database'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Test the API:')
        self.stdout.write('  List all: GET /api/hotel/public/')
        self.stdout.write('  Details:  GET /api/hotel/public/grand-hotel-dublin/')
