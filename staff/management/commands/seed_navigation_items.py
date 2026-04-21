from django.core.management.base import BaseCommand
from hotel.models import Hotel
from staff.models import NavigationItem
from staff.nav_catalog import CANONICAL_NAV_ITEMS, CANONICAL_NAV_SLUGS

# Legacy slugs that are no longer part of the canonical nav.
# These are deactivated (not deleted) so that DB rows already referenced
# by role/staff overrides don't cause constraint errors.
LEGACY_SLUGS_TO_DEACTIVATE = {
    'entertainment', 'stock_tracker', 'reception',
    'room-bookings', 'room_service', 'breakfast',
    'menus', 'bookings', 'guests', 'settings',
}


class Command(BaseCommand):
    help = 'Seeds canonical navigation items for a hotel (or all hotels)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel-slug',
            type=str,
            default=None,
            help='Hotel slug to seed navigation items for (omit for all hotels)',
        )

    def handle(self, *args, **options):
        hotel_slug = options['hotel_slug']

        if hotel_slug:
            try:
                hotels = [Hotel.objects.get(slug=hotel_slug)]
            except Hotel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hotel with slug "{hotel_slug}" does not exist')
                )
                return
        else:
            hotels = list(Hotel.objects.all())
            if not hotels:
                self.stdout.write(self.style.ERROR('No hotels found'))
                return

        for hotel in hotels:
            created_count = 0
            updated_count = 0
            deactivated_count = 0

            for item_data in CANONICAL_NAV_ITEMS:
                nav_item, created = NavigationItem.objects.update_or_create(
                    hotel=hotel,
                    slug=item_data['slug'],
                    defaults={
                        'name': item_data['name'],
                        'path': item_data['path'],
                        'description': item_data['description'],
                        'display_order': item_data['display_order'],
                        'is_active': True,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created: {nav_item.slug}')
                    )
                else:
                    updated_count += 1

            # Deactivate any legacy/removed slugs that still exist in the DB
            deactivated = NavigationItem.objects.filter(
                hotel=hotel,
                slug__in=LEGACY_SLUGS_TO_DEACTIVATE,
                is_active=True,
            ).update(is_active=False)
            deactivated_count += deactivated

            self.stdout.write(
                self.style.SUCCESS(
                    f'{hotel.slug}: {created_count} created, {updated_count} updated, '
                    f'{deactivated_count} legacy slugs deactivated'
                )
            )
