#!/usr/bin/env python
import os
import django
from datetime import timedelta, time

# ─── 1. Setup Django ───────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

# ─── 2. Imports ────────────────────────────────────────────────────────────────
from django.utils import timezone
from hotel.models import Hotel
from hotel_info.models import HotelInfo, HotelInfoCategory

# ─── 3. Configuration ─────────────────────────────────────────────────────────
HOTEL_SLUG    = "hotel-killarney"
CATEGORY_SLUG = "kid-entertainment"
EVENT_TIMES   = [time(10, 0), time(14, 0), time(18, 0)]
DAYS_AHEAD    = 15

def main():
    now = timezone.localdate()

    # Grab the hotel and category
    try:
        hotel    = Hotel.objects.get(slug=HOTEL_SLUG)
        category = HotelInfoCategory.objects.get(slug=CATEGORY_SLUG)
    except Hotel.DoesNotExist:
        print(f"ERROR: Hotel with slug '{HOTEL_SLUG}' not found.")
        return
    except HotelInfoCategory.DoesNotExist:
        print(f"ERROR: Category with slug '{CATEGORY_SLUG}' not found.")
        return

    # Create events
    created = 0
    for day_offset in range(DAYS_AHEAD):
        event_date = now + timedelta(days=day_offset)
        for idx, evt_time in enumerate(EVENT_TIMES, start=1):
            title = f"Kids Activity #{idx} on {event_date.isoformat()}"
            description = f"Fun activity #{idx} for our young guests."
            info, was_created = HotelInfo.objects.get_or_create(
                hotel=hotel,
                category=category,
                event_date=event_date,
                event_time=evt_time,
                defaults={
                    "title": title,
                    "description": description,
                    "active": True,
                }
            )
            if was_created:
                created += 1

    print(f"Created {created} new HotelInfo events for '{HOTEL_SLUG}' in '{CATEGORY_SLUG}' over next {DAYS_AHEAD} days.")

if __name__ == "__main__":
    main()
