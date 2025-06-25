#!/usr/bin/env python
import os
# ─── 1. Setup Django ───────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
import django
django.setup()

# ─── 2. Imports ────────────────────────────────────────────────────────────────
from datetime import timedelta, time
from django.utils import timezone
from io import BytesIO
import cloudinary
import cloudinary.uploader

from hotel.models import Hotel
from hotel_info.models import HotelInfo, HotelInfoCategory

# ─── 3. Configure Cloudinary ──────────────────────────────────────────────────
# Ensure CLOUDINARY_URL is set in your environment
cloudinary.config()  # reads from CLOUDINARY_URL

# ─── 4. Configuration ─────────────────────────────────────────────────────────
HOTEL_SLUG    = "hotel-killarney"
CATEGORY_SLUG = "hotel-leisure"
EVENT_TIMES   = [time(10, 0), time(14, 0), time(18, 0)]
DAYS_AHEAD    = 15
IMAGE_PATH    = r"C:\Users\nlekk\Downloads\nasturtium.png"  # Local image file


def main():
    """Create or update HotelInfo events and upload a static image via Cloudinary."""
    today = timezone.localdate()

    # Verify image file exists
    if not os.path.isfile(IMAGE_PATH):
        print(f"ERROR: Image file '{IMAGE_PATH}' does not exist.")
        return
    # Read image once
    with open(IMAGE_PATH, 'rb') as f:
        img_bytes = f.read()

    # Retrieve hotel and category
    try:
        hotel = Hotel.objects.get(slug=HOTEL_SLUG)
    except Hotel.DoesNotExist:
        print(f"ERROR: Hotel with slug '{HOTEL_SLUG}' not found.")
        return
    try:
        category = HotelInfoCategory.objects.get(slug=CATEGORY_SLUG)
    except HotelInfoCategory.DoesNotExist:
        print(f"ERROR: Category with slug '{CATEGORY_SLUG}' not found.")
        return

    created = 0
    processed = 0

    # Loop through each day and time
    for day_offset in range(DAYS_AHEAD):
        event_date = today + timedelta(days=day_offset)
        for idx, evt_time in enumerate(EVENT_TIMES, start=1):
            # Idempotent event creation
            info, was_created = HotelInfo.objects.get_or_create(
                hotel=hotel,
                category=category,
                event_date=event_date,
                event_time=evt_time,
                defaults={
                    'title': f"Aqua #{idx} on {event_date}",
                    'description': f"Water fantasy #{idx} for our guests.",
                    'active': True,
                }
            )
            if was_created:
                created += 1

            # Upload image to Cloudinary and save public_id
            try:
                public_id = f"hotel_info_{hotel.slug}_{category.slug}_{event_date}_{evt_time.strftime('%H%M')}"
                resp = cloudinary.uploader.upload(
                    BytesIO(img_bytes),
                    resource_type='image',
                    public_id=public_id,
                    overwrite=True
                )
                # Store the public_id string; CloudinaryField will handle URL generation
                info.image = resp.get('public_id')
                info.save()
                print(f"[OK] Uploaded {public_id} for {info}")
            except Exception as e:
                print(f"ERROR uploading image for {info}: {e}")

            processed += 1

    print(f"Done: {created} new events created; images processed for {processed} entries.")


if __name__ == '__main__':
    main()
