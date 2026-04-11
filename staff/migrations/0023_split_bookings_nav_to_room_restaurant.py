"""
Data migration: split legacy 'bookings' nav slug into domain-specific
'room_bookings' and 'restaurant_bookings' nav items.

For every hotel:
  1. Create 'room_bookings' and 'restaurant_bookings' NavigationItem if missing.
  2. For every Role whose default_navigation_items includes 'bookings',
     add the two new items (preserving the legacy item for rollback safety).
  3. For every Staff whose allowed_navigation_items includes 'bookings',
     add the two new items.

This migration is safe to run multiple times (idempotent get_or_create).
The legacy 'bookings' item is NOT removed — it is deactivated and kept for
rollback safety.  A future migration will delete it after the transition
period is confirmed complete.
"""
from django.db import migrations


LEGACY_SLUG = 'bookings'
NEW_SLUGS = [
    {
        'slug': 'room_bookings',
        'name': 'Room Bookings',
        'path': '/room-bookings',
        'description': 'Accommodation booking management',
        'display_order': 4,
    },
    {
        'slug': 'restaurant_bookings',
        'name': 'Restaurant Bookings',
        'path': '/restaurant-bookings',
        'description': 'Dining reservation management',
        'display_order': 5,
    },
]


def forwards(apps, schema_editor):
    NavigationItem = apps.get_model('staff', 'NavigationItem')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')
    Hotel = apps.get_model('hotel', 'Hotel')

    for hotel in Hotel.objects.all():
        # 1. Create new nav items for this hotel
        new_items = {}
        for item_def in NEW_SLUGS:
            nav_item, _ = NavigationItem.objects.get_or_create(
                hotel=hotel,
                slug=item_def['slug'],
                defaults={
                    'name': item_def['name'],
                    'path': item_def['path'],
                    'description': item_def['description'],
                    'display_order': item_def['display_order'],
                    'is_active': True,
                },
            )
            new_items[item_def['slug']] = nav_item

        # Find the legacy 'bookings' item for this hotel (may not exist)
        try:
            legacy_item = NavigationItem.objects.get(
                hotel=hotel, slug=LEGACY_SLUG
            )
        except NavigationItem.DoesNotExist:
            continue  # nothing to migrate for this hotel

        # 2. Roles: if role has legacy item, add new items
        for role in Role.objects.filter(
            default_navigation_items=legacy_item
        ):
            for new_item in new_items.values():
                role.default_navigation_items.add(new_item)

        # 3. Staff overrides: if staff has legacy item, add new items
        for staff in Staff.objects.filter(
            allowed_navigation_items=legacy_item
        ):
            for new_item in new_items.values():
                staff.allowed_navigation_items.add(new_item)

        # 4. Deactivate legacy item so it stops appearing in nav lists,
        #    but keep the record for rollback safety.
        legacy_item.is_active = False
        legacy_item.save(update_fields=['is_active'])


def backwards(apps, schema_editor):
    NavigationItem = apps.get_model('staff', 'NavigationItem')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')
    Hotel = apps.get_model('hotel', 'Hotel')

    for hotel in Hotel.objects.all():
        # Re-activate legacy 'bookings' item
        try:
            legacy_item = NavigationItem.objects.get(
                hotel=hotel, slug=LEGACY_SLUG
            )
            legacy_item.is_active = True
            legacy_item.save(update_fields=['is_active'])
        except NavigationItem.DoesNotExist:
            pass

        # Remove new items from roles and staff, then delete
        for slug in ('room_bookings', 'restaurant_bookings'):
            try:
                new_item = NavigationItem.objects.get(
                    hotel=hotel, slug=slug
                )
            except NavigationItem.DoesNotExist:
                continue

            for role in Role.objects.filter(
                default_navigation_items=new_item
            ):
                role.default_navigation_items.remove(new_item)

            for staff in Staff.objects.filter(
                allowed_navigation_items=new_item
            ):
                staff.allowed_navigation_items.remove(new_item)

            new_item.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0022_add_role_default_navigation_items'),
        ('hotel', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
