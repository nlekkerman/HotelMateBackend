import os
import django
import random
import string

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "porterproject.settings")
django.setup()

from room.models import Room


def generate_unique_pin(existing_pins, length=4):
    chars = string.ascii_lowercase + string.digits
    while True:
        pin = ''.join(random.choices(chars, k=length))
        if pin not in existing_pins:
            return pin


def update_guest_id_pins():
    updated = 0
    skipped = 0

    existing_pins = set(
        Room.objects.exclude(guest_id_pin__isnull=True)
        .exclude(guest_id_pin__exact="")
        .values_list('guest_id_pin', flat=True)
    )

    rooms = Room.objects.filter(guest_id_pin__isnull=True) | Room.objects.filter(guest_id_pin__exact="")

    for room in rooms:
        pin = generate_unique_pin(existing_pins)
        room.guest_id_pin = pin
        room.save()
        existing_pins.add(pin)
        updated += 1
        print(f"Updated Room {room.room_number} with PIN: {pin}")

    print(f"\nDone. {updated} rooms updated. {skipped} skipped.")


if __name__ == "__main__":
    update_guest_id_pins()
