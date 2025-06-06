#!/usr/bin/env python
import os
import sys
import django

# ─── 1. DJANGO SETUP ────────────────────────────────────────────────────────────
# Make sure this file lives at the same level as your manage.py, e.g.:
#   /path/to/HotelMateBackend/
#       manage.py
#       generate_hotel_info_qr.py   ← ← ←
#       HotelMateBackend/
#       hotel/
#       hotel_info/
#
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()


# ─── 2. IMPORTS ─────────────────────────────────────────────────────────────────
from django.core.exceptions import ObjectDoesNotExist
from hotel.models import Hotel
from hotel_info.models import HotelInfo
import qrcode
from io import BytesIO
import cloudinary.uploader
from django.db import IntegrityError


# ─── 3. CONSTANTS ────────────────────────────────────────────────────────────────
# If you ever need to override or iterate in a different order, you can define
# them here; otherwise, we'll pull CATEGORY_CHOICES directly from HotelInfo.
CATEGORY_CHOICES = HotelInfo.CATEGORY_CHOICES

# Map each category key → the corresponding HotelInfo.<field> name for the QR URL
FIELD_MAP = {
    'info_board':     'info_qr_board',
    'kid_entertainment': 'info_qr_kids',
    'dining':         'info_qr_dining',
    'offers':         'info_qr_offers',
}


# ─── 4. QR‐GENERATING HELPER ─────────────────────────────────────────────────────
def generate_qr_code(url: str, public_id: str) -> str:
    """
    Build a QR-code PNG for `url`, upload it to Cloudinary under `public_id`,
    and return the resulting secure URL.
    """
    qr = qrcode.make(url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)

    upload_result = cloudinary.uploader.upload(
        img_io,
        resource_type="image",
        public_id=public_id
    )
    return upload_result.get("secure_url")


# ─── 5. MAIN LOGIC: CREATE OR UPDATE HotelInfo FOR EACH CATEGORY ────────────────
def create_qr_info_entries_for_hotel(hotel: Hotel) -> None:
    """
    For each category in HotelInfo.CATEGORY_CHOICES:
      1. Build the target URL (pointing to your Netlify frontend, as before).
      2. Generate & upload the QR code to Cloudinary.
      3. get_or_create() the HotelInfo row; set the QR‐URL field + extra_info["qr_url"].
    """
    print(f"\n🏨 Processing hotel: {hotel.name} (ID={hotel.id}, slug='{hotel.slug}')")
    processed_count = 0

    for category_key, category_label in CATEGORY_CHOICES:
        # 5.1. Build the URL and Cloudinary public ID
        url = (
            f"https://dashing-klepon-d9f0c6.netlify.app"
            f"/hotel_info/{hotel.slug}/category/{category_key}/"
        )
        public_id = f"hotel_info_qr/{hotel.slug}_{category_key}"

        # 5.2. Generate & upload the QR‐code PNG
        try:
            qr_url = generate_qr_code(url, public_id)
        except Exception as e:
            print(f"   ✖ FAILED to upload QR for category '{category_key}': {e}")
            continue

        # 5.3. get_or_create the HotelInfo row
        info_obj, created = HotelInfo.objects.get_or_create(
            hotel=hotel,
            category=category_key,
            defaults={
                "title":       category_label,
                "description": f"Auto-generated description for {category_label}.",
                "active":      True,
            }
        )

        # 5.4. Set the QR-field (e.g. info_qr_board, info_qr_kids, etc.)
        qr_field_name = FIELD_MAP.get(category_key)
        if qr_field_name:
            setattr(info_obj, qr_field_name, qr_url)

        # 5.5. Also stash the same URL into extra_info["qr_url"]
        #       (merge with existing extra_info if present)
        extra = info_obj.extra_info or {}
        extra["qr_url"] = qr_url
        info_obj.extra_info = extra

        # 5.6. Save the HotelInfo instance
        try:
            info_obj.save()
        except Exception as save_err:
            print(f"   ✖ ERROR saving HotelInfo (category '{category_key}'): {save_err}")
            continue

        status = "Created" if created else "Updated"
        print(
            f"   ✅ {status}: '{category_label}' → field '{qr_field_name}' set\n"
            f"      • QR URL: {qr_url}\n"
            f"      • extra_info now: {info_obj.extra_info}"
        )
        processed_count += 1

    print(f"🏁 Done for hotel '{hotel.name}'. {processed_count} categories processed.\n")


# ─── 6. DRIVER: LOOP OVER A SET OF HOTEL IDS ───────────────────────────────────
def process_hotels_by_ids(hotel_ids: list[int]) -> None:
    for hid in hotel_ids:
        try:
            hotel = Hotel.objects.get(id=hid)
        except Hotel.DoesNotExist:
            print(f"❌ Hotel with ID {hid} not found; skipping.")
            continue

        create_qr_info_entries_for_hotel(hotel)


# ─── 7. ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ◦ You can adjust this list to whatever hotel IDs you need.
    # ◦ If you’d rather parse command-line arguments, replace this with argparse logic.
    hotel_ids_to_process = [2, 34]  # ← e.g. “Hotel Killarney” & “Great Southern”
    process_hotels_by_ids(hotel_ids_to_process)
    print("\nAll specified hotels processed. Exiting.")