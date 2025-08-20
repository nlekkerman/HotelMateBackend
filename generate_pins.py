import os
import django
import random
from django.db import IntegrityError

# --- Setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")  # <-- change to your project
django.setup()

from staff.models import RegistrationCode  # <-- change to your app

def generate_pins(hotel_slug, count=100):
    created = 0
    attempts = 0
    while created < count:
        pin = f"{random.randint(0, 99999):05d}"  # 5-digit zero-padded
        try:
            RegistrationCode.objects.create(
                code=pin,
                hotel_slug=hotel_slug
            )
            print(f"✅ Created: {pin}")
            created += 1
        except IntegrityError:
            # Duplicate across ANY hotel, so skip
            print(f"⚠️ Duplicate skipped: {pin}")
        attempts += 1
        if attempts > count * 10:  # safety valve
            print("⚠️ Too many duplicates, stopping early.")
            break
    print(f"\n🎉 Done! Created {created} codes for hotel: {hotel_slug}")

if __name__ == "__main__":
    generate_pins("hotel-killarney", 100)
