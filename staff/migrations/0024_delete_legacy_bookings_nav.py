"""
Final cleanup: delete the legacy 'bookings' NavigationItem and remove any
lingering M2M references from roles/staff.

Safe & idempotent — if no 'bookings' items exist, this is a no-op.
"""
from django.db import migrations


def delete_legacy_bookings(apps, schema_editor):
    NavigationItem = apps.get_model('staff', 'NavigationItem')
    Role = apps.get_model('staff', 'Role')
    Staff = apps.get_model('staff', 'Staff')

    legacy_items = NavigationItem.objects.filter(slug='bookings')

    # Remove M2M references first (idempotent — does nothing if already clean)
    for item in legacy_items:
        for role in Role.objects.filter(default_navigation_items=item):
            role.default_navigation_items.remove(item)
        for staff in Staff.objects.filter(allowed_navigation_items=item):
            staff.allowed_navigation_items.remove(item)

    # Hard-delete the NavigationItem rows
    count, _ = legacy_items.delete()
    if count:
        print(f"  Deleted {count} legacy 'bookings' NavigationItem(s)")


def reverse_noop(apps, schema_editor):
    # Cannot reverse a deletion — but migration framework requires this.
    # Re-running seed_navigation_items would recreate if nav_catalog still
    # contained 'bookings', but it no longer does.  This is intentional.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0023_split_bookings_nav_to_room_restaurant'),
    ]

    operations = [
        migrations.RunPython(delete_legacy_bookings, reverse_noop),
    ]
