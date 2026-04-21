"""
reset_navigation_items.py

One-shot script: wipe ALL NavigationItem rows for every hotel and
re-create exactly the canonical set.

Run with:
    python manage.py runscript reset_navigation_items
OR:
    python scripts/reset_navigation_items.py  (after django.setup())

Safe to run multiple times — each run does a full replace.
"""

import os
import sys
import django

# Allow running directly (not via manage.py runscript)
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
    django.setup()

from hotel.models import Hotel
from staff.models import NavigationItem
from staff.nav_catalog import CANONICAL_NAV_ITEMS


def run():
    hotels = list(Hotel.objects.all())
    if not hotels:
        print("No hotels found — nothing to do.")
        return

    print(f"Found {len(hotels)} hotel(s): {[h.slug for h in hotels]}\n")

    for hotel in hotels:
        # 1. Delete ALL existing NavigationItem rows for this hotel
        deleted_count, _ = NavigationItem.objects.filter(hotel=hotel).delete()
        print(f"[{hotel.slug}] Deleted {deleted_count} existing nav item(s).")

        # 2. Re-create exactly the canonical set
        created = []
        for item in CANONICAL_NAV_ITEMS:
            NavigationItem.objects.create(
                hotel=hotel,
                slug=item['slug'],
                name=item['name'],
                path=item['path'],
                description=item['description'],
                display_order=item['display_order'],
                is_active=True,
            )
            created.append(item['slug'])

        print(f"[{hotel.slug}] Created {len(created)} canonical nav item(s): {created}\n")

    print("Done. All hotels now have identical canonical NavigationItem sets.")


if __name__ == '__main__':
    run()
