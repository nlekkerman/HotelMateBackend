from django.core.management.base import BaseCommand
from hotel.models import Hotel
from staff.models import NavigationItem


class Command(BaseCommand):
    help = 'Seeds navigation items for a specific hotel'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hotel-slug',
            type=str,
            default='hotel-killarney',
            help='Hotel slug to seed navigation items for'
        )

    def handle(self, *args, **options):
        hotel_slug = options['hotel_slug']
        
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Hotel with slug "{hotel_slug}" does not exist'
                )
            )
            return

        # Navigation items based on NAVIGATION_ICONS_LIST.md
        navigation_items = [
            {
                'slug': 'home',
                'name': 'Home',
                'path': '/',
                'description': 'Dashboard and overview',
                'display_order': 1
            },
            {
                'slug': 'chat',
                'name': 'Chat',
                'path': '/chat',
                'description': 'Staff communication',
                'display_order': 2
            },
            {
                'slug': 'reception',
                'name': 'Reception',
                'path': '/reception',
                'description': 'Reception management',
                'display_order': 3
            },
            {
                'slug': 'rooms',
                'name': 'Rooms',
                'path': '/rooms',
                'description': 'Room management',
                'display_order': 4
            },
            {
                'slug': 'guests',
                'name': 'Guests',
                'path': '/guests',
                'description': 'Guest management',
                'display_order': 5
            },
            {
                'slug': 'roster',
                'name': 'Roster',
                'path': '/roster',
                'description': 'Staff scheduling and attendance',
                'display_order': 6
            },
            {
                'slug': 'staff',
                'name': 'Staff',
                'path': '/staff',
                'description': 'Staff management',
                'display_order': 7
            },
            {
                'slug': 'restaurants',
                'name': 'Restaurants',
                'path': '/restaurants',
                'description': 'Restaurant management',
                'display_order': 8
            },
            {
                'slug': 'bookings',
                'name': 'Bookings',
                'path': '/bookings',
                'description': 'Booking management',
                'display_order': 9
            },
            {
                'slug': 'maintenance',
                'name': 'Maintenance',
                'path': '/maintenance',
                'description': 'Maintenance requests',
                'display_order': 10
            },
            {
                'slug': 'hotel_info',
                'name': 'Hotel Info',
                'path': '/hotel-info',
                'description': 'Hotel information',
                'display_order': 11
            },
            {
                'slug': 'good_to_know',
                'name': 'Good to Know',
                'path': '/good-to-know',
                'description': 'Important information',
                'display_order': 12
            },
            {
                'slug': 'stock_tracker',
                'name': 'Stock Tracker',
                'path': '/stock-tracker',
                'description': 'Inventory management',
                'display_order': 13
            },
            {
                'slug': 'games',
                'name': 'Games',
                'path': '/games',
                'description': 'Entertainment and games',
                'display_order': 14
            },
            {
                'slug': 'settings',
                'name': 'Settings',
                'path': '/settings',
                'description': 'User settings',
                'display_order': 15
            },
            {
                'slug': 'room_service',
                'name': 'Room Service',
                'path': '/room-service',
                'description': 'Room service orders',
                'display_order': 16
            },
            {
                'slug': 'breakfast',
                'name': 'Breakfast',
                'path': '/breakfast',
                'description': 'Breakfast service',
                'display_order': 17
            },
        ]

        created_count = 0
        updated_count = 0
        
        for item_data in navigation_items:
            nav_item, created = NavigationItem.objects.update_or_create(
                hotel=hotel,
                slug=item_data['slug'],
                defaults={
                    'name': item_data['name'],
                    'path': item_data['path'],
                    'description': item_data['description'],
                    'display_order': item_data['display_order'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created: {nav_item.slug} for {hotel.slug}'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated: {nav_item.slug} for {hotel.slug}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created: {created_count}, '
                f'Updated: {updated_count} navigation items for {hotel.slug}'
            )
        )
